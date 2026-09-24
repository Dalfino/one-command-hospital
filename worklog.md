# Multi-Agent Worklog

---
Task ID: 1
Agent: main (Super Z)
Task: Clarify requirements + deep research for Hospital AI Suite (portal + PDF whitepaper)

Work Log:
- AskUserQuestion completed. Locked brief: portal + PDF; audience = clinical operations; all 6 modules included; warm-care style with "alive" animated experience; deep research on all 8 projects then improvise all of them; compliance gets deepest treatment.
- Loaded skills: web-search, fullstack-dev, pdf.
- Initialized fullstack env (Next.js 16 + shadcn/ui scaffold at /home/z/my-project).
- Ran 3 research batches (scripts/research_batch1-3.sh) → 21 JSON files in /home/z/my-project/research/.

Stage Summary:
- KEY RESEARCH FINDINGS:
  * MedGemma 1.5 (Apr 2026): Gemma-3 based 4B multimodal (SigLIP encoder: CXR, CT/MRI, histopath, derm) + 27B text; +5% MedQA, +22% EHRQA vs v1; Google expects fine-tuning; Gemma Terms of Use = free commercial but with use restrictions, derivatives inherit terms.
  * BioMistral-7B: Apache-2.0, continued-pretrain of Mistral-7B-Instruct on PubMed Central, ~51.5% avg on 10 med-QA benchmarks; BioMistral-NLU (2025) extension exists; EU-hostable.
  * Meditron (EPFL): 7B/70B on Llama-2 (Community License); trained on clinical guidelines (WHO/NHS) + PubMed + MIMIC; "Fully Open Meditron" (May 2026) = first fully auditable LLM-CDSS pipeline w/ clinician-audited corpus.
  * BioGPT (Microsoft): MIT license; 346M/Large; SOTA BC5CDR, KD-DTI, DDI relation extraction; 78.2% PubMedQA; narrow but excellent research-mining tool.
  * medspaCy: MIT; ConText (negation/family/uncertainty/experiencer), section detection, hybrid rule+stat; JAMA-recognized (Eyre 2022).
  * scispaCy (AllenAI): NER (bc5cdr etc.) + UMLS/MeSH/RxNorm entity linking + abbreviation detection.
  * OpenBioLLM-8B: Llama-3 Community License; 72.5% avg on 9 biomedical benchmarks (> GPT-3.5, Meditron-70B; 70B variant 86.1%); DPO-tuned.
  * Clinical-Longformer: 4096-token sparse attention, MIMIC-III pretrain, beats ClinicalBERT on long-doc tasks. Clinical-T5: 4 models on MIMIC-III+IV (PhysioNet credentialed access - compliance nuance). 2025 PLOS study: ClinicalT5 embeddings + structured EHR → 30-day readmission.
  * HIPAA: 4 routes for PHI+LLM (BAA cloud / dedicated / self-hosted open weights / on-prem GPU); de-ID: Safe Harbor 18 identifiers, Philter/CliniDeID, open-source targets >95% recall; HHS guidance Feb 2025.
  * EU AI Act 2024/1689: AI medical devices = high-risk (Annex III); core obligations enforceable Aug 2026 (conformity assessment, tech docs, human oversight, logging, data governance).
  * FDA: Dec 2024 final PCCP guidance; Jan 2025 draft AI lifecycle guidance; 1,016 AI-ML devices approved thru 2024.
  * Deployment: 7B → 1×24GB GPU; 70B → 2-4×80GB; vLLM/NIM serving; quantization 4-bit.
  * ROI evidence: ambient scribes cut burnout 51.9%→38.8% in 30 days (JAMA 2025); 20-30% documentation time reduction; commercial scribes cost $2,500-$7,200/clinician/yr (Abridge/DAX) → open-stack TCO contrast.
  * Governance: AI governance committee w/ clinical validation + data governance + MLOps subgroups is the accepted pattern.
