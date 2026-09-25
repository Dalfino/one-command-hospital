#!/usr/bin/env python3
"""Build the HEADLESS Kaggle variant of gpu_pilot_notebook.ipynb.

Source of truth: repo notebook at 832c88b
  /home/z/my-project/hospital/download/one-command-hospital/gpu_pilot/gpu_pilot_notebook.ipynb

Headless deltas (vs the interactive original):
  cell 2: GitHub-PAT clone  -> private Kaggle dataset restore (zero tokens in kernel)
  cell 5: getpass HF token  -> removed; model ladder = official public AWQ -> BnB.4 -> fp16
  cell 7: gate results additionally collected into gate_summary.json (evidence pack input)
  cell 8: evidence pack also carries vLLM log tail + native stack logs + snapshot sha256

Outputs:
  /home/z/my-project/kaggle_pkg/kernel/gpu_pilot_notebook.ipynb
  /home/z/my-project/kaggle_pkg/kernel/kernel-metadata.json
"""
import json, ast, os, sys

SRC_NB = "/home/z/my-project/hospital/download/one-command-hospital/gpu_pilot/gpu_pilot_notebook.ipynb"
OUT_DIR = "/home/z/my-project/kaggle_pkg/kernel"
OUT_NB = os.path.join(OUT_DIR, "gpu_pilot_notebook.ipynb")
OUT_META = os.path.join(OUT_DIR, "kernel-metadata.json")

nb = json.load(open(SRC_NB))
cells = nb["cells"]
assert len(cells) == 10, f"expected 10 cells, got {len(cells)}"

# ---------------------------------------------------------------- cell 0 (md)
cells[0]["source"] = (
    "# GPU Pilot (headless) — One-Command Hospital on Kaggle T4 x2\n"
    "\n"
    "**Automated headless runbook** (pushed via Kaggle API; no human input cells):\n"
    "- repo snapshot restored from private dataset `aminurhakim/och-snapshot` — **no GitHub PAT inside this kernel**\n"
    "- vLLM serves **BioMistral-7B (official AWQ 4-bit → BnB.4 fallback → fp16 last resort)** — all public HF repos, no HF token\n"
    "- native stack in GPU shape (`LLM_URL` override, v0.6.2), guided decoding active\n"
    "- gates: test-unit / test-node / test-integration-native / eval (seed) / eval-full (208) / LIVE strict (LIVE_MODE=gpu) / loadtest (pilot-grade) / audit-verify\n"
    "- evidence pack (`gpu_pilot_evidence_<stamp>.tar.gz` + sha256 + `HOST_manifest.json` + `gate_summary.json`) lands in `/kaggle/working` = notebook output\n"
    "\n"
    "**This is NOT the Gate-5 sign-off run** — free shared VM; latency evidence is pilot-grade only\n"
    "(see `docs/gpu_pilot_plan.md` §4). Tier-1 success = trap refusal ≥90% AND citation validity ≥80% AND red-team floor held.\n"
    "\n"
    "Run config: Accelerator **GPU T4 ×2** (`machine_shape: NvidiaTeslaT4`), Internet **On**, private kernel.\n"
)

# ---------------------------------------------------------------- cell 1 (unchanged)
# GPU introspection stays exactly as-is.

# ---------------------------------------------------------------- cell 2 (dataset restore)
cells[2]["source"] = r'''# CELL 2 — Restore repo snapshot from the private Kaggle dataset (headless; NO tokens in this kernel)
import tarfile, os, glob, shutil, hashlib, subprocess

BASE = "/kaggle/working" if os.path.isdir("/kaggle") else "/content"
SNAP = None
for pat in ["/kaggle/input/och-snapshot/och-snapshot.tar.gz",
            "/kaggle/input/*/och-snapshot.tar.gz",
            "/content/och-snapshot.tar.gz"]:
    hits = glob.glob(pat)
    if hits:
        SNAP = hits[0]; break
assert SNAP, "och-snapshot.tar.gz not found under /kaggle/input — attach dataset aminurhakim/och-snapshot and rerun"

WORK = os.path.join(BASE, "repo")
shutil.rmtree(WORK, ignore_errors=True)
os.makedirs(WORK, exist_ok=True)
snap_sha = hashlib.sha256(open(SNAP, "rb").read()).hexdigest()
with tarfile.open(SNAP) as t:
    t.extractall(WORK)

REPO_DIR = os.path.join(WORK, "download", "one-command-hospital")
assert os.path.isdir(REPO_DIR), f"unexpected snapshot layout: {os.listdir(WORK)}"
os.chdir(REPO_DIR)
os.environ["OCH_SNAPSHOT_SHA256"] = snap_sha
print("repo restored ->", os.getcwd())
print("snapshot sha256:", snap_sha)
print("top-level:", sorted(os.listdir("."))[:24])
'''

# ---------------------------------------------------------------- cell 3 (unchanged)
# Interface discovery stays as-is (runs from the restored project root).

# ---------------------------------------------------------------- cell 4 (unchanged)
# Dependencies cell stays as-is.

