import type { LucideIcon } from "lucide-react";
import {
  BookOpenCheck,
  Boxes,
  ClipboardCheck,
  Container,
  Crosshair,
  FileClock,
  GitBranch,
  Landmark,
  Lock,
  Rocket,
  Scale,
  ScanSearch,
  SearchCheck,
  ServerCog,
  ShieldCheck,
  Stethoscope,
  UserCheck,
  Workflow,
  GraduationCap,
} from "lucide-react";

/* ------------------------------ Repo ------------------------------ */

export const REPO_URL = "https://github.com/Dalfino/one-command-hospital";

/* ------------------------------ Nav ------------------------------ */

export const NAV_LINKS = [
  { label: "How it works", href: "#how" },
  { label: "The combination", href: "#combination" },
  { label: "Improvements", href: "#improvements" },
  { label: "Proof", href: "#proof" },
  { label: "Compliance", href: "#compliance" },
  { label: "Deployment", href: "#deployment" },
  { label: "Roadmap", href: "#roadmap" },
];

/* --------------------------- Hero chips --------------------------- */

export type StatChip = {
  icon: LucideIcon;
  value: string;
  label: string;
  duration: number;
  delay: number;
  offset: string;
};

export const HERO_CHIPS: StatChip[] = [
  { icon: SearchCheck, value: "95%", label: "retrieval on the 208-question eval", duration: 9, delay: 0, offset: "lg:mr-16" },
  { icon: GraduationCap, value: "208", label: "question exam in CI", duration: 12, delay: 0.8, offset: "lg:mr-0" },
  { icon: Lock, value: "0", label: "PHI to the AI", duration: 10, delay: 1.6, offset: "lg:mr-24" },
];

/* ------------------------- How it works --------------------------- */

export type LifecycleStep = {
  id: string;
  num: string;
  name: string;
  desc: string;
  items: string[];
  icon: LucideIcon;
  highlighted?: boolean;
};

export const LIFECYCLE_STEPS: LifecycleStep[] = [
  {
    id: "step-ask",
    num: "Step 1",
    name: "Clinician asks",
    desc: "A protocol question inside the EHR — a SMART on FHIR widget in OpenEMR, with optional note context attached.",
    items: [
      "SMART widget: Vite + React + fhirclient, ask / sign / escalate loop",
      "OpenEMR 7.0.2 sandbox — ONC-certified, native FHIR R4",
      "Only the question and note context leave the chart",
    ],
    icon: Stethoscope,
  },
  {
    id: "step-mediator",
    num: "Step 2",
    name: "OpenHIM bus → AI Mediator",
    desc: "The mediation bus routes the event to a reusable AI Mediator — one contract for every AI service the hospital will ever run.",
    items: [
      "OpenHIM routes clinical events with transaction visibility",
      "One contract: event → de-ID → AI → verify → FHIR writeback",
      "Any future model becomes config, not a new integration",
    ],
    icon: Workflow,
  },
  {
    id: "step-deid",
    num: "Step 3",
    name: "De-ID gate",
    desc: "Presidio + medspaCy scrub every identifier before anything reaches a model. PHI dies here.",
    items: [
      "Presidio patterns + medspaCy clinical rules",
      "Over-redaction is acceptable; under-redaction is alarmed by finding counts",
      "From this hop onward, no identifier exists in the pipeline",
    ],
    icon: ShieldCheck,
    highlighted: true,
  },
  {
    id: "step-rag",
    num: "Step 4",
    name: "Guideline RAG",
    desc: "BM25 (+ optional SBERT channel) retrieves the top guideline sections; BioMistral-7B on vLLM answers only from them, citations forced.",
    items: [
      "Hybrid retrieval: BM25 + optional SBERT vector channel",
      "BioMistral-7B served on-prem by vLLM (OpenAI-compatible)",
      "Citations like [ANTICOAG-BRIDGE §3], stamped with the edition",
      "Low retrieval confidence → NOT_COVERED before the LLM is even called",
    ],
    icon: BookOpenCheck,
  },
  {
    id: "step-verifier",
    num: "Step 5",
    name: "Verifier",
    desc: "medspaCy ConText runs after generation: citation validity, negation polarity, entity grounding between answer and source.",
    items: [
      "ConText negation / polarity checks (verifier v0.2)",
      "Lexical grounding scored — below threshold, the answer is flagged",
      "grounded:false routes to a human-review banner, never silently trusted",
    ],
    icon: ScanSearch,
  },
  {
    id: "step-fhir",
    num: "Step 6",
    name: "FHIR writeback",
    desc: "The answer lands back in the chart as a FHIR Communication with full provenance — sources, edition, model, latency.",
    items: [
      "Communication resource written to the Medplum FHIR spine",
      "Provenance: sources, edition, model + version, latency",
      "human_action: pending_review until a clinician acts",
    ],
    icon: ServerCog,
  },
  {
    id: "step-human",
    num: "Step 7",
    name: "Human closes the loop",
    desc: "Sign or escalate inside the widget — the audit loop ends with a person in it. Always.",
    items: [
      "Sign-off or escalation updates the audit event",
      "Append-only log: question, sources, edition, response, action",
      "Advisory-only: the system never writes orders",
    ],
    icon: UserCheck,
  },
];