- PLATFORM CONCEPT (to build): "Willow Health AI Suite" — 4-layer open clinical AI platform: (1) Trust Fabric [Willow Sentinel: de-ID gate, guardrails, audit, model registry], (2) Intelligence Layer [fine-tuned MedGemma + BioMistral+RAG + encoder pipeline], (3) Data/Integration [FHIR gateway, SMART on FHIR], (4) Experience [6 product lines]: Writer, Sage, Charts, Pulse, Triage, Sentinel.

---
Task ID: 6
Agent: full-stack-developer
Task: Build the Willow Health AI Suite front-end — animated, warm-care-styled single-page Next.js 16 portal for clinical operations teams (route / only).

Work Log:
- Ran init-fullstack script; verified scaffold (Next.js 16 + Tailwind 4 + shadcn/ui, framer-motion 12 already present — no installs needed).
- Design system: wired Fraunces (display serif) + Nunito Sans (body) via next/font/google into CSS vars --font-fraunces/--font-nunito; added Tailwind 4 @theme tokens: cream #FAF7F2, sand #F4EDE4, pine #1E5C4F, forest #2D6A4F, sage #95B8A2, sage-light #DFEBDD, terracotta #D97742, amber-warm #D4A373, ink #4A4440. Zero blue/indigo classes (grep-verified; only false-positive "translate→slate" matches).
- ALIVE layer implemented in globals.css keyframes + framer-motion:
  * 4 drifting ambient blobs (20-40s loops, blur-3xl, sage/terracotta/amber/forest 15-45% opacity) in hero + footer CTA band
  * Brand-signature animated ECG trace: generated SVG QRS path (8 repeating units) with green 5s traveling dash + terracotta 9s secondary pulse (stroke-dashoffset keyframes, pathLength=100)
  * 8 floating medical particles (plus/dot/leaf) with per-item 8-16s float loops
  * Scroll-reveal via reusable <Reveal> (whileInView fade+rise, staggered delays), counters via <AnimatedCounter> (rAF, cubic ease, useInView once, useReducedMotion-aware): 51.9→38.8%, 0→30%, 0→7.2k, 0→1,016
  * Card hover: whileHover y:-4 spring + shadow bloom + terracotta border glow + icon micro-rotate/scale
  * Pulsing "always-on" dot on Trust Fabric layer + hero badge; animated connector drop-dots between stack layers; heartbeat-scale logo mark in nav
  * IdleIcon wrapper: 3-6s y-oscillation/sway on lucide icons in cards (staggered durations)
  * prefers-reduced-motion: global CSS kill-switch + framer useReducedMotion gates (no movement, counters jump to final value)
