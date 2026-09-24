"""Integration-tier guard + base URL constants.

Every test here is marked `integration` and requires the docker test stack:
    docker compose -f tests/integration/docker-compose.test.yml up -d --build
If docker is unavailable (e.g. this sandbox), tests SKIP loudly instead of
failing — the tier still runs in CI where docker exists.
"""
import pathlib
import shutil
import subprocess

import pytest

DEID = "http://localhost:8210"
RAG = "http://localhost:8211"
VERIFIER = "http://localhost:8212"
MEDIATOR = "http://localhost:8213"

COMPOSE_FILE = pathlib.Path(__file__).parent / "docker-compose.test.yml"


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True,
                              timeout=20).returncode == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def stack_ready():
    if not _docker_available():
        pytest.skip("docker not available — start the test stack to run the "
                    "integration tier (see tests/integration/docker-compose.test.yml)")
    # cheap liveness probe of the mediator (the last service to come healthy)
    import urllib.request
    try:
        with urllib.request.urlopen(f"{MEDIATOR}/health", timeout=5) as r:
            assert r.status == 200
    except Exception as e:
        pytest.skip(f"test stack not reachable at {MEDIATOR} — run `make test-integration` ({e})")
    return True