export const HOW_NON_NEGOTIABLES =
  "De-ID before LLM contact · hard refusal when confidence is low · advisory-only, a human always acts · append-only audit on every answer";

/* ------------------------- Six improvements ----------------------- */

export type Improvement = {
  name: string;
  icon: LucideIcon;
  upstream: string;
  ours: string;
  verify: string;
};

export const IMPROVEMENTS: Improvement[] = [
  {
    name: "Citation-forced RAG + hard refusal",
    icon: BookOpenCheck,
    upstream:
      "BioMistral-7B answers freely and hallucinates confidently — no grounding, no clinical safety alignment.",
    ours: "Answers come only from retrieved sections, must cite inline as [CORPUS §N], and low retrieval confidence returns NOT_COVERED before the LLM is even called.",
    verify: "10 refusal traps must refuse · CI gate fails the build under 80% retrieval",
  },
  {
    name: "Guideline edition control",
    icon: GitBranch,
    upstream:
      "The Meditron corpus is pretraining fuel — flattened, versionless, history-less.",
    ours: "guidelines/manifest.yaml gives every document an id, edition, and effective/expiry dates. Every answer is edition-stamped; stale editions refuse or warn.",
    verify: "Bump an edition in the manifest → the stamp changes on the next answer",
  },
  {
    name: "NLP as the verifier",
    icon: ScanSearch,
    upstream: "medspaCy / scispaCy are positioned as preprocessing and extraction tools.",
    ours: "They run after generation: citation validity, ConText negation polarity, and entity grounding between the answer and its cited source. Preprocessing tech becomes the safety net.",
    verify: "POST /verify flags forged citations and unsupported negations",
  },
  {
    name: "The AI Mediator pattern",
    icon: Workflow,
    upstream:
      "OpenHIM mediators are hand-rolled per integration; nothing reusable ties hospital events to AI outputs with provenance.",
    ours: "One contract: event → de-ID → AI → verify → FHIR Communication with provenance + human_action. Any future model becomes a config of the same contract.",
    verify: "Phase 2 swaps in MedGemma with zero contract changes — the swap IS the test",
  },
  {
    name: "Known-answer eval in CI",
    icon: ClipboardCheck,
    upstream: "Synthea covers fake patients; nobody grades a guideline knowledge base end-to-end.",
    ours: "208 questions — 153 traced to corpus + section, 55 refusal traps — scored for retrieval, citation validity, and refusal correctness. Seed set holds 98%; full set holds 95%. Under 80%, the build fails.",
    verify: "make eval → eval/report.md · runs offline, no GPU needed",
  },
  {
    name: "One-command assembly",
    icon: Rocket,
    upstream: "Every repo documents itself alone; combined deployment is where hospital AI projects die.",
    ours: "One compose file, three profiles (gpu / patients / conformance), a coherent port block, and Makefile verbs that read like the story: up, patients, eval.",
    verify: "Fresh machine → make up → nine services reachable in ~20 min (image pulls aside)",
  },
];

/* ------------------------- The combination ------------------------ */

export type Disposition = "Deploy" | "Harvest" | "Component" | "Conformance CI" | "Planned · Phase 2";

export type CombinationRepo = {
  name: string;
  origin: string;
  license: string;
  disposition: Disposition;
  use: string;
};

