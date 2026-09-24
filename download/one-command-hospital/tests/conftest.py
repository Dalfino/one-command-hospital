"""Shared fixtures for the One-Command Hospital test pyramid.

Import strategy: service modules are plain files inside services/<svc>/app/,
so we put their parent dirs on sys.path and import them directly. The unit
tier never imports deid-gate/verifier mains (they pull heavy presidio/medspaCy
deps) — those are exercised by the integration tier against real containers.
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
RAG_DIR = REPO / "services" / "guideline-rag"

# guideline-rag resolves its corpus via GUIDELINES_DIR (a latent container/repo
# path mismatch was fixed by introducing it — see M12). Point it at the real
# corpus for every test run before any service module is imported.
import os
os.environ.setdefault("GUIDELINES_DIR", str(REPO / "guidelines"))

# hardening.py / retrieval.py are dependency-light single files
for p in (str(RAG_DIR / "app"),):
    if p not in sys.path:
        sys.path.insert(0, p)
# rag's app package (for app.main) — relative imports need the parent on path
if str(RAG_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_DIR))