# ---------------------------------------------------------------- cell 5 (vLLM, no getpass)
cells[5]["source"] = r'''# CELL 5 — Launch vLLM: BioMistral-7B 4-bit on :8099 (official public AWQ -> BnB.4 -> fp16 ladder)
# No HF token needed: every candidate is a PUBLIC, non-gated HF repo (BioMistral org).
import subprocess, time, os, signal, sys
import requests

PORT = 8099
# (model_id, extra vllm flags) — int4 first (fits free T4 16GB), fp16 last resort at reduced ctx
CANDIDATES = [
    ("BioMistral/BioMistral-7B-AWQ-QGS128-W4-GEMM",
     ["--max-model-len", "4096", "--gpu-memory-utilization", "0.90"]),
    ("BioMistral/BioMistral-7B-BnB.4",
     ["--quantization", "bitsandbytes", "--load-format", "bitsandbytes",
      "--max-model-len", "4096", "--gpu-memory-utilization", "0.90"]),
    ("BioMistral/BioMistral-7B",
     ["--max-model-len", "2048", "--gpu-memory-utilization", "0.95"]),
]
proc, model_used, ok = None, None, False

for m, extra in CANDIDATES:
    cmd = [sys.executable, "-m", "vllm.entrypoints.openai.api_server",
           "--model", m, "--port", str(PORT), "--enforce-eager"] + extra
    print("launching", m, "(cold download ~5GB — expect up to 20 min)...")
    proc = subprocess.Popen(cmd, stdout=open(f"/tmp/vllm_{PORT}.log", "w"), stderr=subprocess.STDOUT)
    for _ in range(150):  # 150 x 10s = 25 min per candidate
        time.sleep(10)
        try:
            if requests.get(f"http://127.0.0.1:{PORT}/health", timeout=2).status_code == 200:
                ok = True; break
        except Exception:
            pass
        if proc.poll() is not None:
            break
    if ok:
        model_used = m; break
    print("failed:", m, "— tail of log:")
    print(open(f"/tmp/vllm_{PORT}.log").read()[-1200:])
    try: proc.send_signal(signal.SIGTERM)
    except Exception: pass
    proc = None

assert ok, f"vLLM failed for all candidates — inspect /tmp/vllm_{PORT}.log (OOM? quota? kernel mismatch?)"
print("vLLM healthy:", model_used, "on :", PORT)
os.environ["GENERATOR_BASE_URL"] = f"http://127.0.0.1:{PORT}/v1"
os.environ["GENERATOR_MODEL"] = model_used
s = requests.post(f"http://127.0.0.1:{PORT}/v1/chat/completions",
                  json={"model": model_used, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 8}, timeout=60)
print("smoke:", s.status_code, s.json()["choices"][0]["message"]["content"][:40] if s.status_code == 200 else s.text[:200])
'''

# ---------------------------------------------------------------- cell 6 (unchanged)
# Native stack + health + generator smoke stays as-is.

# ---------------------------------------------------------------- cell 7 (gates + summary)
cells[7]["source"] = r'''# CELL 7 — Gates: unit / node / integration-native / eval(seed) / eval-full(208) / LIVE strict / loadtest(pilot) / audit
import subprocess, os, json, time

RAG = "http://127.0.0.1:8101"
GATES = []

def run(cmd, timeout=3600):
    print()
    print(f">>> {cmd}")
    t0 = time.time()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    print(r.stdout[-4500:])
    if r.returncode != 0:
        print("STDERR:", r.stderr[-2000:])
    print(f"--- exit: {r.returncode} ({time.time()-t0:.0f}s) ---")
    GATES.append({"cmd": cmd.split()[0] if cmd.startswith("make") else cmd.split(" ")[0],
                  "exit": r.returncode, "seconds": round(time.time() - t0, 1)})
    return r

run("make test-unit")                       # pytest unit tier
run("make test-node")                       # audit chain, redaction, metrics
run("make test-integration-native")         # golden path / fail-closed / PHI on mock test stack (8210-8213)
run(f"RAG_URL={RAG} make eval")             # seed eval, full mode (citations checked vs live stack)
run(f"RAG_URL={RAG} make eval-full")        # 208-question eval vs live GPU-backed stack
run(f"RAG_URL={RAG} LIVE_MODE=gpu python -m pytest tests/live -m live -v")  # STRICT: trap refusal >=90%, citation validity >=80%, red-team floor
run("make loadtest LOCUST_USERS=20 LOCUST_RUN_TIME=2m")  # pilot-grade latency ONLY (shared VM)
run("make audit-verify")                    # hash-chained audit log walk

base = "/kaggle/working" if os.path.isdir("/kaggle") else "/content"
summary = {"gates": GATES,
           "tier1_live_exit": next((g["exit"] for g in GATES if "pytest" in g["cmd"]), None),
           "generator_model": os.environ.get("GENERATOR_MODEL"),
           "snapshot_sha256": os.environ.get("OCH_SNAPSHOT_SHA256"),
           "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
json.dump(summary, open(os.path.join(base, "gate_summary.json"), "w"), indent=2)
print(json.dumps(summary, indent=2))

print("\n>>> READ tests/live OUTPUT — Tier-1 success = trap refusal >= 90% AND citation validity >= 80% AND red-team floor held")
print(">>> Latency numbers are PILOT-GRADE ONLY (shared VM). Gate-5 sign-off loadtest runs on local/24GB or a ~$2-5 paid spot.")
'''