export const COMBINATION: CombinationRepo[] = [
  {
    name: "BioMistral-7B",
    origin: "EU consortium",
    license: "Apache-2.0",
    disposition: "Deploy",
    use: "The text engine. PubMed Central–pretrained 7B served on-prem by vLLM; answers only from retrieved guideline sections.",
  },
  {
    name: "Meditron corpus",
    origin: "EPFL",
    license: "Llama-2 community terms",
    disposition: "Harvest",
    use: "Harvested, not deployed: the clinical-guidelines corpus is our knowledge-base blueprint — section structure, editions, numbering — not the model.",
  },
  {
    name: "medspaCy + scispaCy",
    origin: "JHU · Vanderbilt · Allen AI",
    license: "MIT / Apache-2.0",
    disposition: "Component",
    use: "The safety verifier: ConText negation polarity, entity linking, and grounding checks run after generation.",
  },
  {
    name: "Presidio",
    origin: "Microsoft",
    license: "MIT",
    disposition: "Component",
    use: "The de-ID gate: pattern + context scrubbing of identifiers before any text reaches an LLM. PHI dies here.",
  },
  {
    name: "Medplum",
    origin: "Medplum",
    license: "Apache-2.0",
    disposition: "Deploy",
    use: "The FHIR spine our app lives in: auth, Bots, SMART launch, and the Communication resources answers write back to.",
  },
  {
    name: "OpenEMR",
    origin: "OpenEMR community",
    license: "GPL",
    disposition: "Deploy",
    use: "The sandbox EHR: ONC-certified, native FHIR R4 — the clinician's front door and the SMART launch context.",
  },
  {
    name: "OpenHIM",
    origin: "Jembi",
    license: "MPL-2.0",
    disposition: "Deploy",
    use: "The mediation bus: routes every clinical event through the AI Mediator with full transaction visibility.",
  },
  {
    name: "Synthea",
    origin: "Synthea community",
    license: "Apache-2.0",
    disposition: "Deploy",
    use: "Synthetic patients: fills the hospital with realistic fake data, so nothing real is ever at risk.",
  },
  {
    name: "HAPI FHIR",
    origin: "Smile CDR / HAPI",
    license: "Apache-2.0",
    disposition: "Conformance CI",
    use: "The referee, not a runtime dependency: validates the shape of every resource we write, in CI.",
  },
  {
    name: "MedGemma",
    origin: "Google",
    license: "Gemma Terms of Use",
    disposition: "Planned · Phase 2",
    use: "Imaging pre-read behind the same mediator contract — the test that any model is config. Gemma terms pass to derivatives; tracked as an open item.",
  },
];

export const COMBINATION_FOOTNOTE =
  "License note: upstream components keep their licenses — OpenEMR (GPL), Medplum / Synthea / HAPI / BioMistral (Apache-2.0), OpenHIM (MPL-2.0), Presidio / medspaCy (MIT), scispaCy (Apache-2.0). The Meditron corpus is used under Llama-2 community terms for research; MedGemma (Phase 2) carries Gemma use restrictions that pass to derivatives. Verify before any commercial use.";

/* ------------------------------ Proof ----------------------------- */

export type ProofMetric = {
  to: number;
  suffix: string;
  label: string;
  sub: string;
};

export const PROOF_METRICS: ProofMetric[] = [
  { to: 208, suffix: "", label: "questions in the exam", sub: "153 traced + 55 refusal traps; hand-written seed kept verbatim" },
  { to: 95, suffix: "%", label: "retrieval on the full exam", sub: "146 of 153 traced items; seed set holds 98%" },
  { to: 55, suffix: "", label: "refusal traps", sub: "out-of-scope questions must return NOT_COVERED" },
  { to: 80, suffix: "%", label: "CI floor", sub: "retrieval below this fails the build" },
];

export const GRADED_ON = ["Retrieval hit rate", "Citation validity", "Refusal correctness"];

export type KillCriterion = {
  title: string;
  desc: string;
  icon: LucideIcon;
};

