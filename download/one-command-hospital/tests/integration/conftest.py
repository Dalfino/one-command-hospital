"""Integration-tier guard + base URL constants.

Every test here is marked `integration` and expects the four AI services to be
reachable at the TEST_PORTS below. Two supported ways to get there:

1. Docker (default, what CI does):
    docker compose -f tests/integration/docker-compose.test.yml up -d --build

2. Native processes (no docker — dev laptops, sandboxes, evidence runs):
    bash tools/native_stack.sh up-test
   The tier is deliberately stack-agnostic: whichever stack answers at the
   test ports is the stack under test. If nothing answers and docker can't
   bootstrap one, tests SKIP loudly instead of failing.
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

# Native mode: tools/native_stack.sh writes PID files here. The fail-closed
# test SIGSTOPs/SIGCONTs the verifier through them when docker is absent.
RUN_DIR = pathlib.Path("/tmp/och-native-stack")


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True,
                              timeout=20).returncode == 0
    except Exception:
        return False


def _mediator_alive() -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(f"{MEDIATOR}/health", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def stack_ready():
    """Probe-first: an already-running stack wins (docker or native); docker
    is only the default bootstrapper, never a hard requirement."""
    if not _mediator_alive() and _docker_available():
        subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE),
                        "up", "-d", "--build"], timeout=600)
    if not _mediator_alive():
        pytest.skip("no integration stack reachable at "
                    f"{MEDIATOR} — `bash tools/native_stack.sh up-test` or "
                    "`make test-integration`")
    # the four services must ALL answer before the tier starts
    import urllib.request
    for url in (f"{DEID}/health", f"{RAG}/health",
                f"{VERIFIER}/health", f"{MEDIATOR}/health"):
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                assert r.status == 200
        except Exception as e:
            pytest.skip(f"integration stack incomplete ({url} -> {e})")
    return True
