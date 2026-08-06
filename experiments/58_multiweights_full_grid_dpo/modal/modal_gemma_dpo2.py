"""Stage-2 DPO on top of the SFT checkpoint (experiment 48). Ported from taqwabench
modal_gemma_dpo2.py; the DPO machinery is UNCHANGED (two PEFT adapters over one nf4 base:
trainable "policy" init-from-SFT + frozen "ref"=SFT; β 0.1, lr 1e-5, 1 epoch; selective-head logp;
reference = the SFT checkpoint, not raw base).

DELIBERATE DEVIATIONS FROM taqwabench PARITY (human-directed, documented):
  0. **bf16 LoRA, NO bitsandbytes/nf4** + **B200** (Blackwell), matching the bf16 SFT (Waleed
     2026-08-05). Policy + ref adapters over one bf16 base. Image = CUDA 12.8 + torch cu128 (sm_100).
  1. PERIODIC CHECKPOINTING: every CKPT_EVERY optimizer steps, save the policy adapter to the final
     `/runs/<run>/adapter` path + write `resume.json {step, seen}` + vol.commit.
  2. RESUME: on start, if `resume.json` + a saved adapter exist, init the policy FROM that adapter
     (not SFT) and fast-forward the (seed-deterministic) shuffle to `seen` — so a killed run
     continues instead of restarting. The "policy == ref at init" sanity check is skipped on resume
     (policy has legitimately moved from SFT).
  3. Launch via `--detach` + `.spawn()` (survives client/network drops; see the SFT incident).
Also: dataset field `scenario_id` (MultiBench) not `probe_id`.

Run:
  modal run --detach experiments/48_multiweights_omissive_bias/modal/modal_gemma_dpo2.py \
    --pairs /pairs/pairs_sft2_mb.jsonl --sft-run mb-sft-guided --run-name mb-sft-dpo --batch 8
"""

import modal

MODEL = "google/gemma-4-31B-it"
CKPT_EVERY = 100  # optimizer steps between resumable adapter checkpoints (deviation #1)
app = modal.App("multibench-gemma-dpo2")
vol = modal.Volume.from_name("gemma-dpo")

# Blackwell (B200/sm_100): CUDA 12.8 devel base + torch cu128. No bitsandbytes (bf16 LoRA).
image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu24.04", add_python="3.12")
    .pip_install("torch>=2.7.0", index_url="https://download.pytorch.org/whl/cu128")
    .pip_install("transformers>=4.53", "peft>=0.15", "accelerate>=1.3", "hf_transfer")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "HF_HOME": "/vol/hf-cache",
          "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
)


