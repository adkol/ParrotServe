from typing import List, Optional
import torch

from parrot.utils import RecyclePool

from ..low_level_context import LowLevelContext


class BlockContext(LowLevelContext):
    """BlockContext: Use the idea of PagedAttention to manage the memory."""

    def __init__(
        self,
        context_id: int,
        parent_context: Optional["BlockContext"],
        kv_cache_manager: RecyclePool,
    ):
        super().__init__(context_id, parent_context)

        # KV blocks address
        self.token_kv_block_ids: List[int] = []
        self.token_ids: List[int] = []

        # KV cache manager i.e. a pool allocator.
        self.kv_cache_manager = kv_cache_manager

        # If the context is extended by the `fill` primitive, it should has a
        # `last_hidden_state` for the `generation` primitive.
        self.last_hidden_state: Optional[torch.Tensor] = None

    def destruction(self):
        super().destruction()

        for block_id in self.token_kv_block_ids:
            self.kv_cache_manager.free(block_id)

    def allocate(self, length: int):
        for _ in range(length):
            self.token_kv_block_ids.append(self.kv_cache_manager.allocate())

    def get_context_len(self) -> int:
        """Return the length of the context."""

        parent_len = self.parent_context.get_context_len() if self.parent_context else 0
        return parent_len + len(self.token_kv_block_ids)

    def get_context_blocks(self) -> List[int]:
        """Return the context blocks."""

        parent_blocks = (
            self.parent_context.get_context_blocks() if self.parent_context else []
        )
        return parent_blocks + self.token_kv_block_ids

    def get_last_token_id(self) -> int:
        """Return the last token id."""

        return self.token_ids[-1]
