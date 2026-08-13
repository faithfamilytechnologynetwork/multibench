"""vLLM OpenAI server for experiment 76 (prompt fading) — experiment-local copy of
`experiments/48/modal/serve_gemma_eval.py`, IDENTICAL except `--max-model-len` is raised
16384 -> 32768 to fit the long-fluff (L3 ~12k-token) sittings with headroom. The shipped
`serve_gemma_eval.py` is UNTOUCHED.

Exposes three model names on ONE H200 endpoint (OpenAI seam, no API key):
  model="google/gemma-4-31B-it" -> base            (arms A1, A2, and conditional arm C)
  model="dpo"                   -> base + /vol/runs/mb-sft-dpo/adapter  (arm B — the deliverable)
  model="sft"                   -> base + /vol/runs/mb-sft-guided/adapter (stretch arm only)

Deploy:  modal deploy experiments/76_prompt_fading/modal/serve_gemma_fading.py
Then the printed URL + "/v1" is EVAL_BASE_URL for collect_fading.py. Scale-to-zero after idle.
"""

import subprocess

import modal

MODEL = "google/gemma-4-31B-it"
SFT_ADAPTER = "/vol/runs/mb-sft-guided/adapter"
DPO_ADAPTER = "/vol/runs/mb-sft-dpo/adapter"
VLLM_PORT = 8000
MINUTES = 60

app = modal.App("multibench-gemma-fading-serve")
vol = modal.Volume.from_name("gemma-dpo")

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu24.04", add_python="3.12")
    .pip_install("vllm>=0.10", "hf_transfer")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HOME": "/vol/hf-cache",
          "VLLM_WORKER_MULTIPROC_METHOD": "spawn"})
)


@app.function(
    image=image, gpu="H200", timeout=6 * 60 * 60, volumes={"/vol": vol},
    secrets=[modal.Secret.from_name("huggingface")],
    scaledown_window=10 * MINUTES,
)
@modal.concurrent(max_inputs=64)  # one H200 handles the eval fan-out
@modal.web_server(port=VLLM_PORT, startup_timeout=15 * MINUTES)
def serve() -> None:
    cmd = [
        "vllm", "serve", MODEL,
        "--host", "0.0.0.0", "--port", str(VLLM_PORT),
        "--dtype", "bfloat16",
        "--max-model-len", "32768",  # exp-76: raised from 16384 for long-fluff (L3) sittings
        "--gpu-memory-utilization", "0.92",
        "--enable-lora", "--max-lora-rank", "32",
        "--lora-modules", f"sft={SFT_ADAPTER}", f"dpo={DPO_ADAPTER}",
    ]
    print("launching:", " ".join(cmd), flush=True)
    subprocess.Popen(cmd)
