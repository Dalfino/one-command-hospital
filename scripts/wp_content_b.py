# Willow Health AI Suite whitepaper - content part B (Ch4-Ch10, References)

B = []

# ============ CHAPTER 4 ============
B.append(('h1', 'Product Lines for Clinical Operations'))
B.append(('body',
 "Architecture only matters when it changes someone's Tuesday afternoon. The six Willow product lines are therefore described by workflow - who touches them, when, and what changes for the clinician - rather than by model. "
 "Each product ships with its own KPI set, its own review gate, and its own kill criteria; no product writes to the record without a named human owner approving the output. "
 "Table 3 maps every product to its engine, its EHR surface and its primary KPI."))
B.append(('h3', 'Willow Writer - discharge and after-visit documentation'))
B.append(('body',
 "Writer monitors the discharge event on the ADT feed, assembles chart context through the FHIR gateway, and drafts a discharge summary or after-visit note in the hospital's own house style within 90 seconds of the trigger. "
 "The draft opens in the clinician's existing EHR context via SMART on FHIR with every factual claim linked to its source note; the clinician edits and signs, and the AI never auto-signs anything. "
 "Target outcomes are a 20 to 30 percent reduction in documentation time per discharge and same-day sign-off rates above 90 percent in pilot departments."))
B.append(('h3', 'Willow Sage - guideline-grounded clinical Q&A'))
B.append(('body',
 "Sage answers protocol and policy questions for clinicians and operations staff - dosing thresholds, isolation rules, referral pathways - by retrieving from the hospital's controlled document library and generating an answer in which every sentence carries a citation to a retrieved passage. "
 "When retrieval confidence is low, Sage refuses and routes the question to the owning committee instead of improvising; the refusal log is itself a governance signal showing which guideline gaps matter most to staff. "
 "The product KPI is simple: 100 percent of answers citation-grounded, zero uncited factual claims in weekly audits."))
B.append(('h3', 'Willow Charts - note intelligence and risk flags'))
B.append(('body',
 "Charts runs the scispaCy and medspaCy pipelines continuously over new notes, maintaining coded extractions (LVEF, NYHA class, medication changes) and firing Clinical-Longformer/T5-based readmission and sepsis risk scores into a daily ward-level digest. "
 "It deliberately ships as a digest, not as interruptive alerts: the 2026 literature on AI-in-CDSS is blunt that unmanaged alerting produces fatigue and abandonment. "
 "After a 90-day silent-mode validation against actual outcomes, threshold-tuned flags are surfaced to charge nurses and the care-management team."))
B.append(('h3', 'Willow Pulse - evidence digest and relation mining'))
B.append(('body',
 "Pulse ingests the daily PubMed/MEDLINE feed, runs BioGPT relation extraction to pre-screen articles against each department's registered interest profile, and produces a morning digest of ranked, linked summaries - two minutes of reading per specialty, not two hours of searching. "
 "Research teams subscribe to entity profiles (a drug, a pathway, a device class) and the digest keeps a visible provenance chain back to every source article. "
 "The KPI is engagement: subscriptions active and reviewed weekly by at least 60 percent of subscribing clinicians after month three."))
B.append(('h3', 'Willow Triage - telehealth pre-consultation'))
B.append(('body',
 "Triage is a structured intake front-end for telehealth and nurse hotlines: OpenBioLLM-8B reasons over a structured symptom schema to produce a pre-consultation summary and a suggested urgency tier, which a registered nurse reviews before anything enters the record. "
 "Red-flag symptom patterns trigger deterministic escalation paths that bypass the model entirely - chest pain protocols, for example, are rule-based by design. "
 "The product's contract with the hospital is explicit: it increases telehealth throughput and consistency, and it never makes an autonomous clinical decision."))
B.append(('h3', 'Willow Sentinel - the compliance console'))
B.append(('body',
 "Sentinel is the product the other five cannot live without: the operations console for the Trust Fabric, exposing the de-identification gate's sampling QA, the model registry with pinned weights and licenses, drift dashboards per model and per input stream, the full audit trail of every model call, and the incident-response workflow. "
 "It is designed for the compliance officer and the ML operations engineer to share one screen, which is rarer than it should be and is precisely what makes the rest of the platform defensible in an audit. "
 "Its KPI is coverage: 100 percent of model calls logged, every model version traceable to corpus, license and reviewer."))
