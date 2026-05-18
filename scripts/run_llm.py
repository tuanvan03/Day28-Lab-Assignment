#!/usr/bin/env python3
"""
Run vLLM server locally with a lightweight model.
Lightest model: Qwen/Qwen2.5-0.5B-Instruct (only 0.5B parameters, ~1GB VRAM).
"""
import subprocess
import sys
import os

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
PORT = 8001

if __name__ == "__main__":
    # Reduce memory usage for low-VRAM GPUs (3.68 GiB)
    env = os.environ.copy()
    env["VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS"] = "0"

    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL,
        "--port", str(PORT),
        "--max-model-len", "1024",
        "--gpu-memory-utilization", "0.35",
        "--max-num-seqs", "16",
        "--dtype", "auto",
        "--enforce-eager",
    ]
    print(f"🚀 Starting vLLM with {MODEL} on port {PORT}...")
    print(f"   (Reduced VRAM mode: max-model-len=1024, gpu-mem=0.35, max-num-seqs=16, eager-mode)")
    subprocess.run(cmd, env=env)