export const KILL_CRITERIA: KillCriterion[] = [
  {
    title: "Grounded answers < 85%",
    desc: "On the 200-question eval at Phase 1 exit — below the floor, the pilot stops.",
    icon: Crosshair,
  },
  {
    title: "Any PHI downstream of de-ID",
    desc: "One strike: root-cause it, fix it, re-certify the gate before anything restarts.",
    icon: Lock,
  },
  {
    title: "Median latency > 8 s",
    desc: "At steady state, after two optimisation passes — then we stop and rethink.",
    icon: FileClock,
  },
  {
    title: "Clinician trust < 80%",
    desc: "More than 20% “would not use” after four weeks ends the pilot.",
    icon: UserCheck,
  },
];

/* --------------------------- Compliance --------------------------- */

export type ComplianceItem = { text: string; done: boolean };

export type ComplianceTab = {
  id: string;
  label: string;
  icon: LucideIcon;
  intro: string;
  items: ComplianceItem[];
};

export const COMPLIANCE_TABS: ComplianceTab[] = [
  {
    id: "hipaa",
    label: "HIPAA & Privacy",
    icon: ShieldCheck,
    intro:
      "Framework: a zero-PHI architecture by construction — self-hosted weights, on-prem GPU, and de-identification before any model contact. Green checks are built; dashed circles are open discussion points we won't pretend are closed.",
    items: [
      {
        text: "De-ID gate (Presidio + medspaCy) scrubs identifiers before any LLM contact — the model never sees them.",
        done: true,
      },
      {
        text: "Self-hosted open weights on your own GPU — inference needs no vendor BAA route.",
        done: true,
      },
      {
        text: "OPEN ITEM — de-ID recall certification: >95% recall is the upstream target; certification on our corpus plus sampling QA is an open discussion point.",
        done: false,
      },
      {
        text: "Append-only audit log: question, sources, edition, model + version, response, human action.",
        done: true,
      },
      {
        text: "OPEN ITEM — DPIA for any real-patient extension: not started; today the hospital runs on Synthea synthetic data only.",
        done: false,
      },
      {
        text: "Bias to over-redaction: under-redaction is alarmed by finding counts at the gate.",
        done: true,
      },
    ],
  },
  {
    id: "euai",
    label: "EU AI Act",
    icon: Scale,
    intro:
      "Framework: human oversight, logging, and traceability are design features, not retrofit. The honest position on classification and timing: open items, not settled facts — the Act's core obligations bite from August 2026.",
    items: [
      {
        text: "Human oversight by design — sign/escalate closes every loop; no autonomous actions.",
        done: true,
      },
      {
        text: "Logging & traceability — every answer carries provenance in an append-only audit trail.",
        done: true,
      },
      {
        text: "Data governance — synthetic corpus only today: Synthea patients + authored seed protocols.",
        done: true,
      },
      {
        text: "OPEN ITEM — conformity assessment timeline: whether CDS assistance lands in Annex III high-risk is an open legal question; tracked, not assumed.",
        done: false,
      },
      {
        text: "OPEN ITEM — technical documentation pack per release: the raw material exists (eval reports, architecture docs); the formal pack is not yet assembled.",
        done: false,
      },
      {
        text: "OPEN ITEM — intended-purpose statement per deployment context, written per hospital before go-live.",
        done: false,
      },
    ],
  },
  {
    id: "fda",
    label: "FDA / SaMD",
    icon: ClipboardCheck,
    intro:
      "Framework: an advisory-only, citation-forced, human-signed assistant is designed to sit outside the device definition. The formal boundary analysis that proves it per deployment is the open item.",
    items: [
      {
        text: "Advisory-only outputs — the system never writes orders; a human always acts.",
        done: true,
      },
      {
        text: "Refusal-first — no source, no answer; NOT_COVERED is the default failure mode.",
        done: true,
      },
      {
        text: "OPEN ITEM — formal boundary analysis (21st Century Cures) per deployment: working assumption documented, formal assessment open.",
        done: false,
      },
      {
        text: "OPEN ITEM — PCCP posture for model updates (FDA final guidance, Dec 2024): planned before any US clinical pilot.",
        done: false,
      },
      {
        text: "Eval-gated releases — the known-answer exam fails the build under 80% retrieval; nothing ships unexamined.",
        done: true,
      },
      {
        text: "OPEN ITEM — pre-registered clinical evaluation protocol, required before Phase 1 exit claims.",
        done: false,
      },
    ],
  },
  {
    id: "gov",
    label: "Governance",
    icon: Landmark,
    intro:
      "Framework: kill criteria are written down before go-live — the failure story is part of the design. What's open: the standing committee and cadence a live hospital deployment would need.",
    items: [
      {
        text: "Kill criteria defined in docs/architecture.md — grounded-rate floor, PHI one-strike, latency ceiling, trust floor.",
        done: true,
      },
      {
        text: "Append-only audit trail with per-answer provenance; gaps are themselves audit findings.",
        done: true,
      },
      {
        text: "The eval harness as a governance instrument — retrieval, citation validity, refusal correctness, graded in CI.",
        done: true,
      },
      {
        text: "OPEN ITEM — standing AI governance committee (clinical validation, data governance, MLOps): structure drafted, not constituted.",
        done: false,
      },
      {
        text: "OPEN ITEM — monthly drift review cadence: designed; starts when a live pilot does.",
        done: false,
      },
      {
        text: "OPEN ITEM — incident-response runbook rehearsal: kill-switch procedure written, not yet drilled.",
        done: false,
      },
    ],
  },
];