B.append(('table', {
  'caption': 'Table 3. Product-to-engine mapping and primary KPIs',
  'ratios': [0.16, 0.33, 0.27, 0.24],
  'font': 8.5,
  'header': ['Product', 'Engine stack', 'EHR surface', 'Primary KPI'],
  'rows': [
    ['Writer', 'MedGemma 4B fine-tune + medspaCy structuring', 'SMART on FHIR panel + note write-back', 'Draft in under 90 s; 20-30% time saved'],
    ['Sage', 'BioMistral-7B + citation RAG over guideline library', 'EHR-embedded search + web', '100% citation-grounded answers'],
    ['Charts', 'scispaCy + medspaCy + Clinical-Longformer/T5 heads', 'Ward digest + coded lists', 'Silent-mode AUROC gate passed'],
    ['Pulse', 'BioGPT relation mining + interest profiles', 'Email / intranet digest', '60% weekly clinician engagement'],
    ['Triage', 'OpenBioLLM-8B + rule-based escalation', 'Telehealth front-end', 'RN sign-off on 100% of encounters'],
    ['Sentinel', 'De-ID gate + registry + audit + drift monitors', 'Governance console', '100% of calls logged and traceable'],
  ]}))

# ============ CHAPTER 5 ============
B.append(('h1', 'Compliance and Governance Framework'))
B.append(('body',
 "Compliance is the hardest part of hospital AI - harder than model quality - because the failure modes are organizational, legal and reputational rather than statistical. "
 "An open model with 95 percent benchmark accuracy that leaks PHI once can end a CIO's career; a beautifully governed model at the same accuracy is a deployable asset. "
 "This chapter is therefore deliberately the deepest in the whitepaper, and it treats the three regimes that govern the platform - HIPAA, the EU AI Act and FDA device regulation - as engineering requirements with named owners, not as a legal appendix. "
 "Where a requirement is genuinely open to interpretation, the framework states the hospital's chosen position explicitly so it can be reviewed and signed, which is all any regulator actually asks of a deployer."))
B.append(('h2', '5.1 HIPAA: PHI routes and the de-identification gate'))
B.append(('body',
 "HIPAA permits four practical routes for running LLMs against protected health information: cloud model endpoints under a Business Associate Agreement, dedicated vendor capacity, self-hosted open weights, and fully on-premise GPUs. "
 "Willow uses the last two exclusively - self-hosted and on-premise - because they keep PHI inside the hospital security boundary, eliminate third-party BAAs for inference, and make every access auditable in one place. "
 "The de-identification gate applies HIPAA Safe Harbor logic (the 18 identifier categories per HHS guidance) using a Philter-class open toolkit plus medspaCy dictionaries, targeting above 95 percent recall with a human sampling program: one percent of de-identified traffic is double-read by trained staff, and any miss triggers re-tuning and a logged corrective action. "
 "Identified and de-identified zones are physically separated network segments, and re-identification attempts are both technically prevented and policy-prohibited."))
B.append(('h2', '5.2 EU AI Act: high-risk obligations on a deadline'))
B.append(('body',
 "The EU AI Act (Regulation 2024/1689) classifies AI medical devices as high-risk, and the core obligations for high-risk systems become fully enforceable in August 2026 - conformity assessment, technical documentation, human oversight, logging, data governance and risk management. "
 "Hospitals deploying in-scope systems are themselves on the hook as deployers, which makes waiting a strategic risk rather than a prudent delay. "
 "Willow's position is to treat the Act's requirements as the platform's minimum feature list, as Table 4 shows; the Fully Open Meditron audited-pipeline methodology gives every fine-tuned model a reproducible corpus and training record, which is the technical-documentation foundation the conformity assessment demands. "
 "Products whose regulatory posture is ambiguous are shipped in monitoring-only mode until legal review resolves them."))
