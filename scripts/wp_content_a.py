# Willow Health AI Suite whitepaper - content part A (Exec Summary, Ch1-Ch3)
# Block types: h1, h2, h3, body, bullet, callout, table, image, quote

A = []

# ============ EXECUTIVE SUMMARY (unnumbered) ============
A.append(('h1_plain', 'Executive Summary'))
A.append(('body',
 "Clinical operations teams are spending an ever-growing share of their day on documentation rather than on patients. "
 "Peer-reviewed evidence now shows the scale of both the problem and the opportunity: clinician burnout fell from 51.9 percent to 38.8 percent within 30 days of introducing ambient AI documentation support (JAMA, 2025), and controlled studies consistently report 20 to 30 percent reductions in documentation time. "
 "Commercial platforms that deliver these gains exist, but they price at roughly 2,500 to 7,200 US dollars per clinician per year, lock hospitals into closed models, and move patient data through vendor infrastructure. "
 "At the same time, the open-source ecosystem has matured dramatically: Google's MedGemma 1.5, BioMistral-7B, EPFL's Meditron pipeline, and Stanford AIMI's Clinical-Longformer and Clinical-T5 encoders now operate at or near clinical-benchmark parity with proprietary systems."))
A.append(('body',
 "What open source has never shipped, however, is the wrapper that makes any of it hospital-grade: de-identification, guardrails, audit trails, validation protocols, and a governance structure that a compliance officer would sign off on. "
 "That gap is exactly where this whitepaper positions the Willow Health AI Suite. Rather than deploying eight research projects as eight disconnected tools, Willow consolidates them into a single governed platform with four layers: a Trust Fabric that wraps every model call, an Intelligence layer that serves fine-tuned open models, a Data and Integration layer built on HL7 FHIR, and an Experience layer of six clinician-facing product lines. "
 "Every one of the eight source projects is retained, upgraded, and hardened in the process - none is discarded."))
A.append(('callout', '51.9% to 38.8%', 'Clinician burnout within 30 days of ambient AI documentation support (JAMA, 2025)'))
A.append(('body',
 "The economics support the investment. A self-hosted Willow deployment is estimated at 900 to 1,400 US dollars per clinician per year at 100-clinician scale, including hardware amortization and a three-person support team - roughly one third to one fifth of typical commercial scribe contracts - with payback on hardware in 12 to 20 months. "
 "The deepest chapter of this document is deliberately the compliance chapter, because that is the hardest part: HIPAA de-identification, EU AI Act high-risk obligations that become fully enforceable in August 2026, and FDA software-as-a-medical-device boundary analysis each demand engineering and governance commitments that no raw model download provides. "
 "The recommended next step is a 90-day, two-department pilot of Willow Writer under the governance framework described in Chapter 9, with explicit go and no-go gates agreed in advance."))

# ============ CHAPTER 1 ============
A.append(('h1', 'The Case for an Open Clinical AI Stack'))
A.append(('body',
 "The documentation burden in hospitals is no longer a soft complaint; it is a measured operational cost. Time-motion studies repeatedly show clinicians spending one to two hours on EHR and desk work for every hour of direct patient contact, with the EHR inbox alone consuming over an hour per day in primary care. "
 "The consequence is well quantified: burnout rates above 50 percent in several specialties, rising turnover, and attrition costs that hospitals absorb in recruitment and locum cover. "
 "Ambient and generative AI documentation tools are the first intervention class with randomized and quasi-experimental evidence of relief at scale, which is why health systems have raced to adopt them."))
A.append(('body',
 "The commercial market, however, prices that relief as a perpetual per-seat subscription with no path to ownership. Analyst estimates for 2026 place enterprise contracts for tools such as Abridge and Nuance Dragon Copilot between 2,500 and 7,200 US dollars per clinician per year; a 100-clinician department therefore commits 250,000 to 700,000 US dollars annually, forever, with the model weights, prompts, and evaluation data all owned by the vendor. "
 "Closed systems also complicate privacy review: PHI leaves the hospital boundary, and the hospital cannot independently verify what the model does with it. "
 "For an institution that intends to build durable internal capability - rather than rent it - the open-weight ecosystem has crossed the quality threshold."))
