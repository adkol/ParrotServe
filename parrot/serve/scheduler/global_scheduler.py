# Copyright (c) 2023 by Microsoft Corporation.
# Licensed under the MIT license.


from typing import Optional, List, Set
from dataclasses import dataclass

from parrot.exceptions import ParrotCoreUserError
from parrot.utils import get_logger, RecyclePool

from parrot.serve.graph import RequestChain
from parrot.serve.backend_repr import ExecutionEngine
from parrot.serve.backend_repr.model import get_model_type, ModelType

from ..engine_manager import EngineManager
from ..context_manager import ServeCoreContextManager
from .completion_task import CompletionTask, TaskStatus
from ..variable_manager import SemanticVariableManager
from ..context_manager import PrefixCache
logger = get_logger("GlobalScheduler")

MAX_DELAY_THRESHOLD = 800
DELAY_SCHEDULING_ON = True
MAX_GROUP_LEN = 4
MAX_TASKS_ENGINE = 6 
MAX_TOKENS_PER_ENGINE = 7500
NOTFREEALL = True

@dataclass
class GlobalSchedulerConfig:
    app_fifo: bool = False
    graph_group: bool = False
    ctx_group: bool = False
    ctx_aware: bool = False
    max_queue_size: int = 1024

class GlobalScheduler:
    """GlobalScheduler (GS) solves the task scheduling problem in the global scope."""

    def __init__(
        self,
        config: GlobalSchedulerConfig,
        engine_mgr: EngineManager,
        context_mgr: ServeCoreContextManager,
        var_mgr: SemanticVariableManager
    ):
        # ---------- Basic ----------
        self.config = config
        self.engine_mgr = engine_mgr
        self.context_mgr = context_mgr
        self.context_mgr.tokenizers_wrapper = engine_mgr.tokenizers_wrapper
        PrefixCache.tokenizer_name = "hf-internal-testing/llama-tokenizer"
        self.var_mgr = var_mgr
        # ---------- Task Queue ----------
        self.task_queue: List[CompletionTask] = []
        self.bad_scheduled = 0
        self.impossible_scheduled = 0
        self.total_scheduled = 0
        self.most_delay = 0

    def _get_engine_list(
        self,
        tasks: List[CompletionTask],
        tasks_num_upperbound: int,
        engines_with_prefix: list
    ) -> List[ExecutionEngine]:
        engine_list = self.engine_mgr.get_live_engines()    

        # NOTE(chaofan): Suppose all tasks noted the same "models" arg.
        models = tasks[0].chain.metadata.models
        model_type_str = tasks[0].chain.metadata.model_type
        model_type = get_model_type(model_type_str)
        # TODO(chaofan): Throughput/latency criteria

        def check_engine_available(engine: ExecutionEngine):
            # Check whether the mode type matches
            if model_type != engine.model.model_type:
                return False

            # Check whether the model matches
            if len(models) > 0 and engine.model_name not in models:
                return False

            # Check whether it violates the tasks_num_upperbound of the tasks.
            # NOTE(chaofan): For TaskGroup (i.e. tasks passed to this function),
            # the whole group is considered as a single task.
            if 1 + engine.get_num_tasks() > MAX_TASKS_ENGINE:
                return False

            # Check whether it violates the tasks_num_upperbound of the engine.
            if len(tasks) + engine.get_num_tasks() > MAX_TASKS_ENGINE:
                return False

            # Check whether the engine has enough task capacity.
            if len(tasks) > engine.get_remain_tasks_capacity():
                return False
            total_tokens_num = 0
            if model_type == ModelType.TOKEN_ID:
                for task in tasks:        
                    total_tokens_num += task.get_token_nums(engine.model.tokenizer_name)                    
            # print("CACHED LENGTH", self.context_mgr.prefix_caches[engine.engine_id].lru.cached_length)
            increment_from_tasks = total_tokens_num
            for context in tasks[0].contexts:
                if context.is_constant and context.prefix_hash in self.context_mgr.prefix_caches[engine.engine_id].lru.dic:
                    increment_from_tasks -= len(tasks)*self.context_mgr.prefix_caches[engine.engine_id].lru.dic[context.prefix_hash][0]
                else:
                    increment_from_tasks -= (len(tasks) - 1) *self.context_mgr.prefix_caches[engine.engine_id].lru.dic[context.prefix_hash][0]
            # print("increment from tasks", increment_from_tasks)
            if self.context_mgr.prefix_caches[engine.engine_id].lru.cached_length + increment_from_tasks > MAX_TOKENS_PER_ENGINE: # can try lowering this
                need_to_free = self.context_mgr.prefix_caches[engine.engine_id].lru.cached_length + increment_from_tasks - MAX_TOKENS_PER_ENGINE
                need_to_free *= 1.5
                items = list(self.context_mgr.prefix_caches[engine.engine_id].lru.dic.keys())[::-1]
                for key in items: # loop through all current prefixes in the engine
                    value = self.context_mgr.prefix_caches[engine.engine_id].lru.dic[key]
                    if value[1].is_constant and self.context_mgr._context_ref_counter[value[1].context_id] == 1: # check which ones we can evict
                        # print("GLOBAL SCHEULER FREEING ", value[1].context_id)
                        self.context_mgr._free_context(value[1]) #evict
                    need_to_free -= value[0]
                    if NOTFREEALL:
                        if need_to_free <= 0:
                            break                
                if need_to_free > 0:
                    return False
            return True
         
        sorted_engine_list = sorted(engine_list, key=lambda x: int(x in engines_with_prefix), reverse=True)
        for engine in sorted_engine_list:
            if check_engine_available(engine):
                return [engine]
        return []
        # toret = [engine for engine in engine_list if check_engine_available(engine)]
        # toret.sort(key=lambda x: x.get_num_tasks())
        # print("Engines Availabe", [x.engine_id for x in toret])
        
        return toret

    def _find_engine(self, tasks: List[CompletionTask]) -> None:
        """Find the best engine for a group of tasks."""

        tasks_num_upperbound = 999999999
        for task in tasks:
            tasks_num_upperbound = min(
                tasks_num_upperbound, task.schedule_annotation.tasks_num_upperbound
            )

        # Get the engine list
        engine_ids_with_prefixes = []
        if self.config.ctx_aware:
            engine_ids_with_prefixes = self.context_mgr.query_prefixes_in_engines(
                tasks[0]
            )

        engine_list = self._get_engine_list(tasks, tasks_num_upperbound, engine_ids_with_prefixes)

        if len(engine_list) == 0:
            return

        best_engine = None
        max_counter = max(task.delay_counter for task in tasks)
        optimal_engine_found = False
        for engine in engine_list:
            if best_engine is None:
                best_engine = engine
                if self.config.ctx_aware and engine.engine_id in engine_ids_with_prefixes:
                    optimal_engine_found = True
            elif (
                self.config.ctx_aware
                and engine.engine_id in engine_ids_with_prefixes
                and best_engine.engine_id not in engine_ids_with_prefixes):
            # or engine.get_num_tasks() == 0:
                # Context-aware engine is preferred
                best_engine = engine
                optimal_engine_found = True
            else:
                # Select the best engine (minimizing the negative impacts, i.e. minimizing the decreasing of upperbound)
                # If the upperbound is not affected, select the engine with the most capacity.
                if (
                    engine.get_tasks_num_upperbound()
                    < best_engine.get_tasks_num_upperbound()
                ):
                    best_engine = engine
                elif (
                    engine.get_remain_tokens_capacity()
                    < best_engine.get_remain_tokens_capacity()
                ):
                    best_engine = engine
        print("engine id with prefix", engine_ids_with_prefixes)
        if DELAY_SCHEDULING_ON and MAX_DELAY_THRESHOLD > max_counter and not optimal_engine_found and engine_ids_with_prefixes:
            for task in tasks:
                # print("DELAYING")
                task.delay_counter += 1
            return 
        elif max_counter == MAX_DELAY_THRESHOLD:
            print("Group was delayed too much")

 
        # Dispatch the tasks to the engine
        assert best_engine is not None
        #print("Scheduled on: ", best_engine.engine_id)
        self.most_delay = max(max_counter, self.most_delay)
        print("Max counter: ", self.most_delay, max_counter)
        # sum([ for t in tasks])
        for task in tasks:
            # print("scheduling contexts", [context.context_id for context in task.contexts if context.is_constant])
            # print("scheduled length", self.context_mgr.prefix_caches[best_engine.engine_id].lru.cached_length)
            task.schedule_to(best_engine)
        self.total_scheduled += len(tasks)
        if not optimal_engine_found:
            self.bad_scheduled += len(tasks)
        print("BAD SCHEDULED COUNT", self.bad_scheduled, self.total_scheduled)  
    # ---------- Public Methods ----------

    def submit_task(self, task: CompletionTask) -> None:
        """Submit a task to the scheduler's queue."""

        if len(self.task_queue) >= self.config.max_queue_size:
            raise ParrotCoreUserError(
                RuntimeError(
                    f"Task queue is full. Current size: {len(self.task_queue)}. "
                    f"Hence the incoming task is rejected."
                )
            )

        logger.debug(
            f"Session(session_id={task.chain.session_id}) submit Task(task_id={task.task_id})"
            " to GlobalScheduler."
        )

        self.task_queue.append(task)
        task.status = TaskStatus.INQUEUE
        return

    def schedule(self) -> None:
        """Try to schedule all tasks in scheduler's queue."""

        if self.config.app_fifo:
            # Sort the tasks by the order of depth
            # The deeper the chain, the higher the priority
            self.task_queue.sort(key=lambda x: -x.chain.gen_node.sv.depth)

        # NOTE(chaofan): The tasks are sorted by priority, by default.
        for i, task in enumerate(self.task_queue):
            if task.is_scheduled:
                continue

            # Group tasks in rest queue
            cur_group: List[CompletionTask] = [task]
            chain_groups = set(task.chain.chain_groups)

            # Only allow one type of grouping at a time
            graph_group_enabled = self.config.graph_group
            ctx_group_enabled = self.config.ctx_group

            if graph_group_enabled or ctx_group_enabled:
                for j in range(i + 1, len(self.task_queue)):
                    task_j = self.task_queue[j]

                    # TODO(chaofan): Models match check
                    models_i = task.chain.metadata.models
                    models_j = task_j.chain.metadata.models

                    # TODO(chaofan): Criteria match check. Only group tasks with the same criteria.

                    if graph_group_enabled:
                        chain_groups_j = set(task_j.chain.chain_groups)
                        common_groups = chain_groups.intersection(chain_groups_j)
                        if len(common_groups) > 0:
                            if len(cur_group) < MAX_GROUP_LEN:
                                cur_group.append(task_j)
                                chain_groups = common_groups
                                ctx_group_enabled = False  # Use graph group this round

                    # Context group check
                    if ctx_group_enabled:
                        if task.chain.first_node.sv == task_j.chain.first_node.sv:
                            if len(cur_group) < MAX_GROUP_LEN:
                                cur_group.append(task_j)
                                graph_group_enabled = False  # Use context group this round


            # Try to find engines for the group
            self._find_engine(cur_group)

        # Update the task queue
        prev_task_queue = self.task_queue
        scheduled_task = [task for task in prev_task_queue if task.is_scheduled]
        self.task_queue = [task for task in prev_task_queue if not task.is_scheduled]

        # Display the scheduled results.
        # NOTE(chaofan): Only display >0 case to reduce the log size.
        if len(scheduled_task) > 0:
            logger.debug(
                f"Scheduled {len(scheduled_task)} tasks. Results: \n"
                + "\n".join(
                    [
                        f"  Task {task.task_id} -> engine: id={task.engine.engine_id}, name={task.engine.name}, "
                        f"num_tasks={task.engine.get_num_tasks()}, "
                        f"remain_tasks_capacity={task.engine.get_remain_tasks_capacity()}, "
                        f"remain_tokens_capacity={task.engine.get_remain_tokens_capacity()}, "
                        f"tasks_num_upperbound={task.engine.get_tasks_num_upperbound()}, "
                        f"tokens_num={task.engine.get_tokens_num()}, "
                        for task in scheduled_task
                    ]
                )
            )

        return
    



