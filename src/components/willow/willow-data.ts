import type { LucideIcon } from "lucide-react";
import {
  Activity,
  BookOpenCheck,
  BrainCircuit,
  ClipboardCheck,
  Container,
  DatabaseBackup,
  FileText,
  Gauge,
  Landmark,
  MonitorSmartphone,
  Newspaper,
  PlugZap,
  Scale,
  ShieldCheck,
  Server,
  Split,
  Stethoscope,
} from "lucide-react";

/* ------------------------------ Nav ------------------------------ */

export const NAV_LINKS = [
  { label: "Platform", href: "#platform" },
  { label: "Products", href: "#products" },
  { label: "Sources", href: "#sources" },
  { label: "Compliance", href: "#compliance" },
  { label: "Deployment", href: "#deployment" },
  { label: "ROI", href: "#roi" },
  { label: "Roadmap", href: "#roadmap" },
];

/* --------------------------- Platform ---------------------------- */

export type PlatformLayer = {
  id: string;
  num: string;
  name: string;
  desc: string;
  items: string[];
  icon: LucideIcon;
  highlighted?: boolean;
};

export const PLATFORM_LAYERS: PlatformLayer[] = [
  {
    id: "layer-4",
    num: "Layer 4",
    name: "Experience",
    desc: "Clinician-facing apps embedded in the EHR workflow",
    items: ["Willow Writer", "Willow Sage", "Willow Charts", "Willow Pulse", "Willow Triage"],
    icon: MonitorSmartphone,
  },
  {
    id: "layer-3",
    num: "Layer 3",
    name: "Data & Integration",
    desc: "Everything speaks FHIR — nothing leaves the zones",
    items: [
      "HL7 FHIR R4 gateway",
      "SMART on FHIR embedding",
      "Event bus (ADT / discharge triggers)",
      "Synthetic-data test harness (Synthea)",
    ],
    icon: PlugZap,
  },
  {
    id: "layer-2",
    num: "Layer 2",
    name: "Intelligence",
    desc: "The open model fleet, served and routed",
    items: [
      "vLLM serving pool",
      "Model router",
      "Fine-tuned MedGemma 4B/27B",
      "BioMistral-7B + RAG",
      "Clinical-Longformer / T5 encoders",
      "BioGPT miner",
      "4-bit quantization",
    ],
    icon: BrainCircuit,
  },
  {
    id: "layer-1",
    num: "Layer 1",
    name: "Trust Fabric",
    desc: "Governance wrapping every model call — always on",
    items: [
      "De-identification gate",
      "Guardrails & citation grounding",
      "Human-in-the-loop review",
      "Audit trail & model registry",
      "Drift monitoring",
      "Governance console",
    ],
    icon: ShieldCheck,
    highlighted: true,
  },
];

/* --------------------------- Products ---------------------------- */

export type Product = {
  name: string;
  icon: LucideIcon;
  promise: string;
  builtFrom: string[];
  bullets: string[];
  kpi: string;
};

export const PRODUCTS: Product[] = [
  {
    name: "Willow Writer",
    icon: FileText,
    promise:
      "Discharge summaries and after-visit notes drafted from chart context — clinicians edit, AI never auto-signs.",
    builtFrom: ["MedGemma", "medspaCy"],
    bullets: [
      "Drafts structured summaries from FHIR chart context in seconds",
      "ConText-aware: negation and family history handled correctly",
      "Every draft gated by clinician review before it reaches the chart",
    ],
    kpi: "≤90s draft · 20–30% time saved",
  },
  {
    name: "Willow Sage",
    icon: BookOpenCheck,
    promise:
      "Guideline-grounded answers with citation links to local protocols — NICE, WHO, and institutional policies.",
    builtFrom: ["BioMistral", "RAG"],
    bullets: [
      "Retrieval over the hospital's own guideline library",
      "Every claim links to a source paragraph",
      "Refuses to answer beyond grounded evidence",
    ],
    kpi: "100% citation-grounded answers",
  },
  {
    name: "Willow Charts",
    icon: Activity,
    promise:
      "Note intelligence that reads the chart like a specialist — extracting what matters and flagging what hides.",
    builtFrom: ["scispaCy", "medspaCy", "Clinical-Longformer", "Clinical-T5"],
    bullets: [
      "Extracts LVEF, NYHA class, and medications from free text",
      "Readmission & sepsis risk flags from note signals",
      "Silent-mode validated before any alert fires",
    ],
    kpi: "Silent-mode validated before alerting",
  },
  {
    name: "Willow Pulse",
    icon: Newspaper,
    promise: "A daily research digest matched to your department's interests — not a firehose.",
    builtFrom: ["BioGPT"],
    bullets: [
      "Daily PubMed/MEDLINE sweep ranked by relevance",
      "Relation mining surfaces drug–disease–gene links",
      "One page per department, every morning",
    ],
    kpi: "Daily · relevance-ranked",
  },
  {
    name: "Willow Triage",
    icon: Stethoscope,
    promise:
      "Structured pre-consultation symptom triage for telehealth — with a human always in the loop.",
    builtFrom: ["OpenBioLLM"],
    bullets: [
      "Structured symptom intake, not free-text guesswork",
      "Escalation rules wired to nursing protocols",
      "RN review gate before any urgency assignment",
    ],
    kpi: "No autonomous decisions — RN review gate",
  },
  {
    name: "Willow Sentinel",
    icon: ShieldCheck,
    promise:
      "The compliance console — every model call observed, logged, and governable from one place.",
    builtFrom: ["All models", "Philter-class de-ID"],
    bullets: [
      "PHI audit trail across every product",
      "Model registry with version pinning & sign-off",
      "Drift dashboards and incident-response tooling",
    ],
    kpi: "Every model call logged",
  },
];

