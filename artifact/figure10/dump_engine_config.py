import sys
import json

cap = int(sys.argv[1])

config = {
    "engine_name": "vicuna-13b-v1.3_local",
    "model": "lmsys/vicuna-13b-v1.3",
    "host": "localhost",
    "port": 9001,
    "engine_type": "builtin",
    "random_seed": 0,
    "tokenizer": "hf-internal-testing/llama-tokenizer",
    "fill_chunk_size": -1,
    "threads_capacity": 256,
    "instance": {
        "block_size": 16,
        "num_kv_cache_blocks": 3800,
        "attn_func": "xformers_fill_vllm_paged_attention_generate",
    },
    "scheduler": {
        "max_batch_size": 256,
        "max_num_batched_tokens": 2560,
        "max_total_tokens": cap,
        "policy": "fifo_v1",
    },
    "os": {"host": "localhost", "port": 9000},
}

with open("cluster_1_vicuna_13b_vllm/engine.json", "w") as f:
    json.dump(config, f)