B.append(('table', {
  'caption': 'Table 4. EU AI Act high-risk obligations mapped to Willow deliverables',
  'ratios': [0.30, 0.70],
  'font': 8.5,
  'header': ['Obligation (enforceable Aug 2026)', 'Willow deliverable'],
  'rows': [
    ['Risk management system', 'Sentinel risk register per product; kill criteria; incident workflow with owners'],
    ['Technical documentation', 'Meditron-style audited corpus records; registry entries per model version'],
    ['Data governance', 'Documented provenance of all training data; de-ID gate for operational data'],
    ['Human oversight', 'Human-in-the-loop review in every product; no autonomous write paths'],
    ['Logging and record-keeping', 'Immutable audit trail of every model call, input hash and output disposition'],
    ['Conformity assessment support', 'Per-product documentation pack maintained in Sentinel, reviewed quarterly'],
  ]}))
B.append(('h2', '5.3 FDA: the SaMD boundary and the PCCP strategy'))
B.append(('body',
 "FDA regulation turns on whether a software function is a medical device - intended to diagnose, cure, mitigate, treat or prevent disease. "
 "Willow's boundary analysis (Table 5) classifies Writer, Sage and Pulse as clinical and administrative workflow tools that inform clinicians but do not drive device-level decisions; Charts risk scores and Triage sit closer to the line and are treated as candidate SaMD with a deliberately conservative posture. "
 "For anything that may cross into device territory, the platform adopts the FDA's Predetermined Change Control Plan approach (final guidance December 2024; draft lifecycle guidance January 2025): pre-declared update protocols, pre-specified performance thresholds and revalidation procedures, so model improvements ship inside an approved change envelope rather than as uncontrolled drift. "
 "Silent-mode-first deployment - models run and are measured for a full quarter before any human sees their output - is the standing rule for every candidate-SaMD component."))
B.append(('table', {
  'caption': 'Table 5. FDA SaMD boundary analysis per product line',
  'ratios': [0.16, 0.26, 0.30, 0.28],
  'font': 8.5,
  'header': ['Product', 'SaMD posture', 'Rationale', 'Control posture'],
  'rows': [
    ['Writer', 'Not a device (intended)', 'Drafts text for clinician edit; no diagnostic claim', 'Workflow tool; human sign-off mandatory'],
    ['Sage', 'Not a device (intended)', 'Retrieves and cites controlled guidelines', 'Citation grounding; refusal behavior'],
    ['Pulse', 'Not a device (intended)', 'Literature digest; no patient-level output', 'Provenance links to source articles'],
    ['Charts / Triage', 'Candidate SaMD', 'Patient-level risk and urgency outputs', 'Silent-mode validation; PCCP draft before live use'],
  ]}))
B.append(('h2', '5.4 Governance structure and kill criteria'))
B.append(('body',
 "The AI steering committee is the governance instrument: a standing body chaired by the CMIO with subgroups for clinical validation, data governance and ML operations, meeting monthly with authority to pause any product. "
 "Every Willow product carries a validation file (benchmarks, silent-mode results, clinician review sampling rates), a named clinical owner, and pre-agreed kill criteria - conditions under which the product is switched off without a meeting: PHI incident at the gate, hallucination rate above threshold in weekly audit, AUROC below the silent-mode gate, or two consecutive drift alarms. "
 "Pre-agreed kill criteria are what make AI governance real; a committee that must debate each failure from scratch will always be too slow. "
 "Shadow use is treated as a governance defect with its own corrective action: all Willow apps are SSO-gated, and usage outside intended workflows is surfaced by Sentinel's audit analytics."))

