# Copyright (c) 2023 by Microsoft Corporation.
# Licensed under the MIT license.


import uuid
import time

from typing import List, Optional, Dict

from parrot.utils import RecyclePool, time_counter_in_nanoseconds, get_logger
from parrot.exceptions import parrot_assert, ParrotCoreUserError

from parrot.serve.graph import (
    SemanticVariable,
    RequestChain,
    ConstantFill,
    PlaceholderFill,
    PlaceholderGen,
)

logger = get_logger("SemanticVariableManager")


class SemanticVariableNamespace:
    """A namespace of Semantic Variables, giving a unique id to each SV.

    The guideline is to hash the most important information of the SV to a single ID.
    There are majorly two types of SVs:
    - Constants: The content is the most important information. We use content-based hashing.
    - Placeholders: The placeholder itself is the most important information. We allocate a seed for
        each placeholder.
    """

    def __init__(self) -> None:
        # Variables: sv_id -> variable
        self.vars: Dict[str, SemanticVariable] = {}

        # Name Generating
        # Seed is for generating unique names.
        self.seed_pool = RecyclePool("SemanticVariable")
        self.namespace_uuid = uuid.uuid4()  # A UUID object.

    def _get_hashed_sv_id(self, content: str) -> str:
        return str(
            uuid.uuid3(
                namespace=self.namespace_uuid,
                name=str(content),
            )
        )

    def get_var_by_content(self, content: str) -> Optional[SemanticVariable]:
        """Get a Semantic Variable by content."""

        sv_id = self._get_hashed_sv_id(content)

        return self.vars.get(sv_id)

    def new_var_by_content(
        self, content: str, is_constant_prefix: bool
    ) -> SemanticVariable:
        """Create a new Semantic Variable by content.
        If the SV already exists, return the existing one. Otherwise, create a new one.
        """

        seed = -1
        hash_name = content

        sv_id = self._get_hashed_sv_id(hash_name)

        if sv_id in self.vars:
            return self.vars[sv_id]

        sv = SemanticVariable(
            name="constant",
            sv_id=sv_id,
            is_constant_prefix=is_constant_prefix,
            seed=seed,
        )
        # NOTE(chaofan): Directly set the content in this case.
        sv.set(content)

        self.vars[sv_id] = sv

        return sv

    def new_var_by_name(self, name: str, is_constant_prefix: bool) -> SemanticVariable:
        """Create a new Semantic Variable."""

        seed = self.seed_pool.allocate()
        hash_name = str(seed)

        sv_id = self._get_hashed_sv_id(hash_name)

        # Must be different.
        parrot_assert(sv_id not in self.vars, "SV ID already exists.")

        sv = SemanticVariable(
            name=name, sv_id=sv_id, is_constant_prefix=is_constant_prefix, seed=seed
        )
        self.vars[sv_id] = sv

        return sv

    def free_var(self, sv: SemanticVariable) -> None:
        """Free a Semantic Variable."""

        parrot_assert(sv.sv_id in self.vars, "SV ID does not exist.")

        self.seed_pool.free(sv.seed)
        self.vars.pop(sv.sv_id)