/* --------------------------- Deployment --------------------------- */

export type MakeVerb = { verb: string; desc: string };

export const MAKE_VERBS: MakeVerb[] = [
  { verb: "up", desc: "core stack — EHR, spine, bus, AI services" },
  { verb: "up-gpu", desc: "core + vLLM serving BioMistral-7B" },
  { verb: "patients", desc: "generate a Synthea population" },
  { verb: "conformance", desc: "start HAPI FHIR for resource checks" },
  { verb: "eval", desc: "run the known-answer exam → eval/report.md" },
  { verb: "down", desc: "stop everything" },
];

export const COMPOSE_PROFILES = ["gpu", "patients", "conformance"];

export type PortRow = { service: string; port: string };

export const PORT_ROWS: PortRow[] = [
  { service: "OpenEMR — sandbox EHR (setup wizard on first boot)", port: ":8300" },
  { service: "Medplum — FHIR spine / API", port: ":8080" },
  { service: "OpenHIM console — mediation bus admin", port: ":9000" },
  { service: "deid-gate / guideline-rag / verifier / ai-mediator", port: ":8100–:8103" },
  { service: "vLLM — OpenAI-compatible (profile: gpu)", port: ":8104" },
  { service: "HAPI FHIR — conformance (profile: conformance)", port: ":8105" },
];

export type DeployFact = { icon: LucideIcon; title: string; big: string; desc: string };

export const DEPLOY_FACTS: DeployFact[] = [
  {
    icon: Container,
    title: "GPU footprint",
    big: "1× ≥24GB GPU",
    desc: "Runs BioMistral-7B fp16 on vLLM. Eval-only mode and the core stack need no GPU at all.",
  },
  {
    icon: Lock,
    title: "Network",
    big: "Air-gapped OK",
    desc: "Images and weights are pulled once into a local cache volume; after that the hospital runs with zero internet egress.",
  },
  {
    icon: Boxes,
    title: "Time to boot",
    big: "~20 minutes",
    desc: "From make up to nine reachable services on a fresh machine (image pulls aside). Pilot-stage estimate — counted honestly.",
  },
];

/* ----------------------------- Roadmap ---------------------------- */

export type PhaseStatus = "done" | "active" | "planned";

export type Phase = {
  phase: string;
  title: string;
  timeframe: string;
  status: PhaseStatus;
  statusLabel: string;
  bullets: { text: string; done?: boolean }[];
  gate: string;
};