# ============ CHAPTER 6 ============
B.append(('h1', 'Deployment and Infrastructure'))
B.append(('body',
 "The reference deployment is fully on-premise: inference never leaves the hospital network, and the platform runs as containers on Kubernetes in four security zones - a DMZ for the FHIR gateway, an application zone for Willow services, a data zone for the de-identified store and vector indexes, and a restricted model zone where the GPU fleet lives. "
 "Serving uses vLLM with continuous batching; 4-bit quantization (GPTQ/AWQ) is the default for models above 8B so that 27B-class models fit a 48 GB card with acceptable latency. "
 "The encoder fleet (scispaCy, medspaCy, Longformer/T5 heads) is CPU-capable and runs continuously at low cost. "
 "Backups follow the 3-2-1 rule with daily configuration snapshots; the full stack is redeployable from the registry in under a day, which is also the disaster-recovery commitment."))
B.append(('table', {
  'caption': 'Table 6. GPU sizing by model class',
  'ratios': [0.30, 0.28, 0.22, 0.20],
  'font': 8.5,
  'header': ['Model class', 'GPU requirement', 'Serving mode', 'Typical throughput'],
  'rows': [
    ['7B (BioMistral, OpenBioLLM)', '1 x 24 GB (L40S / A10)', 'vLLM, 4-bit', '~120 tok/s'],
    ['27B (MedGemma text)', '1 x 48 GB or 2 x 24 GB', 'vLLM, 4-bit', '~40 tok/s'],
    ['Encoder fleet + risk heads', 'CPU or 1 x 16 GB', 'Batch queues', 'Continuous'],
    ['Optional 70B (Meditron)', '2-4 x 80 GB (A100 / H100)', 'vLLM, 4-bit', '~25 tok/s'],
  ]}))
B.append(('table', {
  'caption': 'Table 7. Reference configurations by hospital size',
  'ratios': [0.18, 0.30, 0.26, 0.26],
  'font': 8.5,
  'header': ['Hospital', 'GPU fleet', 'Estimated hardware capex', 'Scope'],
  'rows': [
    ['200 beds', '2 x L40S', 'USD 60,000 - 80,000', 'Writer + Sage + encoders'],
    ['500 beds', '4 x L40S + 1 x A100', 'USD 120,000 - 160,000', 'All six products'],
    ['1,000 beds', '8 x L40S + 2 x H100', 'USD 250,000 - 350,000', 'All products, multi-site ready'],
  ]}))
B.append(('body',
 "Monitoring covers the serving layer and the statistical layer: GPU utilization, queue depth and token latency drive capacity decisions, while Sentinel's drift monitors watch input note distributions, output length and refusal rates per model, alerting on two consecutive alarms. "
 "Capacity is planned with headroom - the 500-bed configuration runs a target 60 percent utilization at peak - because a documentation copilot that queues at 08:00 on Mondays will be abandoned within a month, and abandonment is the most expensive failure mode of all. "
 "Model weights are pinned in an internal registry with corpus hashes and license records, which doubles as the EU AI Act technical-documentation substrate described in Chapter 5."))

# ============ CHAPTER 7 ============
B.append(('h1', 'EHR Integration via HL7 FHIR'))
B.append(('body',
 "Integration is a workflow problem before it is a technical one, and the platform's rule is that clinicians never leave the EHR to use Willow. "
 "The FHIR R4 gateway exposes context reads (Patient, Encounter, DocumentReference, Condition, MedicationRequest) and SMART on FHIR launch contexts, so Writer opens as an EHR panel already scoped to the right patient and encounter. "
 "Event-driven triggers come off the ADT feed: discharge events invoke Writer, new note events feed Charts, and guideline publication events invalidate the relevant Sage retrieval chunks. "
 "All traffic is logged end-to-end by Sentinel, which is what makes the integration audit-ready rather than merely functional. Figure 2 shows the round trip."))
B.append(('image', 'diagram_fhir.png', 'Figure 2. FHIR integration round trip: read, protect, infer, review, write back'))
B.append(('body',
 "Write-back is conservative by policy: Writer produces signed-note documents as DocumentReference resources with the human author as author and the model recorded in provenance; Charts contributes to a parallel coded layer rather than overwriting clinician-entered data; nothing ever writes to medication or order pathways. "
 "This preserves clinical accountability while still giving coding, quality and analytics teams the structured exhaust they need. "
 "Testing runs on Synthea synthetic patients end-to-end before any real chart is touched, and the integration rollout is phased by read scope: Phase 1 reads demographics and documents for Writer only; Phase 2 adds the ADT event bus and Labs for Charts; Phase 3 enables write-back beyond documents after two clean audit cycles. "
 "EHR-vendor specifics (Epic App Orchard vs SMART standards track) are an implementation detail the gateway isolates the products from."))

