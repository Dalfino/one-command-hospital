#!/usr/bin/env python3
"""Expand the known-answer eval set toward the Phase-1 target (200 questions).

Deterministic (no RNG at all): same corpus in, same qa_full.yaml out.

Composition of the generated set:
  - seed items       : the hand-written 52 from qa_seed.yaml (kept verbatim)
  - template items   : 3 per corpus section, phrased around the section title
  - keyword probes   : 1 per section, built from the section's two most
                       distinctive tokens (local TF minus a global stoplist)
  - navigation items : 1 per section ("which section covers X?")
  - edition items    : 2 per corpus (version-history awareness, improvement #2)
  - refusal traps    : hand-written 45 questions about protocols that do NOT
                       exist in this corpus. Each trap is BM25-probed against
                       the corpus; traps that score high are REPORTED for human
                       review (they may actually be covered — never silently
                       dropped).

Answerable generated items carry no must_contain (they are graded on
retrieval + citation validity); traps carry `refusal: true`.
"""
import re
import pathlib
import collections

import yaml

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
GUIDELINES = ROOT / "guidelines"

WORD = re.compile(r"[a-z0-9]+")
SECTION = re.compile(r"^##\s+(\d+)\.\s+(.+)$", re.M)

STOP = set("""the a an and or of to in for with on is are be was were must may should
can it its this that by at as from if when any all patient patients procedure
before after not no our we us their they there these those will shall than then
once per into over under between during within without each other more most less
least same own very just also only such being been has have had do does did done
which what when where who whom whose why how protocol section guidance guideline
guidelines document edition effective history author owner applies""".split())

SHORT = {
    "ANTICOAG-BRIDGE": "peri-operative anticoagulation bridging",
    "SEPSIS-SCR": "sepsis screening",
    "GLYCEMIC-CTRL": "inpatient glycemic control",
}

PREFIX = {
    "ANTICOAG-BRIDGE": "a",
    "SEPSIS-SCR": "s",
    "GLYCEMIC-CTRL": "g",
}

# ── Refusal traps ────────────────────────────────────────────────────────────
# Every entry below was hand-verified against all three corpora (as of
# manifest editions) to NOT be answerable from them. Near-miss traps that share
# vocabulary with the corpus are intentional — they are the interesting ones.
TRAPS = [
    # DOACs — explicitly out of ANTICOAG-BRIDGE scope (§1)
    ("What is the peri-operative management of apixaban?", "doac-scope"),
    ("How should rivaroxaban be interrupted before surgery?", "doac-scope"),
    ("Which DOAC needs no interruption for cataract surgery?", "doac-scope"),
    ("How do we manage dabigatran around a hip replacement?", "doac-scope"),
    # Other anticoagulation gaps
    ("What is the pediatric warfarin bridging protocol?", "peds-scope"),
    ("How should anticoagulation be bridged for emergency surgery?", "emergency-scope"),
    ("What is the protocol for warfarin reversal in intracranial hemorrhage?", "emergency-reversal"),
    ("Which P2Y12 inhibitors should be held before surgery, and for how long?", "antiplatelet"),
    ("How long should clopidogrel be stopped before a colonoscopy?", "antiplatelet"),
    ("What is the bridging plan for a patient with antiphospholipid syndrome?", "aps"),
    ("How is heparin-induced thrombocytopenia managed peri-operatively?", "hit"),
    ("What is the unfractionated heparin infusion nomogram?", "ufh"),
    ("Do I need to dose-adjust low molecular weight heparin in renal impairment?", "lmwh-renal"),
    ("Can a patient on warfarin self-test their INR at home before surgery?", "inr-home"),
    ("Does warfarin interact with cranberry juice or amiodarone?", "interactions"),
    ("Is pharmacogenomic testing recommended before warfarin initiation?", "pgx"),
    ("How should warfarin be managed during pregnancy?", "pregnancy"),
    ("What CHA2DS2-VASc score triggers anticoagulation in atrial fibrillation?", "chads"),
    # Sepsis gaps
    ("Which antibiotics are first-line for sepsis from a urinary source?", "abx-choice"),
    ("When should vasopressors be started in septic shock?", "vasopressors"),
    ("What is the role of procalcitonin in sepsis screening?", "pct"),
    ("How is sepsis screened in the pediatric ICU?", "peds-scope"),
    ("What are the sepsis screening criteria for neonates?", "neonatal"),
    ("When should source control such as drainage be performed in sepsis?", "source-control"),
    ("Are corticosteroids recommended in refractory septic shock?", "steroids-sepsis"),
    ("What follow-up is arranged for sepsis survivors after discharge?", "post-sepsis"),
    ("How often should blood cultures be repeated during ongoing therapy?", "culture-repeat"),
    ("What is the protocol for neutropenic sepsis on the ward?", "neutropenic"),
    # Glycemic gaps
    ("How do we manage diabetic ketoacidosis on the general ward?", "dka-scope"),
    ("What is the blood glucose target for patients in the ICU?", "icu-scope"),
    ("How is hyperosmolar hyperglycemic state managed?", "hhs"),
    ("How should insulin be titrated for outpatient type 2 diabetes?", "outpatient"),
    ("What are the blood glucose targets for gestational diabetes managed in the community?", "pregnancy-gdm"),
    ("How is neonatal hypoglycemia treated in the delivery suite?", "neonatal"),
    ("Should continuous glucose monitors be used for hospital inpatients?", "cgm"),
    ("How do we manage steroid-induced hyperglycemia?", "steroid-hyperglycemia"),
    ("What is the metformin dosing schedule in chronic kidney disease?", "metformin-ckd"),
    ("Should metformin be screened for lactic acidosis risk before admission?", "metformin-la"),
    ("What is the protocol for managing inpatient insulin pumps?", "pump"),
    ("What hypoglycemia pathway applies to a post-bariatric surgery patient?", "bariatric"),
    ("Should sulfonylureas be held on the morning of surgery?", "sulfonylurea"),
    ("How is hypoglycemia treated in a patient during hemodialysis?", "dialysis"),
    # Cross-cutting
    ("What is the antibiotic prophylaxis regimen for joint replacement surgery?", "surgical-prophylaxis"),
    ("How should COVID-19 be treated on general wards?", "covid"),
    ("What is the protocol for MRSA decolonization before admission?", "mrsa"),
]