export const PHASES: Phase[] = [
  {
    phase: "Phase 0",
    title: "Assemble & prove",
    timeframe: "Complete",
    status: "done",
    statusLabel: "Done",
    bullets: [
      { text: "One compose file: 10 upstream services + 3 optional profiles", done: true },
      { text: "Seed knowledge base: 3 synthetic protocols + edition manifest", done: true },
      { text: "Eval harness green: 98% retrieval, CI-gated", done: true },
    ],
    gate: "Gate passed: stack up, exam green",
  },
  {
    phase: "Phase 1",
    title: "Harden the loop",
    timeframe: "4–6 weeks",
    status: "active",
    statusLabel: "In progress",
    bullets: [
      { text: "SMART on FHIR widget in OpenEMR — built, vite build green", done: true },
      { text: "Medplum Bot JWT auth — replaces v0 naive auth", done: true },
      { text: "medspaCy ConText verifier — polarity/negation v0.2 shipped", done: true },
      { text: "Hybrid retrieval — BM25 + optional SBERT channel", done: true },
      { text: "Eval set grows 52 → 208 questions (95% full / 98% seed)", done: true },
      { text: "Hardening wave: audit chain, observability, CI, readiness gate", done: true },
    ],
    gate: "Gate: ≥85% grounded in live mode (needs GPU run) ⬜",
  },
  {
    phase: "Phase 2",
    title: "Teach it to see",
    timeframe: "Next",
    status: "planned",
    statusLabel: "Planned",
    bullets: [
      { text: "Orthanc + OHIF imaging layer in the sandbox" },
      { text: "MedGemma imaging pre-read behind the same mediator contract" },
      { text: "The swap itself tests the “any model is config” claim" },
    ],
    gate: "Gate: pre-read runs through the unmodified mediator contract",
  },
  {
    phase: "Phase 3",
    title: "Prove at scale",
    timeframe: "Later",
    status: "planned",
    statusLabel: "Planned",
    bullets: [
      { text: "MIMIC-code validation pathway" },
      { text: "Federated testbed on Synthea-simulated hospitals" },
      { text: "OpenICE device layer" },
    ],
    gate: "Gate: multi-site reproducibility",
  },
];

/* ------------------------------ Risks ----------------------------- */

export type RiskLevel = "Low" | "Med" | "High" | "Critical";

export type Risk = {
  risk: string;
  likelihood: RiskLevel;
  impact: RiskLevel;
  mitigation: string;
};

export const RISKS: Risk[] = [
  {
    risk: "Refusal rate too high — clinicians get annoyed, workarounds return",
    likelihood: "Med",
    impact: "High",
    mitigation:
      "Confidence-threshold tuning, refusal telemetry, and an extractive fallback with citations before a hard NOT_COVERED",
  },
  {
    risk: "Retrieval drift as the corpus grows",
    likelihood: "Med",
    impact: "Med",
    mitigation:
      "Known-answer exam re-run in CI on every change; hybrid BM25 + SBERT; manifest review per edition",
  },
  {
    risk: "Guideline staleness — an expired edition gets answered",
    likelihood: "Med",
    impact: "High",
    mitigation:
      "Manifest expiry dates, edition-stamped answers, refuse-or-warn on stale editions",
  },
  {
    risk: "PHI found downstream of the de-ID gate",
    likelihood: "Low",
    impact: "Critical",
    mitigation:
      "One-strike kill criterion: stop, root-cause, re-certify the gate; finding-count alarms + sampling QA",
  },
  {
    risk: "Hallucination reaches the chart",
    likelihood: "Med",
    impact: "High",
    mitigation:
      "Citation-forced prompts, ConText grounding check, human sign-off — ungrounded answers are flagged, never trusted",
  },
  {
    risk: "Median latency drifts past 8 s",
    likelihood: "Med",
    impact: "Med",
    mitigation:
      "Latency is a kill criterion — two optimisation passes budgeted, then the approach is revisited",
  },
  {
    risk: "Clinician trust erodes after go-live",
    likelihood: "Med",
    impact: "High",
    mitigation:
      "Trust survey at four weeks is a kill criterion; visible citations and honest refusals are the trust strategy",
  },
  {
    risk: "Upstream license terms change",
    likelihood: "Low",
    impact: "High",
    mitigation:
      "License-neutral mediator contract, pinned weights, Meditron corpus research-use tracked in the open-items list",
  },
];

/* ----------------------------- Footer ----------------------------- */

export const BUILT_ON =
  "Built openly on OpenEMR · Medplum · OpenHIM · Presidio · BioMistral-7B · medspaCy · scispaCy · Synthea · HAPI FHIR";

export const DISCLAIMER =
  "An advisory-only assistant: it never diagnoses or prescribes. Every output requires clinician review, and the seed protocols are synthetic — for testing, never medical advice.";

export const FOOTER_COPY = "© 2026 One-Command Hospital — a Willow Lab research build.";