class SemanticVariableManager:
    """Manage all Semantic Variables used in the system.

    In implementation, we have two types of Semantic Variables:
    - Constant Prefix Variables: These are used for the continuous constants at the beginning of the request.
    - Local Variables: Other variables in the request.

    This is because constant prefixes are usually shared among different requests. We lift them to a global-level
    namespace to prevent from freeing them when the session ends.

    Two-level variables also give hints to ContextMananger. To be specific, a constant prefix adds an extra
    ref_counter to corresponding contexts to prevent them from being freed. The ref_counter is decreased when
    the constant prefix variable is freed.

    Currently, we use a heuristic expiration policy for constant prefix variables.
    """

    def __init__(self, constant_prefix_var_timeout: int) -> None:
        # ---------- Namespace ----------
        self.constant_prefix_namespace = SemanticVariableNamespace()

        # session_id -> namespace
        self.session_namespaces: Dict[int, SemanticVariableNamespace] = {}

        # ---------- Constant Prefixes Management ----------

        # sv_id -> last_access_time
        self.constant_prefix_last_access_time: Dict[str, float] = {}
        self.constant_prefix_var_timeout = constant_prefix_var_timeout

    # ---------- Internal methods ----------

    def _get_constant_prefix_var(self, content: str) -> SemanticVariable:
        """Get/create a prefix-constant variable (hashed by content)."""

        pc_var = self.constant_prefix_namespace.new_var_by_content(
            content, is_constant_prefix=True
        )
        # Update the last access time.
        self.constant_prefix_last_access_time[pc_var.sv_id] = (
            time_counter_in_nanoseconds()
        )
        return pc_var

    def _get_local_var_by_content(
        self, session_id: int, content: str
    ) -> SemanticVariable:
        """Get/create a variable in a session scope (hashed by content)."""

        namespace = self.session_namespaces[session_id]
        lvar = namespace.new_var_by_content(content, is_constant_prefix=False)
        return lvar

    def _create_local_var_by_name(self, session_id: int, name: str) -> SemanticVariable:
        namespace = self.session_namespaces[session_id]
        lvar = namespace.new_var_by_name(name, is_constant_prefix=False)
        return lvar

    def _get_local_var_by_id(self, session_id: int, sv_id: str) -> SemanticVariable:
        namespace = self.session_namespaces[session_id]
        lvar = namespace.vars.get(sv_id)
        parrot_assert(lvar is not None, "Local variable does not exist.")
        return lvar

    # ---------- Public methods ----------

    def register_local_var_space(self, session_id: int) -> None:
        """Register a local namespace."""

        parrot_assert(
            session_id not in self.session_namespaces,
            "Session ID already exists.",
        )

        self.session_namespaces[session_id] = SemanticVariableNamespace()

    def free_local_var_space(self, session_id: int) -> None:
        """Free a local namespace."""

        parrot_assert(
            session_id in self.session_namespaces,
            "Session ID does not exist.",
        )

        self.session_namespaces.pop(session_id)

    def free_expired_constant_prefix_vars(self) -> List[SemanticVariable]:
        """Free expired constant prefix variables.

        Returns:
            List[SemanticVariable]: The list of freed variables.
        """

        cur_time = time_counter_in_nanoseconds()
        ret: List[SemanticVariable] = []

        for sv_id, last_access_time in list(
            self.constant_prefix_last_access_time.items()
        ):
            if (
                cur_time - last_access_time
                > self.constant_prefix_var_timeout * 1_000_000_000
            ):
                var = self.constant_prefix_namespace.vars[sv_id]
                self.constant_prefix_namespace.free_var(var)
                self.constant_prefix_last_access_time.pop(sv_id)
                ret.append(var)
                logger.debug(f"Constant Prefix Variable (id={sv_id}) expired.")

        return ret

    def create_var(self, session_id: int, name: str) -> SemanticVariable:
        """Create a Semantic Variable in the local namespace.]

        Args:
            session_id: int. The session ID.
            name: str. The name of the Semantic Variable.
        """

        parrot_assert(
            session_id in self.session_namespaces,
            f"Local namespace of {session_id} does not exist.",
        )

        return self.session_namespaces[session_id].new_var_by_name(
            name, is_constant_prefix=False
        )

    def get_var(self, session_id: int, sv_id: str) -> SemanticVariable:
        """Get a Semantic Variable by ID.

        Args:
            session_id: int. The session ID.
            sv_id: str. The Semantic Variable ID.
        """

        if sv_id in self.constant_prefix_namespace.vars:
            return self.constant_prefix_namespace.vars[sv_id]

        parrot_assert(
            session_id in self.session_namespaces,
            f"Local namespace of {session_id} does not exist.",
        )

        if sv_id in self.session_namespaces[session_id].vars:
            return self.session_namespaces[session_id].vars[sv_id]

        raise ParrotCoreUserError(ValueError(f"Unknown Semantic Variable ID: {sv_id}"))

    def create_vars_for_request(
        self, session_id: int, request_chain: RequestChain
    ) -> None:
        """Create all the Semantic Variables in the request chain.

        Args:
            session_id: int. The session ID.
            request_chain: RequestChain. The request chain.
        """

        constant_prefix_flag: bool = True
        debug_info: str = ""

        # Create SVs for each node.
        for node in request_chain.iter():
            # "Constant prefix" refers to continuous constants at the beginning of the request.
            # When a placeholder appears, the constant prefix ends.
            if node.has_placeholder:
                constant_prefix_flag = False

            # For ConstantFill, if it is in the constant prefix, we use global variables.
            # We get sv ID by content (the same content -> the same sv ID).
            if isinstance(node, ConstantFill):
                if constant_prefix_flag:
                    node.sv = self._get_constant_prefix_var(content=node.constant_text)
                else:
                    node.sv = self._get_local_var_by_content(
                        session_id=session_id,
                        content=node.constant_text,
                    )
            # For PlaceholderFill, we create/get a local variable by placeholder name.
            # (By name: always create a new variable)
            elif isinstance(node, PlaceholderFill):
                if node.placeholder.should_create:
                    lvar = self._create_local_var_by_name(
                        session_id=session_id,
                        name=node.placeholder.name,
                    )
                else:
                    lvar = self._get_local_var_by_id(
                        session_id=session_id,
                        sv_id=node.placeholder.var_id,
                    )
                node.sv = lvar
            # For PlaceholderGen, always create a new local variable.
            elif isinstance(node, PlaceholderGen):
                node.sv = self._create_local_var_by_name(
                    session_id=session_id,
                    name=node.placeholder.name,
                )
            else:
                parrot_assert(
                    False,
                    "Unknown node type.",
                )

            debug_info += f"\t{node.__class__.__name__} -> {node.sv.sv_id}, is_constant_prefix: {node.sv.is_constant_prefix}\n"

        request_chain.sv_created = True

        logger.debug("SVs created for request chain:\n" + debug_info)
