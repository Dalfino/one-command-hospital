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
# The tarball name is VERSION-UNIQUE (och-snapshot-<repo-sha>.tar.gz) and its sha256 is pinned
# at build time — Kaggle's server-side tar extraction is async/inconsistent and stale trees
# from older dataset versions linger in the mount; a unique name + sha check makes the
# restore deterministic (kernel extracts the exact tarball itself, never trusts the mount tree).
snap_name = os.environ.get("SNAP_TAR_NAME", "och-snapshot.tar.gz")
snap_sha = os.environ.get("SNAP_TAR_SHA256", "")
cells[2]["source"] = r'''# CELL 2 — Restore repo snapshot from the private Kaggle dataset (headless; NO tokens in this kernel)
import os, glob, shutil, hashlib, tarfile, time

BASE = "/kaggle/working" if os.path.isdir("/kaggle") else "/content"
DS = "/kaggle/input/och-snapshot" if os.path.isdir("/kaggle/input/och-snapshot") \
     else (sorted(glob.glob("/kaggle/input/*")) or [None])[0]
assert DS and os.path.isdir(DS), f"och-snapshot dataset not mounted — /kaggle/input: {glob.glob('/kaggle/input/*')}"
TARBALL = "__SNAP_NAME__"
EXPECT_SHA = "__SNAP_SHA__"

tar_hit = None
for _ in range(30):  # up to 150s for server-side processing to materialize
    hits = [t for t in glob.glob(os.path.join(DS, "**", TARBALL), recursive=True) if os.path.isfile(t)]
    if hits:
        tar_hit = hits[0]; break
    time.sleep(5)
assert tar_hit, f"{TARBALL} not found under {DS} — contents: {sorted(os.listdir(DS))[:20]}"

got = hashlib.sha256(open(tar_hit, "rb").read()).hexdigest()
assert got == EXPECT_SHA, f"snapshot sha mismatch: got {got[:16]}... expected {EXPECT_SHA[:16]}... (stale dataset version?)"

WORK = os.path.join(BASE, "repo")
shutil.rmtree(WORK, ignore_errors=True)
os.makedirs(WORK, exist_ok=True)
with tarfile.open(tar_hit) as t:
    t.extractall(WORK)
cand = glob.glob(os.path.join(WORK, "**", "download", "one-command-hospital"), recursive=True)
assert cand, "tarball extracted but project subtree not found"
REPO_DIR = cand[0]

os.chdir(REPO_DIR)
os.environ["OCH_SNAPSHOT_SHA256"] = got
print("repo restored ->", os.getcwd())
print("tarball:", TARBALL, "| sha256:", got)
print("top-level:", sorted(os.listdir("."))[:24])
'''.replace("__SNAP_NAME__", snap_name).replace("__SNAP_SHA__", snap_sha)

# ---------------------------------------------------------------- cell 3 (unchanged)
# Interface discovery stays as-is (runs from the restored project root).