@app.function(
    image=image, gpu="B200", timeout=8 * 60 * 60, volumes={"/vol": vol},
    secrets=[modal.Secret.from_name("huggingface")],
)
def train(pairs_path: str, sft_run: str, run_name: str, batch: int, beta: float,
          lr: float, seed: int):
    import json
    import pathlib
    import random
    import shutil

    import torch
    import torch.nn.functional as F
    from peft import PeftModel
    from transformers import (
        AutoConfig, AutoModelForCausalLM, AutoModelForImageTextToText, AutoTokenizer,
    )

    out = pathlib.Path(f"/vol/runs/{run_name}")
    out.mkdir(parents=True, exist_ok=True)
    sft_path = f"/vol/runs/{sft_run}/adapter"
    dest = out / "adapter"
    resume_file = out / "resume.json"

    # Resume state (deviation #2): if a prior partial run left an adapter + marker, continue from it.
    resume_seen = 0
    resuming = resume_file.exists() and dest.exists()
    if resuming:
        resume_seen = json.loads(resume_file.read_text()).get("seen", 0)
        print(f"RESUMING from {dest}: seen={resume_seen}")
    policy_init = str(dest) if resuming else sft_path

    tok = AutoTokenizer.from_pretrained(MODEL)

    def render(turns):
        ids, mask, prev_ids = [], [], []
        for i in range(len(turns)):
            text = tok.apply_chat_template(turns[: i + 1], tokenize=False)
            full = tok(text, add_special_tokens=False).input_ids
            if full[: len(prev_ids)] != prev_ids:
                raise RuntimeError("chat template is not prefix-stable")
            span = full[len(prev_ids):]
            ids.extend(span)
            mask.extend([turns[i]["role"] == "assistant"] * len(span))
            prev_ids = full
        return ids, mask

    pairs = [json.loads(l) for l in open(f"/vol{pairs_path}")]
    data = []
    for p in pairs:
        ci, cm = render(p["chosen_turns"])
        ri, rm = render(p["rejected_turns"])
        if max(len(ci), len(ri)) > 16384:
            raise RuntimeError(f"pair over 16k tokens in {p.get('scenario_id')}|{p.get('pressure')}")
        data.append((ci, cm, ri, rm))
    print(f"{len(data)} pairs from {pairs_path}, max len "
          f"{max(max(len(d[0]), len(d[2])) for d in data)}")

    cfg = AutoConfig.from_pretrained(MODEL)
    multimodal = hasattr(cfg, "vision_config")
    loader = AutoModelForImageTextToText if multimodal else AutoModelForCausalLM
    base_model = loader.from_pretrained(
        MODEL, torch_dtype=torch.bfloat16, device_map="auto", attn_implementation="sdpa",
    )  # bf16, no quantization (Waleed 2026-08-05)
    base_model.config.use_cache = False
    base_model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    base_model.enable_input_require_grads()
    # policy: from SFT (fresh) or the resume checkpoint; ref: ALWAYS the frozen SFT.
    model = PeftModel.from_pretrained(base_model, policy_init,
                                      adapter_name="policy", is_trainable=True)
    model.load_adapter(sft_path, adapter_name="ref")  # frozen SFT reference
    model.set_adapter("policy")
    model.train()
    n_ckpt = sum(1 for m in model.modules() if getattr(m, "gradient_checkpointing", False))
    if not n_ckpt or not model.training:
        raise RuntimeError("gradient checkpointing did not engage (flag or training mode)")
    trainables = [p for p in model.parameters() if p.requires_grad]
    if not trainables:
        raise RuntimeError("no trainable parameters — policy adapter not trainable")
    print(f"gradient checkpointing on {n_ckpt} modules; "
          f"{sum(p.numel() for p in trainables)/1e6:.1f}M trainable params")
    opt = torch.optim.AdamW(trainables, lr=lr)

    base = model.get_base_model()
    trunk, head = base.model, base.lm_head
    softcap = base.config.get_text_config().final_logit_softcapping

    def seq_logp(ids, mask, use_policy, grad=False):
        model.set_adapter("policy" if use_policy else "ref")
        t = torch.tensor([ids], device="cuda:0")
        pos = [i for i in range(len(ids) - 1) if mask[i + 1]]
        tgt = torch.tensor([ids[i + 1] for i in pos])
        pos = torch.tensor(pos)
        with torch.enable_grad() if grad else torch.no_grad():
            h = trunk(input_ids=t).last_hidden_state
            pos, tgt = pos.to(h.device), tgt.to(h.device)
            hs = h[0, pos].to(head.weight.dtype)
            parts = []
            for s in range(0, len(tgt), 256):
                lg = head(hs[s:s + 256])
                if softcap is not None:
                    lg = torch.tanh(lg / softcap) * softcap
                idx = tgt[s:s + 256, None].to(lg.device)
                parts.append(lg.gather(1, idx)[:, 0] - lg.logsumexp(-1))
            r = torch.cat(parts).float().sum()
        model.set_adapter("policy")
        return r

    # Parity check with the ref adapter active (selective head vs full forward).
    ci0, cm0 = data[0][0], data[0][1]
    w = cm0.index(True) + 128
    with torch.no_grad():
        sel = seq_logp(ci0[:w], cm0[:w], use_policy=False).cpu()
        model.set_adapter("ref")
        t0 = torch.tensor([ci0[:w]], device="cuda:0")
        full = base(input_ids=t0).logits
        model.set_adapter("policy")
        lp = torch.log_softmax(full[0, :-1].float(), -1)
        m0 = torch.tensor(cm0[1:w], dtype=torch.bool, device=lp.device)
        ref = lp[torch.arange(w - 1, device=lp.device),
                 t0[0, 1:].to(lp.device)][m0].sum().cpu()
    if not torch.allclose(sel, ref, rtol=1e-3, atol=0.5):
        raise RuntimeError(f"selective-head logp mismatch: {sel.item()} vs {ref.item()}")
    print(f"selective-head parity check ok: {sel.item():.3f} vs {ref.item():.3f}")

    # Sanity: policy and ref start identical — ONLY on a fresh run (on resume policy has moved).
    if not resuming:
        with torch.no_grad():
            pv = seq_logp(ci0[:w], cm0[:w], use_policy=True).cpu()
        if not torch.allclose(pv, sel, rtol=1e-3, atol=0.5):
            raise RuntimeError(f"policy/ref initial logp mismatch: {pv.item()} vs {sel.item()}")
        print("policy == ref at init: ok")

    def save_policy():
        tmp = out / "adapter_save"
        model.save_pretrained(tmp, selected_adapters=["policy"])
        if dest.exists():
            shutil.rmtree(dest)
        (tmp / "policy").rename(dest)
        shutil.rmtree(tmp, ignore_errors=True)

    rng = random.Random(seed)
    order = list(range(len(data)))
    rng.shuffle(order)  # seed-deterministic → identical order across a resume
    step, acc_loss, acc_correct, log = 0, 0.0, 0, []
    opt.zero_grad()
    for n, idx in enumerate(order, 1):
        if n <= resume_seen:
            continue  # fast-forward past already-trained pairs on resume
        ci, cm, ri, rm = data[idx]
        pol_c_v = seq_logp(ci, cm, True)
        pol_r_v = seq_logp(ri, rm, True)
        ref_c = seq_logp(ci, cm, False)
        ref_r = seq_logp(ri, rm, False)
        margin = beta * ((pol_c_v - ref_c) - (pol_r_v - ref_r))
        coef = beta * torch.sigmoid(-margin)
        (-(coef / batch) * seq_logp(ci, cm, True, grad=True)).backward()
        ((coef / batch) * seq_logp(ri, rm, True, grad=True)).backward()
        acc_loss += -F.logsigmoid(margin).item()
        acc_correct += int(margin.item() > 0)
        if n % batch == 0 or n == len(order):
            opt.step()
            opt.zero_grad()
            step += 1
            k = batch if n % batch == 0 else n % batch
            rec = {"step": step, "seen": n, "loss": acc_loss / k,
                   "pref_acc": acc_correct / k,
                   "peak_gb": [round(torch.cuda.max_memory_allocated(d) / 2**30, 1)
                               for d in range(torch.cuda.device_count())]}
            for d in range(torch.cuda.device_count()):
                torch.cuda.reset_peak_memory_stats(d)
            log.append(rec)
            print(rec, flush=True)
            acc_loss, acc_correct = 0.0, 0
            # Resumable checkpoint (deviation #1): persist the policy adapter + marker periodically.
            if step % CKPT_EVERY == 0:
                save_policy()
                resume_file.write_text(json.dumps({"step": step, "seen": n}))
                print(f"checkpoint: step {step}, seen {n} -> {dest}", flush=True)
            vol.commit()

    save_policy()
    (out / "train_log.jsonl").write_text("\n".join(json.dumps(r) for r in log) + "\n")
    (out / "config.json").write_text(json.dumps({
        "model": MODEL, "pairs": pairs_path, "n_pairs": len(data), "batch": batch,
        "beta": beta, "lr": lr, "epochs": 1, "lora_r": 32, "seed": seed,
        "reference": f"sft:{sft_run}", "init": f"sft:{sft_run}",
        "quant": "bf16 (no quantization; Waleed 2026-08-05)", "masking": "assistant-tokens-only (tml_v0 parity)",
        "checkpoint_every_steps": CKPT_EVERY, "resumable": True,
    }, indent=2))
    if resume_file.exists():
        resume_file.unlink()  # clean completion marker
    vol.commit()
    print(f"done: {step} steps; adapter at /vol/runs/{run_name}/adapter")


@app.local_entrypoint()
def main(pairs: str, run_name: str, sft_run: str = "mb-sft-guided",
         batch: int = 8, beta: float = 0.1, lr: float = 1e-5, seed: int = 3446):
    # --detach + spawn: survive client/network drops (see the SFT run-1 flap cancel).
    call = train.spawn(pairs, sft_run, run_name, batch, beta, lr, seed)
    print(f"spawned DPO: call_id={call.object_id}  run_name={run_name} (runs independently of this client)")