A.append(('body',
 "Table 1 summarizes the eight projects this platform is built from. Two facts stand out. First, coverage is remarkably complementary: multimodal medical foundation models (MedGemma), domain-pretrained reasoners (BioMistral, Meditron), clinical assertion engines (medspaCy), entity-linking toolkits (scispaCy), long-document encoders (Clinical-Longformer, Clinical-T5), and narrow high-precision miners (BioGPT) together cover nearly every clinical-language workload a hospital has. "
 "Second, licenses are workable for hospital use, with two caveats - the Gemma terms attach use restrictions to derivatives, and PhysioNet-credentialed models inherit a data use agreement - both manageable and addressed in Chapter 5. "
 "What none of them ships is hospital readiness itself, which is the productization work described in the rest of this document."))
A.append(('table', {
  'caption': 'Table 1. The eight source projects at a glance',
  'ratios': [0.185, 0.145, 0.205, 0.215, 0.25],
  'font': 8.5,
  'header': ['Project', 'Origin', 'Class', 'License', 'Role in Willow'],
  'rows': [
    ['MedGemma 1.5 (4B / 27B)', 'Google', 'Multimodal medical LLM', 'Gemma Terms of Use', 'Primary writer / multimodal engine'],
    ['BioMistral-7B', 'EU consortium', 'Domain-pretrained LLM', 'Apache-2.0', 'Guideline QA reasoner + RAG'],
    ['Meditron (7B / 70B)', 'EPFL', 'Clinical LLM pipeline', 'Llama-2 Community', 'Audited training pipeline'],
    ['BioGPT', 'Microsoft', 'Biomedical transformer', 'MIT', 'Relation mining / evidence digest'],
    ['medspaCy', 'JHU / Vanderbilt / NIH', 'Rule-based clinical NLP', 'MIT', 'Assertion + section engine'],
    ['scispaCy', 'AllenAI', 'Biomedical NLP models', 'Apache-2.0 (code)', 'NER + UMLS entity linking'],
    ['OpenBioLLM-8B', 'Saama / aaditya', 'Fine-tuned medical LLM', 'Llama-3 Community', 'Triage reasoning engine'],
    ['Clinical-Longformer / Clinical-T5', 'Stanford AIMI', 'MIMIC-pretrained encoders', 'PhysioNet-credentialed', 'Risk heads on long notes'],
  ]}))
A.append(('body',
 "The strategic logic is therefore not open versus commercial on quality alone - it is ownership versus rental, transparency versus black box, and fixed cost versus perpetual per-seat fees. "
 "Open weights let the hospital fine-tune on its own note style, pin versions in a registry, and pass audits with full artifact traceability. "
 "The remainder of this whitepaper describes how to convert that potential into a governed, production-grade clinical platform."))

# ============ CHAPTER 2 ============
A.append(('h1', 'Platform Architecture: The Willow Suite'))
A.append(('body',
 "Willow Health AI Suite is a four-layer platform in which every clinical capability shares one governance core. "
 "The design principle is governance-first: rather than bolting safety onto individual apps, the platform inserts a Trust Fabric between the models and everything else, so that no protected health information ever reaches a model un-de-identified and no generated output reaches a patient record without human review. "
 "This inverts the usual open-source failure mode, where impressive demos fail procurement precisely because the compliance wrapper was never engineered. Figure 1 shows the layers and their components."))