# ---------------------------------------------------------------- cell 4 (deps: eval+tests+SERVICES+model+vllm+locust)
cells[4]["source"] = r'''# CELL 4 — Dependencies: eval + tests + SERVICES requirements + spacy model + vLLM + locust
# (native path has no Dockerfile: deid-gate needs presidio+spacy model, verifier uses medspacy,
#  loadtest needs locust — the exact set the compose images otherwise install)
import subprocess, sys, os

def pip(*args):
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", *args], capture_output=True, text=True)
    tag = "ok" if r.returncode == 0 else "FAIL: " + (r.stderr or r.stdout)[-500:]
    print("pip", " ".join(args)[:60], "->", tag)
    return r

pip("-U", "pip")
for req in ["eval/requirements.txt", "tests/requirements.txt",
            "services/deid-gate/requirements.txt",
            "services/guideline-rag/requirements.txt",
            "services/verifier/requirements.txt"]:
    if os.path.exists(req):
        pip("-r", req)
    else:
        print("!!", req, "missing — discovery cell output should explain the tree shape")

# deid-gate SPACY_MODEL default = en_core_web_sm (Dockerfile parity)
r = subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], capture_output=True, text=True)
print("spacy en_core_web_sm ->", "ok" if r.returncode == 0 else "FAIL: " + (r.stderr or r.stdout)[-400:])

pip("locust")  # make loadtest falls back to docker otherwise — no docker on notebook VMs

r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "vllm"], capture_output=True, text=True)
print("vllm install tail:", (r.stdout or r.stderr)[-600:])
r = subprocess.run([sys.executable, "-c", "import vllm; print('vllm OK', vllm.__version__)"], capture_output=True, text=True)
print(r.stdout or r.stderr)
assert r.returncode == 0, "vLLM install failed"
'''
# ---------------------------------------------------------------- cell 5 (vLLM, no getpass)
cells[5]["source"] = r'''# CELL 5 — Launch vLLM: BioMistral-7B 4-bit on :8099 (official public AWQ -> BnB.4 -> fp16 ladder)
# No HF token needed: every candidate is a PUBLIC, non-gated HF repo (BioMistral org).
import subprocess, time, os, signal, sys
import requests

PORT = 8099
# v0.6.3 pilot finding: BASE BioMistral-7B answers sanely (4.7s/GPU gen) but ignores the
# citation contract (citations=[], zero inline [CORPUS §N] markers) -> Tier-1 gates fail.
# Experiment: the org's Zephyr-Beta SLERP merge (DPO chat-tuned, public, int4) first.
CANDIDATES = [
    ("BioMistral/BioMistral-7B-Zephyr-Beta-SLERP-AWQ-QGS128-W4-GEMM",
     ["--max-model-len", "4096", "--gpu-memory-utilization", "0.90"]),
    ("BioMistral/BioMistral-7B-AWQ-QGS128-W4-GEMM",
     ["--max-model-len", "4096", "--gpu-memory-utilization", "0.90"]),
]
proc, model_used, ok = None, None, False

for m, extra in CANDIDATES:
    SERVED = m  # serve under the real id; native_stack.sh forwards LLM_MODEL (v0.6.3)
    cmd = [sys.executable, "-m", "vllm.entrypoints.openai.api_server",
           "--model", m, "--served-model-name", SERVED,
           "--port", str(PORT), "--enforce-eager"] + extra
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

# ---------------------------------------------------------------- cell 6 (stack: longer health budget + self-diagnosis)
cells[6]["source"] = r'''# CELL 6 — Probe the live vLLM wire shapes, then start NATIVE stack in GPU shape + health-wait
# v0.6.3 findings baked in here: (a) vLLM must serve under LLM_MODEL (--served-model-name in
# cell 5); (b) the guided-decoding wire shape must match what the live vLLM accepts — we PROBE
# before boot and export the matching GUIDED_JSON_FIELD (service reads it per request).
import subprocess, os, time, json
import requests

os.environ["LLM_URL"] = f"http://127.0.0.1:{PORT}/v1"
os.environ["LLM_MODEL"] = model_used  # == vLLM --served-model-name; forwarded by native_stack.sh (v0.6.3)
os.environ.setdefault("GUIDED_DECODING", "1")

print("proxy env:", {k: v for k, v in os.environ.items() if "proxy" in k.lower()} or "(none)")
try:
    m = requests.get(f"http://127.0.0.1:{PORT}/v1/models", timeout=5)
    print("vLLM /v1/models:", m.status_code, m.json().get("data", [{}])[0].get("id") if m.status_code == 200 else m.text[:120])
except Exception as e:
    print("vLLM /v1/models EXC:", repr(e)[:200])

schema = json.load(open("deploy/vllm/guided_answer_schema.json"))
def probe(name, extra):
    body = {"model": os.environ["LLM_MODEL"], "temperature": 0.1, "max_tokens": 64,
            "messages": [{"role": "user", "content": 'Reply with the JSON {"covered": true, "answer": "OK", "citations": []}'}]}
    body.update(extra)
    try:
        r = requests.post(f"http://127.0.0.1:{PORT}/v1/chat/completions", json=body, timeout=120)
        ok = r.status_code == 200
        print(f"probe {name}: {r.status_code}" + ("" if ok else " " + r.text[:180]))
        return ok
    except Exception as e:
        print(f"probe {name}: EXC {repr(e)[:180]}")
        return False

plain_ok        = probe("plain (no guided)", {})
gj_raw_ok       = probe("guided_json=raw-schema", {"guided_json": schema})
so_wrapped_ok   = probe("structured_outputs={json:schema}", {"structured_outputs": {"json": schema}})
so_raw_ok       = probe("structured_outputs=raw-schema", {"structured_outputs": schema})
assert plain_ok, "vLLM chat/completions unreachable — abort before wasting the stack boot"

if so_wrapped_ok:
    os.environ["GUIDED_JSON_FIELD"] = "structured_outputs"   # service wraps under {"json": ...} (v0.6.3)
elif gj_raw_ok:
    os.environ["GUIDED_JSON_FIELD"] = "guided_json"          # legacy raw-schema field
else:
    os.environ["GUIDED_DECODING"] = "0"
    print("!! no guided wire shape accepted by this vLLM -> GUIDED_DECODING=0 (legacy prompt-only)")
print("chosen wire field:", os.environ.get("GUIDED_JSON_FIELD", "(legacy)"),
      "| guided enabled:", os.environ.get("GUIDED_DECODING", "1") not in ("0", "false", "no", "off"))

r = subprocess.run(["bash", "tools/native_stack.sh", "up-prod"], capture_output=True, text=True)
print((r.stdout or r.stderr)[-3000:])

