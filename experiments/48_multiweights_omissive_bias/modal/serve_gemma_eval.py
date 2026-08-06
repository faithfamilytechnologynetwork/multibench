"""vLLM OpenAI server for the eval sweep (experiment 48): base gemma-4-31b + the SFT LoRA, exposed
as TWO model names on one endpoint so every eval runner (AFB, over-application probes, MultiBench
descriptive) hits the SAME serving stack via the OpenAI seam.

  model="google/gemma-4-31B-it" -> base (the same-stack base control)
  model="sft"                   -> base + /vol/runs/mb-sft-guided/adapter  (stage-1 checkpoint)
  (add "dpo" after stage 2)

Base is served bf16 with the LoRA applied — the adapter was trained against an nf4-quantized base
(recorded deviation, same as taqwabench). Plain chat only: gemma-4-31b-it's tokenizer ships its own
chat template, so no --chat-template / reasoning / tool-parser flags are needed (unlike the shannon
tool-calling server). Image = taqwabench's proven vllm>=0.10 gemma-4 image (cuda devel for the
router-GEMM kernel compile). No API key (short-lived eval endpoint on an obscure Modal URL; runners
send api_key="EMPTY"). Scale-to-zero after 10 min idle.

Deploy:  modal deploy experiments/48_multiweights_omissive_bias/modal/serve_gemma_eval.py
Then the printed URL + "/v1" is the base_url for the eval runners. Stop by removing min_containers
(it is already scale-to-zero) — the app idles down on its own.
"""

import os
import subprocess

import modal

MODEL = "google/gemma-4-31B-it"
SFT_ADAPTER = "/vol/runs/mb-sft-guided/adapter"
DPO_ADAPTER = "/vol/runs/mb-sft-dpo/adapter"  # stage-2 checkpoint (served as model="dpo")
VLLM_PORT = 8000
MINUTES = 60

app = modal.App("multibench-gemma-eval-serve")
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
        "--max-model-len", "16384",
        "--gpu-memory-utilization", "0.92",
        "--enable-lora", "--max-lora-rank", "32",
        "--lora-modules", f"sft={SFT_ADAPTER}", f"dpo={DPO_ADAPTER}",
    ]
    print("launching:", " ".join(cmd), flush=True)
    subprocess.Popen(cmd)