A.append(('image', 'diagram_arch.png', 'Figure 1. Willow Suite four-layer platform architecture'))
A.append(('body',
 "The Intelligence layer runs a shared vLLM serving pool behind a model router, which is what makes the platform economical: a 7B model on a single 24 GB GPU serves Sage and Triage traffic, MedGemma 4B handles Writer drafts, and the encoder fleet runs on modest hardware, all scaled independently per department workload. "
 "The Data and Integration layer exposes everything through an HL7 FHIR R4 gateway with SMART on FHIR launch contexts, so products appear inside the existing EHR workflow instead of as a separate tab clinicians must remember to open. "
 "The Experience layer packages capabilities into the six product lines detailed in Chapter 4, each with its own KPI set and its own go and no-go criteria."))
A.append(('table', {
  'caption': 'Table 2. Layer responsibilities and component inventory',
  'ratios': [0.17, 0.44, 0.39],
  'font': 8.5,
  'header': ['Layer', 'Components', 'Function'],
  'rows': [
    ['4 Experience', 'Writer, Sage, Charts, Pulse, Triage apps', 'Clinician-facing workflow entry points with per-product KPIs'],
    ['3 Data / Integration', 'FHIR R4 gateway, SMART on FHIR, event bus, synthetic harness', 'EHR context in, signed output back; ADT and discharge triggers'],
    ['2 Intelligence', 'vLLM pool, model router, fine-tuned MedGemma, BioMistral+RAG, Clinical-Longformer/T5, BioGPT', 'Serving, routing and tuning of all open models'],
    ['1 Trust Fabric', 'De-ID gate, guardrails and citation grounding, human-in-the-loop, audit trail and model registry, drift monitoring, governance console', 'Safety, compliance and evidence for every model call'],
  ]}))
A.append(('body',
 "Two architectural decisions deserve emphasis. First, the model router means models are swappable, not load-bearing: if a license changes or a better open model appears, the platform upgrades without re-platforming, which neutralizes the main long-term risk of open-source dependence. "
 "Second, the Trust Fabric is itself a product (Willow Sentinel) with a user interface, dashboards, and an owner - governance that is visible and staffed, rather than a policy document in a drawer. "
 "This is the single most important differentiator between a pile of checkpoints on Hugging Face and a system a hospital can actually run."))

# ============ CHAPTER 3 ============
A.append(('h1', 'Source Projects: Deep-Dive and Improvisation Plan'))
A.append(('body',
 "Each of the eight projects was reviewed individually: what it verifiably is today, what license governs it, where it falls short of hospital use, and the specific improvisation Willow applies. "
 "The pattern is consistent - keep the trained knowledge in the weights, replace the research scaffolding with production infrastructure, and harden with the Trust Fabric. "
 "None of the eight is used as-is; none is discarded either."))

A.append(('h2', '3.1 MedGemma 1.5 (Google) - the Writer engine'))
A.append(('body',
 "MedGemma 1.5 is Google's open medical vision-language family built on Gemma 3, shipped in a 4B multimodal variant with a SigLIP image encoder pre-trained on de-identified medical data - chest X-rays, CT and MRI volumes, histopathology and dermatology imaging - and a 27B text-heavy variant. "
 "The 1.5 release improved MedQA accuracy by 5 percent and EHRQA by 22 percent over the original, and Google explicitly expects developers to fine-tune it for institutional use cases. "
 "The license is the Gemma Terms of Use: free for research and commercial use, but with use restrictions that propagate to derivative models, which Chapter 5 handles through registry pinning and legal review. "
 "Willow keeps MedGemma as the multimodal core of Willow Writer and, in the 27B variant, as the escalation model for complex multimodal review."))
A.append(('box', ['Keep: multimodal medical foundation capability; benchmark trajectory across versions.',
                  'Add: supervised fine-tuning on hospital discharge summaries and after-visit notes with clinician-graded outcomes.',
                  'Harden: structured-output constraints, citation grounding to chart context, full Gemma-terms compliance tracking in the model registry.']))