print("== health poll (300s budget) ==")
healthy = {}
for attempt in range(60):
    healthy.clear()
    for port in (8100, 8101, 8102, 8103):
        try:
            resp = requests.get(f"http://127.0.0.1:{port}/health", timeout=2)
            healthy[port] = resp.status_code
        except Exception:
            healthy[port] = "down"
    if all(v == 200 for v in healthy.values()):
        break
    time.sleep(5)
print("health:", healthy)
if not all(v == 200 for v in healthy.values()):
    # self-diagnosing: dump native-stack service log tails into the notebook output
    import glob as _glob
    for lg in sorted(_glob.glob("/tmp/och-native-stack/logs/*")):
        print(f"----- {lg} (tail) -----")
        print("".join(open(lg, errors="replace").readlines()[-30:]))
assert all(v == 200 for v in healthy.values()), "Stack not healthy on 8100-8103 — service log tails printed above."

# generator smoke: must NOT be extractive — a healthy GPU answer has latency >> 10ms and no verbatim dump
q = requests.post("http://127.0.0.1:8101/answer", json={"question": "What is the bridging plan for warfarin before surgery?"}, timeout=180)
print("generator smoke:", q.status_code, str(q.json())[:400])

# unconditional service-log tails: llm_call_failed events land in the kernel log now (v0.6.3)
import glob as _glob
for lg in sorted(_glob.glob("/tmp/och-native-stack/logs/guideline-rag*")):
    print(f"----- {lg} (tail) -----")
    print("".join(open(lg, errors="replace").readlines()[-12:]))
'''

# ---------------------------------------------------------------- cell 7 (gates + summary)
cells[7]["source"] = r'''# CELL 7 — Gates (ORDER MATTERS): prod-stack gates FIRST (eval/eval-full/LIVE/loadtest/audit),
# then unit/node, then test-integration-native LAST (its cleanup `native_stack.sh down` kills
# ALL pid files incl. -prod — lesson from run 4 where it silently tore down the prod stack).
import subprocess, os, json, time
import requests

RAG = "http://127.0.0.1:8101"
GATES = []

def run(name, cmd, timeout=3600):
    print()
    print(f">>> [{name}] {cmd}")
    t0 = time.time()
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    print(r.stdout[-4500:])
    if r.returncode != 0:
        print("STDERR:", r.stderr[-2000:])
    print(f"--- exit: {r.returncode} ({time.time()-t0:.0f}s) ---")
    GATES.append({"name": name, "cmd": cmd, "exit": r.returncode, "seconds": round(time.time() - t0, 1)})
    return r

def ensure_prod_stack():
    down = []
    for port in (8100, 8101, 8102, 8103):
        try:
            if requests.get(f"http://127.0.0.1:{port}/health", timeout=2).status_code != 200:
                down.append(port)
        except Exception:
            down.append(port)
    if not down:
        return True
    print(f"prod stack down on {down} — restarting via native_stack.sh up-prod ...")
    subprocess.run("bash tools/native_stack.sh down", shell=True, capture_output=True, text=True)
    subprocess.run("bash tools/native_stack.sh up-prod", shell=True, capture_output=True, text=True)
    for _ in range(60):
        ok = all(requests.get(f"http://127.0.0.1:{p}/health", timeout=2).status_code == 200
                 for p in (8100, 8101, 8102, 8103))
        if ok:
            print("prod stack restored")
            return True
        time.sleep(5)
    return False

assert ensure_prod_stack(), "prod stack could not be restored — see native stack logs above"

# --- Tier-1 core: prod-stack gates on the LIVE GPU-backed stack ---
run("eval-seed",  f"RAG_URL={RAG} make eval")             # seed eval, full mode (citations checked vs live stack)
run("eval-full",  f"RAG_URL={RAG} make eval-full")        # 208-question eval vs live GPU-backed stack
run("live-strict", f"RAG_URL={RAG} LIVE_MODE=gpu python -m pytest tests/live -m live -v")  # STRICT: trap refusal >=90%, citation validity >=80%, red-team floor
run("loadtest",   "make loadtest LOCUST_USERS=20 LOCUST_RUN_TIME=2m")  # pilot-grade latency ONLY (shared VM)
run("audit-verify", "make audit-verify")                  # hash-chained audit log walk
# --- regression tiers (stack-independent / self-contained) ---
run("test-unit", "make test-unit")                        # pytest unit tier
run("test-node", "make test-node")                        # audit chain, redaction, metrics
# integration tier runs in its DOCUMENTED mock shape (LLM_URL reset to the dead URL) —
# v10 finding: the inherited live LLM_URL leaked into the test stack and broke fail-closed tests
run("test-integration-native", "env LLM_URL=http://localhost:1/v1 make test-integration-native")

base = "/kaggle/working" if os.path.isdir("/kaggle") else "/content"
summary = {"gates": GATES,
           "tier1_live_exit": next((g["exit"] for g in GATES if g["name"] == "live-strict"), None),
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