# ============ CHAPTER 8 ============
B.append(('h1', 'ROI and Total Cost of Ownership'))
B.append(('body',
 "The financial model compares three-year total cost of ownership for a 100-clinician deployment. "
 "Commercial documentation AI prices at 2,500 to 7,200 US dollars per clinician per year in 2026 analyst estimates - 250,000 to 720,000 US dollars annually, recurring, with the estate owned by the vendor. "
 "Willow's cost structure is instead front-loaded: hardware (100,000 to 160,000 US dollars for the 500-bed class), a three-person run team (two MLOps engineers, one clinical informaticist, roughly 450,000 US dollars annually loaded), fine-tuning compute and evaluation overhead. "
 "At scale that lands at roughly 900 to 1,400 US dollars per clinician per year all-in - one third to one fifth of commercial pricing - and the hospital owns the weights, the data and the capability outright. Figure 3 visualizes the per-clinician contrast."))
B.append(('image', 'chart_roi.png', 'Figure 3. Annual documentation-AI cost per clinician: Willow open stack vs commercial scribes'))
B.append(('table', {
  'caption': 'Table 8. Three-year TCO sketch, 100-clinician deployment (USD thousands)',
  'ratios': [0.34, 0.22, 0.22, 0.22],
  'font': 8.5,
  'header': ['Cost line', 'Willow (3 yr)', 'Commercial low (3 yr)', 'Commercial high (3 yr)'],
  'rows': [
    ['Software licenses / subscriptions', '0', '7,500', '21,600'],
    ['Hardware (amortized 3 yr)', '40 - 55', 'included', 'included'],
    ['Run team (3 FTE, 3 yr)', '1,350', 'vendor-provided', 'vendor-provided'],
    ['Fine-tuning + evaluation', '90 - 120', 'n/a', 'n/a'],
    ['Three-year total', '1,480 - 1,525', '7,500', '21,600'],
  ]}))
B.append(('body',
 "The benefit side compounds the case. At the JAMA-anchored 20 to 30 percent documentation-time reduction, a 100-clinician institution recovers roughly 8,000 to 12,000 clinician hours annually; valued conservatively at clinical-assistant rates, that alone covers the Willow run team. "
 "Burnout and retention effects are harder to price but directionally enormous - one locum month costs more than a GPU - and the coded-exhaust products (Charts) support quality reporting and coding efficiency that commercial scribes do not provide at all. "
 "Under the model's assumptions, hardware pays for itself in 12 to 20 months against the commercial-low scenario, and immediately against commercial-high. "
 "The honest caveats: the model assumes a hospital that can hire and retain two MLOps engineers, and Willow's benefits depend on the fine-tuning program actually being run - a license without a training plan is shelfware."))

# ============ CHAPTER 9 ============
B.append(('h1', 'Implementation Roadmap'))
B.append(('body',
 "The roadmap is built around one principle: earn trust in a narrow lane first, then widen it. "
 "Phase 0 establishes the machinery of governance before any clinical touch; Phase 1 runs Willow Writer in two departments under silent-mode-plus-review; Phase 2 scales Writer, adds Charts and Sage with FHIR write-back; Phase 3 extends to Triage, Pulse and multi-site rollout with the EU AI Act conformity pack complete. "
 "Every phase ends in a go / no-go gate chaired by the steering committee with the kill criteria from Chapter 5 already in force. Table 9 lays out the windows, the work and the gates."))