A.append(('h2', '3.2 BioMistral-7B (EU consortium) - the Sage engine'))
A.append(('body',
 "BioMistral-7B is Mistral-7B-Instruct further pre-trained on the complete PubMed Central corpus and released under Apache-2.0, the cleanest license in this portfolio. "
 "It is competitive across ten medical question-answering benchmarks at 7B scale, has spawned follow-up work (BioMistral-NLU) generalizing its medical natural-language understanding, and is EU-hostable - a meaningful property for European data-residency requirements. "
 "Its weakness is exactly what raw pre-training never provides: it can sound authoritative while being wrong. "
 "Willow therefore deploys it exclusively behind retrieval-augmented generation over the hospital's own guideline library - NICE, WHO and institutional protocols - with every claim citation-grounded and answers that cannot cite a retrieved passage are refused rather than guessed."))
A.append(('box', ['Keep: Apache-2.0 weights; PubMed Central domain knowledge; EU hosting option.',
                  'Add: MEGA-RAG-style citation-grounded retrieval over local guidelines with refusal-on-no-evidence behavior.',
                  'Harden: guardrail layer per Nature npj Digital Medicine guidance; monthly benchmark regression suite.']))

A.append(('h2', '3.3 Meditron (EPFL) - the audited training pipeline'))
A.append(('body',
 "Meditron is EPFL's suite of medical LLMs adapted from Llama-2, pre-trained on clinical guidelines (WHO, UK NHS) plus PubMed abstracts and MIMIC-III/IV notes, and it was the strongest open medical model at its 2023 release. "
 "Its most valuable contribution to Willow in 2026 is not the weights but the methodology: the Fully Open Meditron pipeline (May 2026) publishes the first fully auditable LLM-CDSS recipe - a clinician-audited training corpus and a reproducible data pipeline - which is precisely the evidence trail a hospital must produce under EU AI Act technical-documentation obligations. "
 "Willow adopts the audited pipeline as the standard for all institutional fine-tuning, rather than treating training as an artisanal, undocumented activity."))
A.append(('box', ['Keep: guideline-grounded training corpus methodology; clinician-audit workflow.',
                  'Add: institution-specific small-model training for note style and local protocol vocabulary.',
                  'Harden: every training run versioned in the registry with corpus hashes and reviewer sign-off.']))

A.append(('h2', '3.4 BioGPT (Microsoft) - the Pulse miner'))
A.append(('body',
 "BioGPT is Microsoft's generative transformer for biomedical text, MIT-licensed including the pre-trained weights, with state-of-the-art results on BC5CDR, KD-DTI and DDI relation extraction and 78.2 percent on PubMedQA at publication. "
 "It is narrow by modern LLM standards - 346M parameters, BART-style generation - and that is exactly why it survives the cut: precision tasks with no hallucination tolerance, where a small deterministic specialist beats a large generalist. "
 "Willow uses BioGPT inside Willow Pulse for drug-disease and gene-disease relation extraction over incoming literature, feeding the daily evidence digest, and as a candidate-labeler to pre-screen publications before any generative summarization happens."))
A.append(('box', ['Keep: MIT-licensed relation-extraction checkpoints; PubMedQA-class QA ability.',
                  'Add: department interest profiles that rank the daily PubMed/MEDLINE digest per research team.',
                  'Harden: extraction-only role in the pipeline; outputs always linked to source article identifiers.']))

A.append(('h2', '3.5 medspaCy (JHU / Vanderbilt / NIH) - the assertion engine'))
A.append(('body',
 "medspaCy is the open clinical NLP toolkit behind a widely cited JAMA-format paper (Eyre et al., 2022), providing ConText-based assertion detection - negation, family history, uncertainty, experiencer and temporality - plus section detection and hybrid rule-and-statistical concept extraction. "
 "These are unglamorous capabilities with outsized safety value: a model that reads 'father had MI' as the patient having an MI is not a better model, it is a dangerous one. "
 "Willow embeds medspaCy in every pipeline that touches free text: Writer uses section detection to structure drafts, Charts uses ConText to qualify extracted findings, and the de-identification gate uses its dictionaries as a first-pass detector. "
 "Its MIT license and pure-Python deployment make it the lowest-risk component in the stack."))
