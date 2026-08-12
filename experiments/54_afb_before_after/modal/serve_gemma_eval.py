"""vLLM OpenAI server for the AFB before/after collection (#54): base gemma-4-31b + the DPO
INCUMBENT LoRA, exposed as two model names on one endpoint so both subjects hit the SAME serving
stack via the OpenAI seam.

  model="google/gemma-4-31B-it" -> base (vanilla gemma, catalog subject "gemma-4-31b-it")
  model="dpo"                   -> base + /vol/runs/mb-sft-dpo/adapter  (the #48 shipped incumbent,
                                   catalog subject "mb-sft-dpo")

This is a COPY of experiments/58's serve script (never edit #58's committed file — it is that
experiment's provenance), with `dpo` repointed from #58's scaling-null `mb-dpo-full` to the #48
incumbent `mb-sft-dpo`, and the `sft` module dropped (Waleed's vanilla↔DPO-only scope, #54).

Base is served bf16 with the LoRA applied — the adapter was trained against an nf4-quantized base
(recorded deviation, same as taqwabench/#48). Plain chat only: gemma-4-31b-it's tokenizer ships its
own chat template. No API key (short-lived eval endpoint on an obscure Modal URL; runners send
api_key="EMPTY"). Scale-to-zero after 10 min idle.

Deploy:  modal deploy experiments/54_afb_before_after/modal/serve_gemma_eval.py
Then the printed URL + "/v1" is EVAL_BASE_URL for the collection runner. Tear down after the run
(remove min_containers / stop the app — it is already scale-to-zero and idles down on its own).
"""

import subprocess

import modal

MODEL = "google/gemma-4-31B-it"
DPO_ADAPTER = "/vol/runs/mb-sft-dpo/adapter"  # #48 incumbent (NOT #58's mb-dpo-full), served as model="dpo"
VLLM_PORT = 8000
MINUTES = 60

app = modal.App("multibench-afb-eval-serve")
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
@modal.concurrent(max_inputs=64)  # one H200 handles the collection fan-out
@modal.web_server(port=VLLM_PORT, startup_timeout=15 * MINUTES)
def serve() -> None:
    cmd = [
        "vllm", "serve", MODEL,
        "--host", "0.0.0.0", "--port", str(VLLM_PORT),
        "--dtype", "bfloat16",
        "--max-model-len", "16384",
        "--gpu-memory-utilization", "0.92",
        "--enable-lora", "--max-lora-rank", "32",
        "--lora-modules", f"dpo={DPO_ADAPTER}",
    ]
    print("launching:", " ".join(cmd), flush=True)
    subprocess.Popen(cmd)