B.append(('table', {
  'caption': 'Table 9. Phased implementation plan with gates',
  'ratios': [0.13, 0.14, 0.47, 0.26],
  'font': 8.5,
  'header': ['Phase', 'Window', 'Key activities', 'Gate to advance'],
  'rows': [
    ['Phase 0', 'Weeks 1-4', 'Governance charter; data-use agreements; de-ID gate online; synthetic (Synthea) end-to-end dry run; registry seeded', 'De-ID sampling QA at target recall; dry run clean'],
    ['Phase 1', 'Days 30-90', 'Writer fine-tune on pilot-department notes; 2-department pilot; clinician review board; weekly audits', '20%+ documentation-time reduction; zero PHI incidents; sign-off satisfaction 4/5'],
    ['Phase 2', 'Months 4-9', 'Writer scale-out; Charts silent mode then threshold release; Sage guideline RAG live; FHIR write-back', 'Charts AUROC gate passed; Sage 100% citation audit; two clean audit cycles'],
    ['Phase 3', 'Months 10-18', 'Triage with RN gate; Pulse digests; multi-site rollout; EU AI Act conformity pack finalized', 'Committee review; regulator-ready documentation accepted'],
  ]}))
B.append(('body',
 "KPIs are tracked per product from day one - time-to-draft, edit distance, sign-off latency for Writer; extraction precision and AUROC for Charts; citation completeness and refusal quality for Sage - and every KPI has a pre-agreed threshold, because a metric without a threshold is trivia rather than governance. "
 "The committee reviews the full KPI panel monthly, and the roadmap itself is versioned: delays are recorded with causes, which turns the implementation history into evidence of operational maturity rather than an embarrassment. "
 "Resourcing follows the same logic - Phase 0 requires roughly 0.5 FTE of legal and 1.0 FTE of informatics time; steady state is the three-person run team plus departmental clinical champions, whose role is to keep the workflow honest as scale grows."))

# ============ CHAPTER 10 ============
B.append(('h1', 'Risk Register and Validation Protocol'))
B.append(('body',
 "Every residual risk worth managing is in Table 10, scored for likelihood and impact with a named mitigation and owner. "
 "The register is a living document in Sentinel - reviewed monthly by the steering committee, with additions welcome from any staff member through the incident channel. "
 "The most consequential risks are not exotic: hallucination entering the chart and PHI leakage at the gate are the two events that would end the program, which is why their mitigations (human sign-off on every output; de-identification plus sampling QA) are structural rather than procedural."))
B.append(('table', {
  'caption': 'Table 10. Risk register (L = likelihood, I = impact)',
  'ratios': [0.20, 0.09, 0.11, 0.42, 0.18],
  'font': 8,
  'header': ['Risk', 'L', 'I', 'Mitigation', 'Owner'],
  'rows': [
    ['Hallucinated content enters record', 'Med', 'High', 'Citation grounding; clinician sign-off on 100% of outputs; weekly hallucination audit', 'CMIO'],
    ['PHI leakage past de-ID gate', 'Low', 'Critical', 'Safe Harbor gate; 1% human double-read; zoned network; re-ID prohibition', 'Security officer'],
    ['Model drift over time', 'Med', 'Med', 'Input/output distribution monitors; monthly eval suite; registry pinning', 'ML Ops lead'],
    ['Upstream license change', 'Low', 'High', 'License-neutral architecture; weights pinned per version; legal review of derivatives', 'Legal'],
    ['Shadow use outside workflow', 'Med', 'Med', 'SSO-gated apps; audit analytics for off-pattern usage; governance training', 'Clinical champion'],
    ['Alert fatigue from Charts', 'Med', 'Med', 'Digest-first design; silent-mode thresholds; KPI-gated release', 'Ward leads'],
    ['MLOps skill gap', 'Med', 'Med', 'Two dedicated FTE; vendor-neutral docs; runbook-first operations', 'CIO'],
    ['Vendor/platform deprecation', 'Low', 'Low', 'Self-hosted weights; pinned containers; redeployable in one day', 'ML Ops lead'],
  ]}))