A.append(('box', ['Keep: ConText assertion engine; section detection; hybrid extraction architecture.',
                  'Add: institutional ICD-10 and SNOMED coding dictionaries and local shorthand lists.',
                  'Harden: quarterly dictionary review with clinical informatics; assertion output logged for audit.']))

A.append(('h2', '3.6 scispaCy (AllenAI) - the UMLS coder'))
A.append(('body',
 "scispaCy provides spaCy pipelines and models for biomedical and scientific text, including NER models trained on BC5CDR and related corpora, abbreviation detection, and - critically - entity linking into UMLS, MeSH and RxNorm knowledge bases. "
 "That linking step is what turns 'atrial fibrillation' into a coded, queryable, billable, decision-support-ready concept, and it is the bridge between free-text notes and the structured world the EHR and coding teams live in. "
 "Willow fine-tunes its NER on cardiology notes to auto-extract LVEF values, NYHA class and medication lists for Willow Charts, and runs the UMLS linker in batch mode to maintain a coded problem list alongside the clinician's own. "
 "Because scispaCy models are small and CPU-capable, this runs continuously and cheaply on the encoder fleet."))
A.append(('box', ['Keep: BC5CDR-class NER; UMLS/MeSH/RxNorm entity linking; abbreviation detection.',
                  'Add: cardiology-domain NER fine-tune (LVEF, NYHA, meds) with a gold-standard held-out set.',
                  'Harden: extraction confidence thresholds; ambiguous-link flags routed to human coder queue.']))

A.append(('h2', '3.7 OpenBioLLM-8B (Saama / aaditya) - the Triage engine'))
A.append(('body',
 "OpenBioLLM-8B is a Llama-3-8B derivative tuned with domain-adaptive pre-training and preference optimization on medical data, averaging 72.5 percent across nine biomedical benchmarks - outperforming GPT-3.5-class and Meditron-70B at one tenth the size, with the 70B variant reaching 86.1 percent. "
 "Under the Llama-3 Community License (commercial use permitted below 700 million monthly active users), it gives Willow a strong medical reasoner that fits on a single 24 GB GPU. "
 "Willow uses it inside Willow Triage for structured symptom-intake reasoning and pre-consultation summaries - strictly as a decision-support aid with an RN review gate and deterministic escalation rules for red-flag symptoms, never as an autonomous decision maker. "
 "The multi-agent guardrail patterns from the 2026 clinical-safety literature wrap every triage turn."))
A.append(('box', ['Keep: 8B medical reasoning quality; single-GPU footprint; Llama-3 Community License.',
                  'Add: structured intake schema, red-flag escalation rules, telehealth front-end.',
                  'Harden: RN review gate; no-triage-without-human sign-off; conversation transcripts in the audit trail.']))

A.append(('h2', '3.8 Clinical-Longformer and Clinical-T5 (Stanford AIMI) - the Charts encoders'))
A.append(('body',
 "Clinical-Longformer adapts Longformer's 4,096-token sparse attention to MIMIC-III notes and consistently outperforms ClinicalBERT-class models on long-document clinical tasks, while Clinical-T5 provides four span-corruption models pre-trained on the union of MIMIC-III and MIMIC-IV notes. "
 "A 2025 PLOS study demonstrates the practical pattern: Clinical-T5 embeddings combined with structured EHR data predict 30-day readmission with clinically usable accuracy. "
 "Both are hosted on PhysioNet, which means access is credentialed and governed by a MIMIC data use agreement - a compliance nuance the registry tracks explicitly. "
 "Willow fine-tunes them as the readmission and sepsis risk heads of Willow Charts, deployed in silent mode until Chapter 10's validation gates are passed."))
A.append(('box', ['Keep: 4,096-token long-note encoding; MIMIC-III/IV pre-training; proven readmission pattern.',
                  'Add: hospital-cohort fine-tuning heads; silent-mode evaluation against 90-day outcomes.',
                  'Harden: PhysioNet DUA tracking in the registry; drift monitoring on input note distributions.']))
