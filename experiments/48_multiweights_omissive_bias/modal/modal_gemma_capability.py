"""Capability-regression panel for the MultiWeights checkpoints (experiment 48 guard).

Ported VERBATIM from taqwabench modal_gemma_capability.py (architect: "copy their exact lm-eval
config"). lm-evaluation-harness over the same vLLM stack: IFEval + MMLU 5-shot + GSM8K CoT. Standard
task configs so numbers are comparable to published gemma results and to the taqwabench baseline
(base/sft/sft+dpo = MMLU 0.467/0.468/0.470, GSM8K-CoT-strict 0.792/0.867/0.848,
IFEval-inst-strict 0.273/0.279/0.282 — no regression).

Run: modal run --detach experiments/48_multiweights_omissive_bias/modal/modal_gemma_capability.py
Out: /vol/runs/capability/<checkpoint>/ (lm-eval result JSONs) + stdout table
"""

import modal

MODEL = "google/gemma-4-31B-it"
app = modal.App("multibench-gemma-capability")
vol = modal.Volume.from_name("gemma-dpo")

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu24.04", add_python="3.12")
    .pip_install("vllm>=0.10", "lm_eval[vllm,ifeval]>=0.4.8", "hf_transfer")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HOME": "/vol/hf-cache",
          "VLLM_WORKER_MULTIPROC_METHOD": "spawn", "HF_ALLOW_CODE_EVAL": "1"})
)

# base + our stage-1 adapter; sft-dpo slot filled after stage 2.
CHECKPOINTS = {
    "base": None,
    "mb-sft-guided": "/vol/runs/mb-sft-guided/adapter",
    # "mb-sft-dpo": "/vol/runs/mb-sft-dpo/adapter",  # add after stage-2 DPO
}
TASKS = "ifeval,mmlu,gsm8k_cot"


@app.function(
    image=image, gpu="H200", timeout=5 * 60 * 60, volumes={"/vol": vol},
    secrets=[modal.Secret.from_name("huggingface")],
)
def run_panel(name: str):
    import subprocess

    adapter = CHECKPOINTS[name]
    margs = f"pretrained={MODEL},dtype=bfloat16,gpu_memory_utilization=0.9,max_model_len=4096"
    if adapter:
        margs += f",enable_lora=True,max_lora_rank=32,lora_local_path={adapter}"
    out = f"/vol/runs/capability/{name}"
    cmd = ["lm_eval", "--model", "vllm", "--model_args", margs,
           "--tasks", TASKS, "--batch_size", "auto", "--output_path", out]
    print("running:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    vol.commit()
    print(f"panel done: {name}")


@app.local_entrypoint()
def main(only: str = ""):
    # spawn + detach: survives local client/network drops; completion observed via the volume.
    names = [only] if only else list(CHECKPOINTS)
    handles = [run_panel.spawn(n) for n in names]
    print("spawned:", names)
    for h in handles:
        h.get()