/* ------------------------- Source projects ----------------------- */

export type SourceProject = {
  name: string;
  origin: string;
  license: string;
  keep: string;
  add: string;
};

export const SOURCES: SourceProject[] = [
  {
    name: "MedGemma 1.5 4B / 27B",
    origin: "Google",
    license: "Gemma Terms of Use",
    keep: "Multimodal medical vision–language engine; +5% MedQA and +22% EHRQA over v1.",
    add: "Fine-tuned on hospital discharge summaries, outcome-evaluated against clinician edits.",
  },
  {
    name: "BioMistral-7B",
    origin: "EU consortium",
    license: "Apache-2.0",
    keep: "PubMed Central–pretrained medical reasoning; EU-hostable weights.",
    add: "Citation-grounded RAG over local guidelines, plus output guardrails.",
  },
  {
    name: "Meditron 7B / 70B",
    origin: "EPFL",
    license: "Llama-2 Community",
    keep: "Corpus trained on WHO / NHS clinical guidelines.",
    add: "\u201cFully Open Meditron\u201d audited pipeline for transparent, institution-specific tuning.",
  },
  {
    name: "BioGPT",
    origin: "Microsoft",
    license: "MIT",
    keep: "Relation extraction & biomedical QA strengths — 78.2% PubMedQA.",
    add: "Department-specific evidence digest agent behind Willow Pulse.",
  },
  {
    name: "medspaCy",
    origin: "Johns Hopkins · Vanderbilt · NIH",
    license: "MIT",
    keep: "ConText engine: negation, family history, temporality.",
    add: "Institutional ICD-10 / SNOMED coding dictionaries.",
  },
  {
    name: "scispaCy",
    origin: "Allen Institute for AI",
    license: "Apache-2.0",
    keep: "UMLS / MeSH / RxNorm entity linking.",
    add: "Cardiology NER fine-tune: LVEF, NYHA class, medications.",
  },
  {
    name: "OpenBioLLM-8B",
    origin: "Saama · aaditya",
    license: "Llama-3 Community",
    keep: "GPT-4-class medical QA at 8B — 72.5% avg across 9 benchmarks.",
    add: "Multi-agent guardrails and the escalation front-end for Willow Triage.",
  },
  {
    name: "Clinical-Longformer / Clinical-T5",
    origin: "Stanford AIMI",
    license: "PhysioNet-credentialed",
    keep: "4,096-token long-note encoders pretrained on MIMIC-III/IV.",
    add: "Readmission & sepsis prediction heads validated in silent mode.",
  },
];

export const SOURCES_FOOTNOTE =
  "License note: Llama-2/3 Community Licenses are compatible with hospital use below the 700M monthly-active-user threshold. Gemma Terms of Use carry use restrictions that pass to derivatives — tracked as a compliance item below.";

/* --------------------------- Compliance -------------------------- */

export type ComplianceTab = {
  id: string;
  label: string;
  icon: LucideIcon;
  intro: string;
  items: string[];
};

