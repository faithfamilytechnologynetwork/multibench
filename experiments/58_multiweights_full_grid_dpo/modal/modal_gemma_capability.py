"""Capability-regression panel for the MultiWeights checkpoints (experiment 58).

MEASUREMENT FIX (architect 2026-08-06): #48's panel ran lm-eval in RAW-COMPLETION mode on an
instruction-tuned model — MMLU ~0.467 etc. were completion-mode ARTIFACTS (base gemma-4-31b-it is
~85-class MMLU chat-formatted), and IFEval barely measured instruction-following at all. This panel
runs CHAT mode (--apply_chat_template --fewshot_as_multiturn, max_model_len 8192, output dirs
`*-chat`), ported from taqwabench's fixed script (tmp/dpo-experiment/modal_gemma_capability.py).

For exp-58 the capability leg is a FOUR-checkpoint chat-mode panel — base, mb-sft-guided,
mb-sft-dpo (incumbent), mb-dpo-full (new head) — so the four-gate MMLU comparison re-anchors to
chat-mode numbers measured in THIS SAME rerun (the old 0.4424 completion-mode threshold is void).
Sanity-check the chat-mode BASE absolutes against the model card / RedHat lm-eval anchors before
reporting; if base lands far off class, STOP (do not decide on unanchored numbers).

Run (all four, chat): modal run --detach experiments/58_multiweights_full_grid_dpo/modal/modal_gemma_capability.py --chat
Out: /vol/runs/capability/<checkpoint>-chat/ (lm-eval result JSONs) + stdout table
"""

import modal

MODEL = "google/gemma-4-31B-it"
app = modal.App("multibench58-gemma-capability")
vol = modal.Volume.from_name("gemma-dpo")

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu24.04", add_python="3.12")
    .pip_install("vllm>=0.10", "lm_eval[vllm,ifeval]>=0.4.8", "hf_transfer")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HOME": "/vol/hf-cache",
          "VLLM_WORKER_MULTIPROC_METHOD": "spawn", "HF_ALLOW_CODE_EVAL": "1"})
)

# The four-gate re-anchoring panel: base + the three heads, all measured in the SAME chat-mode rerun.
CHECKPOINTS = {
    "base": None,
    "mb-sft-guided": "/vol/runs/mb-sft-guided/adapter",
    "mb-sft-dpo": "/vol/runs/mb-sft-dpo/adapter",       # incumbent
    "mb-dpo-full": "/vol/runs/mb-dpo-full/adapter",     # exp-58 new head
}
TASKS = "ifeval,mmlu,gsm8k_cot"


@app.function(
    image=image, gpu="H200", timeout=5 * 60 * 60, volumes={"/vol": vol},
    secrets=[modal.Secret.from_name("huggingface")],
)
def run_panel(name: str, tasks: str = TASKS, log_samples: bool = False, chat: bool = False):
    import subprocess

    adapter = CHECKPOINTS[name]
    # Chat mode = deployment-faithful for an -it model: chat template applied, few-shot as multi-turn,
    # 8k ctx headroom for template tokens. Raw-completion kept only for continuity with #48.
    max_len = 8192 if chat else 4096
    margs = (f"pretrained={MODEL},dtype=bfloat16,gpu_memory_utilization=0.9,"
             f"max_model_len={max_len}")
    if adapter:
        margs += f",enable_lora=True,max_lora_rank=32,lora_local_path={adapter}"
    suffix = ("-chat" if chat else "") + ("-samples" if log_samples else "")
    out = f"/vol/runs/capability/{name}{suffix}"
    cmd = ["lm_eval", "--model", "vllm", "--model_args", margs,
           "--tasks", tasks, "--batch_size", "auto", "--output_path", out]
    if chat:
        cmd += ["--apply_chat_template", "--fewshot_as_multiturn"]
    if log_samples:
        cmd.append("--log_samples")
    print("running:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    vol.commit()
    print(f"panel done: {name}")


@app.local_entrypoint()
def main(only: str = "", tasks: str = TASKS, log_samples: bool = False, chat: bool = False):
    # spawn + detach: survives local client/network drops; completion observed via the volume.
    names = [only] if only else list(CHECKPOINTS)
    handles = [run_panel.spawn(n, tasks, log_samples, chat) for n in names]
    print("spawned:", names)
    for h in handles:
        h.get()
