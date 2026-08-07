"""Verify a file ON the gemma-dpo volume as the volume actually stores it (experiment 57).

`modal volume put` can SILENTLY truncate/corrupt large files while reporting success (exp-58 infra
scar 2026-08-06: a 16.9MB file 404'd on a storage block; another landed 172/1584 lines). The only
reliable check is a SHA-256 + line-count round-trip computed on the VOLUME side — that is what a
training job will actually read. This function returns the volume-side sha256 + line count; the
`verified_put.sh` wrapper compares it to the local file and retries the put until they match.

Run (via wrapper, not directly):
  modal run experiments/57_multiweights_split/modal/modal_volume_verify.py --path /pairs/<name>
"""

import modal

app = modal.App("mb-volume-verify")
vol = modal.Volume.from_name("gemma-dpo")
image = modal.Image.debian_slim(python_version="3.12")


@app.function(image=image, volumes={"/vol": vol}, timeout=600)
def verify(path: str):
    import hashlib

    p = f"/vol{path}"
    h = hashlib.sha256()
    lines = 0
    size = 0
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            size += len(chunk)
            lines += chunk.count(b"\n")
    return {"sha256": h.hexdigest(), "lines": lines, "bytes": size}


@app.local_entrypoint()
def main(path: str):
    import json
    print(json.dumps(verify.remote(path)))