export const COMPLIANCE_TABS: ComplianceTab[] = [
  {
    id: "hipaa",
    label: "HIPAA & Privacy",
    icon: ShieldCheck,
    intro:
      "PHI never reaches a model un-sanctioned. Willow standardizes on self-hosted open weights and on-prem GPUs, with a de-identification gate in front of every call.",
    items: [
      "Four sanctioned PHI × LLM routes mapped — BAA-covered cloud, dedicated capacity, self-hosted open weights, on-prem GPUs. Willow runs the last two.",
      "De-identification gate screens all 18 HIPAA Safe Harbor identifiers before any text reaches a model.",
      "Philter-class open-source de-ID targeting >95% recall on clinical notes.",
      "Human sampling QA — random note samples re-reviewed weekly to verify gate performance.",
      "Egress allow-list: no PHI can leave the model zone toward non-sanctioned endpoints.",
      "Data-use agreements signed for every corpus the models touch.",
    ],
  },
  {
    id: "euai",
    label: "EU AI Act",
    icon: Scale,
    intro:
      "AI in medical devices is high-risk under Annex III, and the Act's core obligations bite from August 2026. Willow treats conformity as a documentation problem solved in advance.",
    items: [
      "High-risk classification acknowledged — Annex III covers AI systems in medical devices.",
      "Core obligations tracked: conformity assessment, technical documentation, human oversight, logging, data governance.",
      "A documentation pack ships per product: intended purpose, risk file, evaluation results.",
      "Human oversight by design — clinician sign-off is a product feature, not an afterthought.",
      "Traceability: every model call lands in the immutable audit trail.",
      "Data governance documented for fine-tune corpora (Synthea synthetic + licensed data).",
    ],
  },
  {
    id: "fda",
    label: "FDA / SaMD",
    icon: ClipboardCheck,
    intro:
      "Not everything here is a device — and pretending otherwise slows care. Willow runs a boundary analysis per product and deploys prediction features silent-first.",
    items: [
      "Boundary analysis per product: documentation assistance and admin tooling fall outside the device definition.",
      "Risk-prediction flags (readmission, sepsis) may cross into SaMD — governed accordingly until cleared.",
      "PCCP strategy per FDA's final guidance (Dec 2024) for planned model updates.",
      "Silent-mode-first: predictions are logged and evaluated before any clinician-facing alert.",
      "Precedent map maintained — 1,016 AI-enabled devices authorized through 2024.",
      "Clinical evaluation protocols pre-registered with the review board.",
    ],
  },
  {
    id: "gov",
    label: "Governance",
    icon: Landmark,
    intro:
      "A standing AI steering committee owns the lifecycle — with subgroups for clinical validation, data governance, and MLOps — and every product carries explicit kill criteria.",
    items: [
      "AI steering committee with clinical validation, data governance, and MLOps subgroups.",
      "Immutable audit trail and model registry — version pinning with named sign-off.",
      "Incident-response runbook with per-product kill criteria defined before go-live.",
      "Monthly drift review: input/output distributions plus re-run of the evaluation suite.",
      "Quarterly governance report delivered to clinical leadership.",
      "Shadow-use control: SSO-gated apps only, plus governance training for staff.",
    ],
  },
];

/* --------------------------- Deployment -------------------------- */

export type StackItem = { icon: LucideIcon; title: string; desc: string };

export const REFERENCE_STACK: StackItem[] = [
  {
    icon: Server,
    title: "vLLM serving pool",
    desc: "PagedAttention batching across 7B–27B weights, 4-bit quantized where latency allows.",
  },
  {
    icon: Split,
    title: "Model router",
    desc: "Routes by task: encoders for extraction, 7B for Q&A, MedGemma for multimodal.",
  },
  {
    icon: Container,
    title: "Kubernetes runtime",
    desc: "GPU scheduling, autoscaling, and pinned containers for reproducibility.",
  },
  {
    icon: ShieldCheck,
    title: "Security zones",
    desc: "DMZ, app, data, and model zones — PHI only ever lives inside the data zone.",
  },
  {
    icon: Gauge,
    title: "Monitoring & drift detection",
    desc: "Input/output drift, latency, and evaluation-suite dashboards.",
  },
  {
    icon: DatabaseBackup,
    title: "Backup & DR",
    desc: "Nightly weight + config snapshots; documented RTO/RPO per zone.",
  },
];

export type GpuRow = { workload: string; gpu: string; throughput: string };

