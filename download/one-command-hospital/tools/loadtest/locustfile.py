"""
Load test — the latency SLO is a KILL CRITERIA item (median answer > 8s for a
sustained window = the project gets killed), so load behavior is not optional
knowledge. Run against a live stack:

    make loadtest                     # 20 users ramping over 2 min vs :8103
    LOCUST_USERS=50 make loadtest     # heavier

Scenarios mirror real clinical traffic shape:
  70%  repeat questions (cache-hit path — the "busy ward asking the same thing" wave)
  20%  unique questions (cache-miss path — retrieval + generate)
  10%  health/metrics probes (ops tools)

SLO targets (from docs/deployment_readiness.md — measured, not hoped):
  p50 ask latency  < 2000 ms (mock/extractive; live LLM: see readiness gate)
  p95 ask latency  < 8000 ms
  error rate       < 1% (non-429)
  refusal budget   monitored by alert `RefusalFatigue` (>40% → investigate)
"""
import os
import random

from locust import HttpUser, between, task

MEDIATOR_HOST = os.environ.get("LOCUST_HOST", "http://localhost:8103")

REPEAT_QUESTIONS = [
    "How do I bridge warfarin before surgery?",
    "What INR triggers bridging?",
    "When should sepsis screening be repeated?",
    "What is the insulin correction factor protocol?",
]
UNIQUE_STEMS = [
    "perioperative management",
    "glucose targets",
    "screening criteria",
    "hold time before procedure",
    "resume anticoagulation",
    "lactate threshold",
]


class ClinicianUser(HttpUser):
    host = MEDIATOR_HOST
    wait_time = between(1, 3)

    @task(7)
    def ask_repeat(self):
        """Cache-hit path: the same guideline question asked ward-wide."""
        q = random.choice(REPEAT_QUESTIONS)
        self.client.post("/process", json={"question": q, "userId": "loadtest"},
                         name="/process [repeat]")

    @task(2)
    def ask_unique(self):
        """Cache-miss path: retrieval + generate on fresh phrasing."""
        q = f"{random.choice(UNIQUE_STEMS)} protocol variant {random.randint(1, 10**9)}"
        self.client.post("/process", json={"question": q, "userId": "loadtest"},
                         name="/process [unique]")

    @task(1)
    def health(self):
        self.client.get("/health", name="/health [ops]")


class OpsProbeUser(HttpUser):
    """Background observability traffic (Prometheus-equivalent)."""
    host = MEDIATOR_HOST
    wait_time = between(5, 10)

    @task
    def metrics(self):
        self.client.get("/metrics", name="/metrics [ops]")