B.append(('h2', '10.1 Validation protocol'))
B.append(('body',
 "Validation is a permanent process, not a launch event, and it runs on four instruments. "
 "Benchmark gates: every model version passes a frozen internal benchmark suite (task-specific: MedQA-class for reasoners, NER F1 for extractors, AUROC for risk heads) before the registry will serve it. "
 "Silent-mode evaluation: every new or retrained model runs for one full quarter producing output nobody sees, while outcomes are collected and scored against the gate thresholds. "
 "Clinician review sampling: a fixed percentage of live outputs is double-read weekly by reviewing clinicians, with edit distance as the primary quality signal and findings reported to the committee. "
 "Red-teaming: a quarterly adversarial exercise in which clinicians deliberately try to induce unsafe outputs, with results scored and mitigated like any other defect."))
B.append(('h2', '10.2 Kill criteria'))
B.append(('body',
 "Each product carries pre-agreed kill criteria that trigger automatic suspension pending committee review: any PHI incident at the gate; hallucination audit rate above threshold in any weekly cycle; performance below the silent-mode gate; or two consecutive drift alarms on the serving layer. "
 "Suspension is a one-command operation per product - the router drops it from the serving pool - because a safety mechanism that takes an afternoon to execute is not a safety mechanism. "
 "Reinstatement requires a documented root cause, a revalidation pass and committee sign-off, and the full history is retained in Sentinel as part of the audit trail. "
 "The existence of credible, rehearsed kill criteria is, in the end, the strongest argument the hospital can make to itself and to any regulator that this platform is governed in fact and not only on paper."))

# ============ REFERENCES ============
B.append(('h1_plain', 'References'))
B.append(('refs', [
 "Google. (2026). MedGemma 1.5 technical report and model card. Health AI Developer Foundations. https://developers.google.com/health-ai-developer-foundations/medgemma/model-card",
 "Sellergren, A. B., et al. (2026). MedGemma: Technical report on medical vision-language foundation models based on Gemma 3. arXiv.",
 "Labrak, Y., et al. (2024). BioMistral: A collection of open-source pretrained large language models for medical domains. arXiv:2402.10373.",
 "Chen, Q., et al. (2025). BioMistral-NLU: Towards more generalizable medical language understanding models. PMC.",
 "Zhang, Z., et al. (2026). Fully Open Meditron: An auditable pipeline for clinical LLMs. arXiv.",
 "Pinto, F., et al. (2023). Meditron-70B: Open-source medical large language models. EPFL / Hugging Face.",
 "Luo, R., et al. (2022). BioGPT: Generative pre-trained transformer for biomedical text mining. Bioinformatics, 38(6).",
 "Eyre, H., et al. (2022). Launching into clinical space with medspaCy: A new clinical text processing toolkit in Python. JAMIA.",
 "Neumann, M., et al. (2019). scispaCy: Fast and robust models for biomedical natural language processing. ACL.",
 "Ankit, A., et al. (2024). Llama3-OpenBioLLM-8B: Open biomedical LLM achieving GPT-4-class performance. Hugging Face.",
 "Lehman, E., et al. Clinical-T5: Large language models built using MIMIC clinical text. PhysioNet.",
 "Li, Y., et al. (2022). Clinical-Longformer and Clinical-BigBird: Transformers for long clinical documents. arXiv:2204.05332.",
 "Pandey, S. R., et al. (2025). Predicting 30-day hospital readmissions using ClinicalT5 embeddings with structured EHR data. PLOS ONE.",
 "Olson, K. D., et al. (2025). Use of ambient AI scribes to reduce administrative burden and professional burnout. JAMA.",
 "Hakim, J. B., et al. (2025). The need for guardrails with large language models in healthcare. npj Digital Medicine (Nature).",
 "U.S. Department of Health and Human Services. (2025). Guidance regarding methods for de-identification of protected health information under HIPAA.",
 "U.S. Food and Drug Administration. (2024-2025). Predetermined change control plans for AI-enabled device software functions; AI-enabled device software functions: lifecycle management. FDA CDRH.",
 "European Union. (2024). Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (AI Act). Official Journal of the European Union.",
 "Dennstädt, F., et al. (2026). The EU AI Act: Implications and compliance guidance for healthcare organisations. Frontiers in Digital Health.",
 "Kartchner, D., et al. (2023). A comprehensive evaluation of biomedical entity linking models. PMC.",
]))