export const GPU_ROWS: GpuRow[] = [
  {
    workload: "7B chat — BioMistral / OpenBioLLM",
    gpu: "1× 24GB — L40S / RTX 4090 / A10",
    throughput: "~120 tok/s",
  },
  {
    workload: "27B multimodal — MedGemma 27B",
    gpu: "1× 48GB (A6000 / L40S-48) or 2× 24GB",
    throughput: "~40 tok/s",
  },
  {
    workload: "70B — optional Meditron-70B",
    gpu: "2–4× 80GB — A100 / H100",
    throughput: "4-bit quantized",
  },
  {
    workload: "Encoder fleet — Longformer / T5",
    gpu: "CPU, or 1× 16GB GPU",
    throughput: "Batch, offline",
  },
];

export type Scenario = { beds: string; gpus: string; capex: string; desc: string };

export const SCENARIOS: Scenario[] = [
  {
    beds: "200-bed hospital",
    gpus: "2× L40S",
    capex: "~$60–80k capex",
    desc: "Writer + Sage for one or two service lines; encoders run on CPU.",
  },
  {
    beds: "500-bed hospital",
    gpus: "4× L40S + 1× A100",
    capex: "All six products",
    desc: "Room for MedGemma-27B plus a quantized 70B when guidelines demand it.",
  },
  {
    beds: "1,000-bed hospital",
    gpus: "8× L40S + 2× H100 cluster",
    capex: "Multi-site ready",
    desc: "Dedicated model zone, full drift monitoring, and cross-site disaster recovery.",
  },
];

/* ----------------------------- Roadmap --------------------------- */

export type Phase = {
  phase: string;
  title: string;
  timeframe: string;
  bullets: string[];
  gate: string;
};

export const PHASES: Phase[] = [
  {
    phase: "Phase 0",
    title: "Foundation",
    timeframe: "Weeks 1–4",
    bullets: [
      "Governance charter signed",
      "Data-use agreements in place",
      "De-ID gate online with QA sampling",
      "Synthea synthetic-data dry run",
    ],
    gate: "Gate: charter signed · de-ID ≥95% recall",
  },
  {
    phase: "Phase 1",
    title: "Pilot",
    timeframe: "Days 30–90",
    bullets: [
      "Willow Writer pilot in 2 departments",
      "Silent-mode evaluation harness running",
      "Clinician review board convened",
    ],
    gate: "Gate: ≥80% draft acceptance · zero PHI incidents",
  },
  {
    phase: "Phase 2",
    title: "Scale",
    timeframe: "Months 4–9",
    bullets: [
      "Charts + Sage scale-out",
      "FHIR write-back to the EHR",
      "Drift monitoring live in production",
    ],
    gate: "Gate: silent-mode targets met",
  },
  {
    phase: "Phase 3",
    title: "Federation",
    timeframe: "Months 10–18",
    bullets: ["Triage + Pulse launched", "Multi-site rollout", "EU AI Act conformity pack filed"],
    gate: "Gate: conformity pack reviewed",
  },
];

/* ------------------------------ Risks ---------------------------- */

export type RiskLevel = "Low" | "Med" | "High" | "Critical";

export type Risk = {
  risk: string;
  likelihood: RiskLevel;
  impact: RiskLevel;
  mitigation: string;
};

export const RISKS: Risk[] = [
  {
    risk: "Hallucination reaches the chart",
    likelihood: "Med",
    impact: "High",
    mitigation: "Citation grounding + mandatory clinician sign-off",
  },
  {
    risk: "PHI leakage",
    likelihood: "Low",
    impact: "Critical",
    mitigation: "De-ID gate + full audit trail + egress allow-list",
  },
  {
    risk: "Model drift",
    likelihood: "Med",
    impact: "Med",
    mitigation: "Monthly eval re-runs, registry version pinning",
  },
  {
    risk: "License terms change",
    likelihood: "Low",
    impact: "High",
    mitigation: "License-neutral architecture, weight pinning",
  },
  {
    risk: "Shadow AI use by staff",
    likelihood: "Med",
    impact: "Med",
    mitigation: "SSO-gated apps + governance training",
  },
  {
    risk: "Alert fatigue",
    likelihood: "Med",
    impact: "Med",
    mitigation: "Silent-mode thresholds + KPI gates before alerting",
  },
  {
    risk: "MLOps skill gap",
    likelihood: "Med",
    impact: "Med",
    mitigation: "2 dedicated FTE + vendor-neutral documentation",
  },
  {
    risk: "Vendor / API deprecation",
    likelihood: "Low",
    impact: "Low",
    mitigation: "Self-hosted weights in pinned containers",
  },
];

/* ----------------------------- Footer ---------------------------- */

export const BUILT_ON =
  "Built openly on MedGemma · BioMistral · Meditron · BioGPT · medspaCy · scispaCy · OpenBioLLM · Clinical-T5";
