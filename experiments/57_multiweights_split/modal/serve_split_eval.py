"""vLLM OpenAI server for the experiment-57 descriptive eval: base gemma-4-31b + the SPLIT LoRA
adapters, exposed as model names on one endpoint (same stack as #48's serve_gemma_eval.py, distinct
app so it does not touch the #48 endpoint).

  model="google/gemma-4-31B-it" -> base (same-stack control; unused here, base reused from #53 CSV)
  model="sft"                   -> base + /vol/runs/mb-sft-split50/adapter
  model="dpo"                   -> base + /vol/runs/mb-dpo-split50/adapter  (only after DPO trains)

The DPO adapter does not exist during the SFT-descriptive phase, so lora modules are built from
whatever adapters are present on the volume at serve time — one script serves both phases. Plain
chat (gemma's own template); no api key (obscure Modal URL; runners send api_key="EMPTY").

Deploy:  modal deploy experiments/57_multiweights_split/modal/serve_split_eval.py
URL:     https://waleedkadous--multibench-gemma-eval-serve-split-serve.modal.run  (+ /v1)
Idles to zero after 10 min (scale-to-zero); no manual stop needed.
"""

import os
import subprocess

import modal

MODEL = "google/gemma-4-31B-it"
ADAPTERS = {
    "sft": "/vol/runs/mb-sft-split50/adapter",
    "dpo": "/vol/runs/mb-dpo-split50/adapter",
}
VLLM_PORT = 8000
MINUTES = 60

app = modal.App("multibench-gemma-eval-serve-split")
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
@modal.concurrent(max_inputs=64)
@modal.web_server(port=VLLM_PORT, startup_timeout=15 * MINUTES)
def serve() -> None:
    present = [f"{name}={path}" for name, path in ADAPTERS.items() if os.path.isdir(path)]
    cmd = [
        "vllm", "serve", MODEL,
        "--host", "0.0.0.0", "--port", str(VLLM_PORT),
        "--dtype", "bfloat16",
        "--max-model-len", "16384",
        "--gpu-memory-utilization", "0.92",
        "--enable-lora", "--max-lora-rank", "32",
        "--lora-modules", *present,
    ]
    print("serving adapters:", present, flush=True)
    print("launching:", " ".join(cmd), flush=True)
    subprocess.Popen(cmd)