def load_manifest():
    return yaml.safe_load((GUIDELINES / "manifest.yaml").read_text())["corpus"]


def parse_sections(entry):
    text = (GUIDELINES / entry["file"]).read_text()
    parts = re.split(r"^(##\s+\d+\..+)$", text, flags=re.M)
    out = []
    for i in range(1, len(parts), 2):
        block = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        m = re.match(r"##\s+(\d+)\.\s*(.+)", block)
        out.append({"num": m.group(1), "title": m.group(2).strip(),
                    "block": block, "body": body})
    return out


def distinctive_tokens(body, global_counts):
    counts = collections.Counter(WORD.findall(body.lower()))
    scored = []
    for tok, n in counts.items():
        if tok in STOP or len(tok) < 4 or tok.isdigit():
            continue
        # local frequency, discounted by corpus-wide frequency: distinctive = rare elsewhere
        scored.append((n / (1 + global_counts.get(tok, 0)), tok))
    scored.sort(reverse=True)
    return [t for _, t in scored]


def main():
    manifest = load_manifest()

    # global token counts across all sections (for distinctiveness)
    global_counts = collections.Counter()
    per_corpus = {}
    for e in manifest:
        secs = parse_sections(e)
        per_corpus[e["id"]] = secs
        for s in secs:
            global_counts.update(set(WORD.findall((s["block"] + s["body"]).lower())))

    items = []
    n = {"tpl": 0, "kw": 0, "nav": 0, "ver": 0}

    for e in manifest:
        cid, short = e["id"], SHORT[e["id"]]
        for s in per_corpus[cid]:
            topic = s["title"].rstrip(".").strip()
            topic_lc = topic[0].lower() + topic[1:] if topic else topic
            n["tpl"] += 1
            items.append({
                "id": f'{PREFIX[cid]}-tpl{n["tpl"]}',
                "question": f'What does the {short} protocol say about {topic_lc}?',
                "expected_corpus": cid, "expected_section": s["num"],
            })
            n["tpl"] += 1
            items.append({
                "id": f'{PREFIX[cid]}-tpl{n["tpl"]}',
                "question": f'Per our guidelines, summarize the current guidance on {topic_lc}.',
                "expected_corpus": cid, "expected_section": s["num"],
            })
            n["tpl"] += 1
            items.append({
                "id": f'{PREFIX[cid]}-tpl{n["tpl"]}',
                "question": f'A colleague asks about {topic_lc} — what do we tell them to do?',
                "expected_corpus": cid, "expected_section": s["num"],
            })
            n["nav"] += 1
            items.append({
                "id": f'{PREFIX[cid]}-nav{n["nav"]}',
                "question": f'Which section of the {short} protocol covers {topic_lc}?',
                "expected_corpus": cid, "expected_section": s["num"],
            })
            toks = distinctive_tokens(s["block"] + s["body"], global_counts)[:2]
            if len(toks) == 2:
                n["kw"] += 1
                items.append({
                    "id": f'{PREFIX[cid]}-kw{n["kw"]}',
                    "question": f'Our ward is asking about {toks[0]} and {toks[1]} — what do the {short} guidelines say?',
                    "expected_corpus": cid, "expected_section": s["num"],
                })

        # edition-awareness items (improvement #2)
        n["ver"] += 1
        items.append({
            "id": f'{PREFIX[cid]}-ver{n["ver"]}',
            "question": f'What changed in the most recent edition of the {short} protocol?',
            "expected_corpus": cid, "expected_section": _version_section(per_corpus[cid]),
        })
        n["ver"] += 1
        items.append({
            "id": f'{PREFIX[cid]}-ver{n["ver"]}',
            "question": f'When did the current {short} protocol take effect, and how do we know it is still active?',
            "expected_corpus": cid, "expected_section": _version_section(per_corpus[cid]),
        })

    seed = yaml.safe_load((HERE / "qa_seed.yaml").read_text())["questions"]
    for t, (q, tag) in enumerate(TRAPS):
        items.append({"id": f"rt-gen{t + 1:02d}", "question": q,
                      "refusal": True, "trap_tag": tag})

    full = {"questions": seed + items}
    out = HERE / "qa_full.yaml"
    header = (
        "# Generated eval set — DO NOT HAND-EDIT (run eval/generate_eval.py to rebuild).\n"
        f"# Composition: {len(seed)} hand-written seed items + "
        f"{n['tpl']} template + {n['kw']} keyword-probe + {n['nav']} navigation + "
        f"{n['ver']} edition + {len(TRAPS)} refusal traps = {len(full['questions'])} items.\n"
        "# Answerable generated items are graded on retrieval + citation validity;\n"
        "# refusal traps are graded on the live service refusing (full mode).\n"
    )
    body = yaml.safe_dump(full, sort_keys=False, allow_unicode=True, width=100)
    out.write_text(header + body)

    print(f"seed={len(seed)} tpl={n['tpl']} kw={n['kw']} nav={n['nav']} "
          f"ver={n['ver']} traps={len(TRAPS)}  →  TOTAL={len(full['questions'])}")
    print(f"wrote {out}")

    # Trap coverage sanity: BM25-probe each trap; report high scorers for review.
    try:
        from rank_bm25 import BM25Okapi
        corpus_chunks = []
        for e in manifest:
            for s in per_corpus[e["id"]]:
                corpus_chunks.append(
                    f"[{e['title']} — §{s['num']} {s['title']}] (edition {e['edition']})\n{s['block']}\n{s['body']}"
                )
        bm25 = BM25Okapi([WORD.findall(c.lower()) for c in corpus_chunks])
        import statistics
        all_scores = []
        for t, (q, tag) in enumerate(TRAPS):
            scores = bm25.get_scores(WORD.findall(q.lower()))
            all_scores.append(max(scores))
        hi = sorted(zip(all_scores, TRAPS), reverse=True)[:5]
        thresh = statistics.median(all_scores)
        print(f"\ntrap BM25 max-score: median={thresh:.2f} max={max(all_scores):.2f}")
        print("top-scoring traps (review these — they share vocabulary with the corpus):")
        for s, (q, tag) in hi:
            flag = "  ⚠ REVIEW" if s > thresh + 4 else ""
            print(f"  {s:6.2f}  [{tag}] {q[:70]}{flag}")
    except ImportError:
        print("(rank_bm25 not installed — trap sanity probe skipped)")


def _version_section(sections):
    for s in sections:
        if "version" in s["title"].lower() or "history" in s["title"].lower():
            return s["num"]
    # fall back to the last section
    return sections[-1]["num"]


if __name__ == "__main__":
    main()
