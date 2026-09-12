"""vLLM OpenAI server for experiment 126 (prompt fading, L4 ~32k) — copy of #78's
`serve_gemma_fading.py`, IDENTICAL except `--max-model-len` is raised 32768 -> 49152 to fit the
L4 (~32k-token) filler sittings: guide + 32k fluff + the clean dilemma turns + generation, with
headroom. Deployed as a DISTINCT app so #78's `multibench-gemma-fading-serve` stays intact.

Context-length check (done BEFORE raising, from the model config — not memory): Gemma 4 31B's
`config.json` reports text_config.max_position_embeddings = 262144 (256k). 49,152 << 256k, so the
window is supported. Expect LOWER concurrency than #78 at this prompt length (KV cache grows with
context) — measure warm throughput in the smoke and project the full run off that, not #78's rate.

Exposes three model names on ONE H200 endpoint (OpenAI seam, no API key):
  model="google/gemma-4-31B-it" -> base            (arms A1, A2, and conditional arm C)
  model="dpo"                   -> base + /vol/runs/mb-sft-dpo/adapter  (arm B — the deliverable)
  model="sft"                   -> base + /vol/runs/mb-sft-guided/adapter (stretch arm only)

Deploy:  modal deploy experiments/126_prompt_fading_32k/modal/serve_gemma_fading.py
Then the printed URL + "/v1" is EVAL_BASE_URL for collect_fading.py. Scale-to-zero after idle.
"""

import subprocess

import modal

MODEL = "google/gemma-4-31B-it"
SFT_ADAPTER = "/vol/runs/mb-sft-guided/adapter"
DPO_ADAPTER = "/vol/runs/mb-sft-dpo/adapter"
VLLM_PORT = 8000
MINUTES = 60

app = modal.App("multibench-gemma-fading-32k-serve")
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
        "--max-model-len", "49152",  # exp-126: raised from 32768 for L4 (~32k fluff) sittings; 49k << 256k ctx
        "--gpu-memory-utilization", "0.92",
        "--enable-lora", "--max-lora-rank", "32",
        "--lora-modules", f"sft={SFT_ADAPTER}", f"dpo={DPO_ADAPTER}",
    ]
    print("launching:", " ".join(cmd), flush=True)
    subprocess.Popen(cmd)