- Sections built (src/components/willow/*, composed in page.tsx): sticky glassmorphism nav (cream/70 backdrop-blur, Sheet hamburger w/ 7 links + CTA), Hero (badge chip, H1, subhead, 2 CTAs, 3 floating stat chips 6/8/100%, ECG), Why Now (4 cited counter cards), Platform (4-layer expandable stack, Trust Fabric highlighted + pulsing, governance tagline), Products (6 cards w/ built-from badges, bullets, KPI chips), Sources (8 keep/add cards, origin+license chips, license footnote), Compliance (4 shadcn Tabs w/ 6 animated checklist rows each), Deployment (reference stack list, GPU sizing table w/ min-w-[560px] internal scroll, 3 scenario cards), ROI (animated 100% vs 20% cost bars, 12-20mo payback card, 4 benefit chips), Roadmap (4-phase timeline, animated scaleX progress line desktop / vertical line mobile, gate chips), Risks (8-row table w/ Low/Med/High/Critical badges), Footer (pine CTA band + built-on line + disclaimer, mt-auto sticky footer).
- Lint: `bun run lint` clean (exit 0). Fixed en route: unused StatCard delay prop, unused PulsingDot import.
- Runtime bug found & fixed via browser: on 375px viewport the deployment grid caused +325px horizontal overflow (grid item min-width:auto inflated by GPU table min-content). Fix: min-w-0 on grid Reveal wrappers + min-w-[560px] on table inside overflow-x-auto → overflowX now 0, table scrolls internally.
- agent-browser verification (desktop 1366px + mobile 375px): title correct, zero console errors / zero page errors; all 9 anchored sections present; nav anchor click lands at scroll-mt 80px exactly; compliance tabs switch (EU AI Act / FDA verified: active state + 6 items each); platform layer 4 expand/collapse works (5 badges); counters reach 38.8 / 1,016 / 7.2 after inView animation; mobile hamburger opens Sheet (7 links), link click closes sheet + navigates (#compliance top=80px); footer bottom == document bottom (sticky-footer compliant); ECG/blobs/particles all mounted; VLM inspection of full-page desktop + mobile screenshots: "NO ISSUES".
- Final GET / → HTTP 200; dev.log clean (only a transient module-not-found during mid-write file creation, resolved; subsequent compiles clean).

Stage Summary:
- Portal front-end COMPLETE at route /: 12 willow components + data module, warm-care palette, full ALIVE animation system, responsive mobile-first, accessible (semantic landmarks, aria-expanded/controls, labelled sections, 44px touch targets, sr-safe tables), sticky footer.
- Fonts (Fraunces/Nunito Sans), palette tokens, keyframes live in globals.css/layout.tsx for reuse by later agents (e.g., PDF whitepaper should match #FAF7F2/#1E5C4F/#D97742).
- No deviations from spec; all 11 sections + nav/footer delivered; only addition is the mobile GPU-table internal scroll needed to kill overflow.

---
Task ID: 5,7,8 (main agent)
Task: PDF whitepaper production (outline, skill chain, build, QA)

Work Log:
- Set 14-section outline via Outline tool; output chapter numbering map (Exec Summary unnumbered, Ch1-10, References unnumbered).
- Read full pdf skill chain: report.md (all 1704 lines), fonts.md, palette.md, cover.md, cover-backgrounds.md, charts.md, overflow.md, pagination.md, typography.md, fill-engine.md, geometry.md.
- Generated cascade palette: intent=nature, monochrome, seed=7 (green family; header_fill #456454, accent #298959).
- Built Playwright+CSS diagrams (4-layer architecture, FHIR round trip) at 2x scale; matplotlib ROI horizontal bar chart per charts.md.
- Cover: Template 01 HUD, light bg, cascade CSS vars; fixed validator-flagged nested-span overlap; poster_validate PASS, cover_validate PASS; rendered via html2poster.js --width 794px.
- Body: ReportLab TocDocTemplate + multiBuild, FreeSerif + install_font_fallback, roman TOC numbering + arabic body reset, CondPageBreak orphan control, safe_keep_together, Paragraph-wrapped tables with ratio colWidths.
- Fixed 3 bugs found by inspection/QA: heading double-append in flush logic, body_start_page stale across multiBuild passes, caption/callout tuple indexing (captions dropped, callout rendered '5').
- QA chain: code.sanitize, meta.brand, pages.clean (0 blank), font.check (0 issues), toc.check (pass), pdf_qa.py --skip-cover: PASS (fixed cover page-size mismatch via 0.1pt normalize threshold).

Stage Summary:
- FINAL: /home/z/my-project/download/Willow_Health_AI_Suite_Whitepaper.pdf (23 pages, ~544 KB, vector, cover+TOC+10 chapters+18 references)
- Cover HTML source delivered at /home/z/my-project/download/Willow_Whitepaper_Cover.html
- Assets/scripts persisted under /home/z/my-project/scripts/ (diagram_arch.html, diagram_fhir.html, gen_chart.py, gen_body.py, wp_content_a/b.py, merge_final.py)

---
Task ID: 9 (main agent)
Task: Strategy pivot + scaffold the "One-Command Hospital — Guideline Copilot" flagship project

Work Log:
- Strategy evolved across user exchanges: improvising all repos rejected → independent-research framing → infra repos (#29-38) reviewed → 50-project list absorbed → ONE project locked: Guideline Copilot on the One-Command Hospital (OpenEMR sandbox, Medplum spine, OpenHIM bus, Presidio de-ID, BioMistral-7B vLLM, Meditron corpus as KB, medspaCy/scispaCy verifier, Synthea patients, HAPI conformance CI).
- Scaffolded /home/z/my-project/download/one-command-hospital/: README, docker-compose.yml (10 services + gpu/patients/conformance profiles), .env.example, Makefile, .gitignore.
- Knowledge base: guidelines/manifest.yaml (edition/expiry tracking = improvement #2) + 2 SYNTHETIC seed protocols (anticoagulation bridging v3.0, sepsis screening ed.2) with numbered sections.
- Eval harness: eval/qa_seed.yaml (24 pairs: 20 traced + 4 refusal traps) + run_eval.py (BM25 retrieval scoring, optional full-mode vs live RAG, CI gate at 80%, report.md). Fixed typo (f-"-) and refusal-trap grading bug en route.
- Services: deid-gate (FastAPI+Presidio), guideline-rag (BM25 → citation-forced prompt → vLLM, NOT_COVERED refusal, edition-stamped citations, extractive fallback), verifier (heuristic grounding/negation v0, ConText in Phase 1), ai-mediator (Node/Express: deid→RAG→verify→FHIR Communication with provenance + human_action).
- Stubs: smart-app/README (SMART on FHIR widget, Phase 1), tools/synthea/Dockerfile (two-stage Maven build, output to ./data/synthea).
- Docs: architecture.md (request lifecycle, safety layers, KILL CRITERIA, ops notes) + improvements.md (6 improvements with verify steps).
- Validated: py_compile all Python OK, YAML OK, eval green: 18/20 retrieval hits (90%, BM25 on; a03/s01 genuine misses → Phase 1 vector retrieval), CI gate passed.

Stage Summary:
- FLAGSHIP SCAFFOLD COMPLETE + PROVEN: eval harness runs green in retrieval-only mode (90%).
- The six improvements are implemented or stubbed with verify paths; compose file is the "one command" artifact.
- Prior deliverables (Willow portal at / route, whitepaper PDF) reflect the OLD all-8-improvise strategy — superseded by this architecture; portal/whitepaper need a content refresh pass to match the new one-project focus (pending user go-ahead).
- Next: Phase 1 (SMART widget, Bot JWT auth, medspaCy ConText verifier, vector retrieval, 200-question eval), then portal+whitepaper refresh.

---
Task ID: 11 (main agent)
Task: Phase 1 build + GitHub repo (Dalfino/one-command-hospital) with milestone pushes + portal refresh integration

Work Log:
- Created repo via API; PAT verified (login: Dalfino). Token used inline only (never in .git/config or files); grep-checked before every push (clean).
- Git auth note: `x-access-token:` prefix rejected; `https://Dalfino:<PAT>@github.com/...` works for this fine-grained PAT.
- M0 `b8aea4d`: v0 scaffold pushed (compose stack, corpus, eval 18/20, 4 services).
- M1 `0a109b8`: SMART widget — Vite+React+fhirclient, warm-care UI, ask/sign/escalate. Fixed PostCSS parent-lookup (inline css.postcss config) + duplicated button; vite build GREEN.
- M2 `11bbaa2`: medplum-auth.js (OAuth2 client_credentials + JWT client_assertion RS384, token cache) + /signoff endpoint closing human_action loop; node --check green.
- M3 `ce51fea`: verifier v0.2 — medspaCy ConText polarity map (answer vs source), conflicts flagged, heuristic fallback, engine in /health.
- M4 `406d6d8`: retrieval.py HybridRetriever (alpha·norm(BM25)+(1−α)·cosine, VECTOR_BACKEND/HYBRID_ALPHA envs, honest degradation) + title-boosted chunks + Dockerfile WITH_SBERT ARG. Fixed relative import + comprehension bug pre-push.
- M5 `2c05ca2`: GLYCEMIC-CTRL v1.0 protocol + eval to 52 pairs (42 traced + 10 refusal traps, incl. paraphrase items) + eval loader sync → 98% retrieval (41/42, BM25; misses a10/g02 borderline), CI gate green.
- M6 `f234d29`: portal copied to portal/ (rsync minus node_modules/.next/db/prisma etc.) + portal/README + README status/milestones. `09b92ec` docs fix.
- Portal refresh (Task 10, full-stack-developer subagent): content rewritten to flagship story — hero "librarian robot", how-it-works 7-hop lifecycle, combination (10 repos), 6 improvements, proof+kill criteria, compliance open-items, deployment, roadmap; lint exit 0; agent-browser 1366px+375px: 0 overflow, 0 console errors, counters/tabs/expanders verified; obsolete components removed; metadata retitled ("a Willow Lab research build").
- Whitepaper refresh NOT started this turn (pdf skill chain + script surgery needs its own focused pass) — scheduled next.

Stage Summary:
- REPO LIVE: github.com/Dalfino/one-command-hospital, 8 commits M0-M6 + docs fix, every milestone pushed as requested.
- Phase 1 core landed: SMART widget (build green), JWT auth, ConText verifier, hybrid retrieval, 52-pair eval @ 98%.
- Portal (workspace Next.js app at /) now tells the new story and is verified; copy lives at portal/ in the repo.
- PENDING: whitepaper PDF refresh to match new architecture (next dedicated pass, using persisted scripts in /home/z/my-project/scripts/); eval 52→200; OpenEMR SMART launch registration; user advised to ROTATE the PAT shared in chat.

---
Task ID: 10
Agent: full-stack-developer
Task: Pivot the Willow portal (route /) to the locked flagship story — "Guideline Copilot on the One-Command Hospital" — keeping the Task 6 design system, layout quality, and animation style untouched.

Work Log:
- Read worklog + one-command-hospital repo (README, docs/architecture.md, docs/improvements.md, eval/qa_seed.yaml, eval/report.md, docker-compose.yml, Makefile, git log M1–M5) to source every number honestly: 52 pairs (42 traced + 10 refusal traps), 98% retrieval (41/42, BM25-only, eval/report.md), 80% CI floor, kill criteria (85% grounded / PHI one-strike / >8s median latency / trust <80%), ~20-min boot, 1×≥24GB GPU, port map, licenses, Phase 0 done + Phase 1 items shipped (SMART widget, Bot JWT, ConText verifier v0.2, hybrid BM25+SBERT).
- Rewrote src/components/willow/willow-data.ts as the single content module: NAV_LINKS (7 anchors), HERO_CHIPS (98% retrieval / 52-question exam / 0 PHI to AI), LIFECYCLE_STEPS (7-hop request lifecycle, de-ID gate highlighted), IMPROVEMENTS (6 cards, upstream→ours→verify), COMBINATION (10 repos with Deploy/Harvest/Component/Conformance-CI/Planned dispositions + license footnote), PROOF_METRICS + GRADED_ON + KILL_CRITERIA, COMPLIANCE_TABS (each item flagged done vs OPEN ITEM), MAKE_VERBS + COMPOSE_PROFILES + PORT_ROWS + DEPLOY_FACTS, PHASES with status chips (done/active/planned + per-bullet done checks), RISKS (8 rows aligned to kill criteria: refusal fatigue, retrieval drift, staleness, PHI, hallucination, latency, trust, licenses), REPO_URL, BUILT_ON, DISCLAIMER, FOOTER_COPY ("a Willow Lab research build").
- Components: rewrote hero.tsx (H1 "A librarian robot inside the hospital", terracotta subhead "Guideline Copilot on the One-Command Hospital", zero-PHI subhead, CTAs "Read the architecture"→#how + "View the repo"→GitHub external; chips 98%/52/0), site-nav.tsx (brand "One-Command Hospital — Guideline Copilot · a Willow Lab build", repo CTA, Sheet aria-describedby fix), why-now.tsx (2 a.m. warfarin scenario card + 3 kept industry stats re-captioned "general industry finding"), platform→how-it-works.tsx (kept expandable layer treatment + connector drop-dots; de-ID step gets terracotta pulsing "PHI dies here" chip; non-negotiables banner), products→improvements.tsx (Upstream today / Ours boxes + FlaskConical Verify chips, IdleIcons kept), sources→combination.tsx (10 repo cards with disposition chips), roi→proof.tsx (animated counters 52/98%/10/80%, make-eval strip, 4 kill-criteria cards with pulsing terracotta dots), compliance.tsx (framework+open-items legend; done=forest check, open=amber dashed circle cards), deployment.tsx (one-command code block, Makefile verbs, profile chips, port-map table with min-w-[520px] internal scroll, GPU/air-gapped/~20-min fact cards), roadmap.tsx (status chips Done/In progress/Planned, desktop progress line animates to 3/8, pulsing active node, per-bullet done checks), site-footer.tsx (pine CTA band "Run the hospital yourself" + repo + architecture buttons, GitHub link, advisory-only disclaimer); page.tsx reordered (Hero→Why→How→Combination→Improvements→Proof→Compliance→Deployment→Roadmap→Risks); layout.tsx metadata retitled "One-Command Hospital — Guideline Copilot".
- Removed obsolete platform.tsx/products.tsx/sources.tsx/roi.tsx. Kept willow-* CSS keyframes/classes and motion-primitives untouched.
- Fixed lint regression: eslint was scanning download/one-command-hospital/smart-app/dist (Task 9 Vite build artifact) and failing; added download/research/scripts/mini-services/db/tests to eslint ignores (build artifacts must not be linted). bun run lint → exit 0.
- Verification (agent-browser, desktop 1366×900 + mobile 375×812): title correct; zero console errors, zero page errors (fixed one Radix SheetContent aria-describedby warning en route); all 9 anchored sections present; nav anchor lands at exactly 80px (desktop #how; mobile #proof after Sheet close, sheet closes on nav click); horizontal overflow 0px on both viewports incl. all lifecycle steps expanded (strict per-element scan excluding intentional overflow containers); port table scrolls internally on mobile; compliance tabs switch (EU AI Act: 6 items, 3 OPEN ITEM); lifecycle expanders work (7 steps, aria-expanded toggles); proof counters animate to 52 / 98% / 10 / 80%; deployment facts + port rows (6) verified; roadmap statuses Done/In progress/Planned×2; footer bottom == document bottom on both viewports (11953/11953 desktop, 21140/21140 mobile); ambient blobs/ECG/particles mounted.
- VLM inspection of full-page screenshots (after scroll-triggering all whileInView reveals): desktop 1366 = "NO ISSUES"; mobile 375 = flagged items disproven by DOM ground truth (no overflow/clipping) except expected below-the-fold stat chips on mobile hero — accepted, matches Task 6 pattern. Screenshots at /tmp/task10-*.png, VLM script persisted at scripts/task10_vlm_check.mjs.
- dev.log: transient module-not-found only during mid-write file swaps (old page.tsx ↔ new components), resolved; final compiles clean, GET / → 200.

Stage Summary:
- Portal now tells the locked flagship story end-to-end with design system and ALIVE animations intact; all content traceable to the one-command-hospital repo (no invented numbers; ~20-min boot explicitly labeled "pilot-stage estimate").
- Honesty treatments added: OPEN ITEM markers in compliance tabs, "general industry finding" captions on kept stats, verify chips on every improvement, kill criteria surfaced as a dedicated card row.
- Old "Willow Health AI Suite" fully retired from user-visible copy; "Willow" survives only as "a Willow Lab research build" (permitted). Files: willow-data.ts, hero, site-nav, why-now, how-it-works, improvements, combination, proof, compliance, deployment, roadmap, site-footer, page.tsx, layout.tsx, eslint.config.mjs (+ removed 4 obsolete components).
- Verification green: lint exit 0; desktop+mobile zero console/page errors, zero horizontal overflow, anchors/tabs/expanders/counters/footer-stickiness all pass.
- Note for main agent: whitepaper (download/) still carries the old suite story and is explicitly out of scope here; dist artifacts inside download/one-command-hospital/smart-app are excluded from lint via eslint.config.mjs ignores.

---
Task ID: 12
Agent: main (Super Z)
Task: Clinical-readiness audit + hardening wave M7-M11 (user question: "is everything done and ready for clinical deployment? improvements across smoothness/efficiency/accuracy/infrastructure/security/governance?")

Work Log:
- Audited repo state post-platform-resync: git remote lost, history rewritten locally (UUID commits); all content intact; 0-insertion permission diffs only. No PAT in env (used inline-only last session) → push pending.
- Found + fixed 2 real bugs: ai-mediator Dockerfile never COPYed medplum-auth.js (container would crash on boot); README referenced missing .env.example (created).
- M7 Security: compose network segmentation (internal `data` tier), non-root USER + cap_drop ALL + no-new-privileges + read-only rootfs on all 4 AI services, healthchecks + service_healthy gating, resource limits, per-IP token-bucket rate limits, body caps, security headers (shared zero-dep hardening.py duplicated per service by design), .env.example.
- M8 Governance: hash-chained append-only audit trail (audit.js, genesis→sha256 chain, /audit/verify + verifyChain walk), audit events on answer/signoff/error; mediator v0.3 scrubs the QUESTION text too (raw question was going to LLM path — real PHI gap); docs/governance.md (roles, change control classes, incident severity ladder, kill criteria, EU-AI-Act/FDA/HIPAA posture), docs/model_card.md, docs/security_checklist.md, docs/deployment_readiness.md (Gate 0-5 matrix with explicit NOT-READY verdict + named sign-off block).
- M9 Observability: observe profile (Prometheus :8106, Grafana :8107), prometheus.yml + alert_rules.yml (refusal fatigue >40%, ungrounded answers critical, audit-chain broken critical, p95>8s, 5xx, service down), 8-panel Grafana dashboard; /metrics on all 4 services (zero-dep text exposition, Python + Node mirrors).
- M10 Accuracy: eval/generate_eval.py (deterministic, no RNG) → qa_full.yaml 208 items (52 seed + 63 template + 21 keyword-probe + 21 navigation + 6 edition + 45 hand-verified traps); BM25 trap sanity probe flags vocabulary-overlap traps for review (lmwh-renal top, none actually covered); run_eval.py accepts file arg + separate report_full.md. RESULTS: seed 41/42 = 98%, FULL 146/153 = 95% (gate ≥80% green both).
- M11 Ops: tools/doctor.sh + `make doctor` (docker/env/ports/disk/GPU/secret-hygiene preflight), .github/workflows/ci.yml (eval gates both sets, py_compile, YAML validity, node --check, smart-app build, compose config, gitleaks), TTL+LRU answer cache in guideline-rag, RETRIEVAL_MARGIN ambiguity gate (default 0.02), vLLM --enable-prefix-caching, verifier NLP built once (was per request), Makefile targets observe/eval-full/audit-verify.
- Synced real numbers to README (status banner + milestone table M7-M11) and portal willow-data.ts (hero chips 208/95%, proof metrics 208/95%/55/80%, roadmap bullets) in workspace app + repo portal/ copy; bun run lint exit 0.
- Committed locally: 0875c1f (59 files, +3,485). PUSH PENDING: needs fresh PAT from user (old one shared in chat must be rotated); when provided, reconcile rewritten local history with GitHub M0-M6 history (prefer: re-apply M7-M11 changes on top of remote main to preserve milestone SHAs).

Stage Summary:
- VERDICT DELIVERED: not clinically deployable (research pilot). Blocking opens: real protocols + steward sign-off, live-mode trap refusal + grounding eval (GPU), TLS + pen test, Medplum auth fail-closed, structured logs + off-box shipping, backup/restore drills, load test, regulatory counsel, committee ratification.
- Everything implementable in-sandbox landed: 5 milestones, 2 crash/security bugs fixed, eval 4x, gates/alerts/docs codified. Portal + README carry only real numbers.