# ---------------------------------------------------------------- cell 8 (evidence pack richer)
cells[8]["source"] = r'''# CELL 8 — Evidence harvest: HOST manifest + logs + tarball + sha256 (Kaggle: /kaggle/working = output)
import subprocess, os, json, hashlib, tarfile, time, shutil, glob

stamp = time.strftime("%Y%m%d_%H%M%S")
gpu_q = subprocess.run(["bash", "-lc", "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader"],
                       capture_output=True, text=True).stdout.strip()
host = {"provider": "kaggle" if os.path.isdir("/kaggle") else "colab" if os.path.isdir("/content") else "unknown",
        "gpu": gpu_q, "shared_vm": True, "timestamp_utc": stamp,
        "model": os.environ.get("GENERATOR_MODEL"),
        "snapshot_sha256": os.environ.get("OCH_SNAPSHOT_SHA256")}
manifest = {"host": host,
            "caveat": "free shared-VM — pilot-grade evidence, not Gate-5 sign-off",
            "gate5_signoff": False}
os.makedirs("eval/evidence", exist_ok=True)
json.dump(manifest, open("eval/evidence/HOST_manifest.json", "w"), indent=2)

# carry run logs into the evidence dir (best-effort)
base = "/kaggle/working" if os.path.isdir("/kaggle") else "/content"
try:
    if os.path.exists(f"/tmp/vllm_{PORT}.log"):
        open("eval/evidence/vllm_8099_tail.log", "w").write(open(f"/tmp/vllm_{PORT}.log").read()[-20000:])
except Exception as e:
    print("vllm log copy skipped:", e)
try:
    for lg in glob.glob("/tmp/och-native-stack/logs/*"):
        shutil.copy(lg, "eval/evidence/native_" + os.path.basename(lg))
except Exception as e:
    print("stack log copy skipped:", e)
try:
    shutil.copy(os.path.join(base, "gate_summary.json"), "eval/evidence/gate_summary.json")
except Exception as e:
    print("gate summary copy skipped:", e)

out = os.path.join(base, f"gpu_pilot_evidence_{stamp}.tar.gz")
with tarfile.open(out, "w:gz") as t:
    t.add("eval/evidence", arcname="eval/evidence")
digest = hashlib.sha256(open(out, "rb").read()).hexdigest()
print("evidence tarball:", out)
print("sha256:", digest)
print(json.dumps(manifest, indent=2))

try:
    from google.colab import drive  # Colab only
    drive.mount("/content/drive")
    shutil.copy(out, "/content/drive/MyDrive/")
    print("copied to Google Drive: MyDrive/" + os.path.basename(out))
except Exception as e:
    print("(Drive copy skipped:", type(e).__name__, "— on Kaggle the tarball is in /kaggle/working notebook output)")
'''

# ---------------------------------------------------------------- cell 9 (unchanged)
# Teardown stays as-is.

# ---------------------------------------------------------------- write + validate
os.makedirs(OUT_DIR, exist_ok=True)
json.dump(nb, open(OUT_NB, "w"), indent=1)

meta = {
    "id": "aminurhakim/gpu-pilot-notebook",
    "title": "gpu_pilot_notebook",
    "code_file": "gpu_pilot_notebook.ipynb",
    "language": "python",
    "kernel_type": "notebook",
    "is_private": "true",
    "enable_gpu": "true",
    "enable_tpu": "false",
    "enable_internet": "true",
    "machine_shape": "NvidiaTeslaT4",
    "dataset_sources": ["aminurhakim/och-snapshot"],
    "competition_sources": [],
    "kernel_sources": [],
    "model_sources": [],
}
json.dump(meta, open(OUT_META, "w"), indent=2)

# validation: JSON round-trip + AST for every code cell
reloaded = json.load(open(OUT_NB))
errors = []
for i, c in enumerate(reloaded["cells"]):
    src = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
    if c["cell_type"] == "code":
        try:
            ast.parse(src)
        except SyntaxError as e:
            errors.append(f"cell {i}: {e}")
        if "getpass" in src:
            errors.append(f"cell {i}: getpass found (headless must not prompt)")
        if "github_pat" in src.lower() or "hf_" + "rimc" in src or "KGAT_" in src:
            errors.append(f"cell {i}: TOKEN LITERAL FOUND")
blob = json.dumps(reloaded)
for lit in ("github_pat_11BHM2YDA0", "hf_rimcMqSp", "KGAT_df89c288"):
    if lit in blob:
        errors.append(f"notebook contains literal token {lit[:12]}...")

if errors:
    print("VALIDATION FAILED:"); [print(" -", e) for e in errors]; sys.exit(1)
print("OK: notebook written,", len(reloaded["cells"]), "cells, AST valid, no prompts, no token literals")
print("OK: kernel-metadata.json written (machine_shape=NvidiaTeslaT4, dataset=aminurhakim/och-snapshot)")
