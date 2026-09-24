# vLLM serving profile — guided decoding (ADOPT, docs/tech_radar.md)

This directory carries the ops-facing half of the constrained-decoding
ADOPT item: the answer schema the generator is mechanically held to, plus
the flags that turn the constraint on.

## What constrains what

| Layer | Mechanism | Lives in |
|---|---|---|
| Decoding (mechanical) | `guided_json` request field — the model **cannot** emit anything except the schema | `services/guideline-rag/app/guided_decoding.py` → merged into `/chat/completions` body by `main.call_llm` |
| Prompt (intent) | Instructions mirror the schema so intent and constraint agree | `main.build_prompt(guided=True)` |
| Parse (fail-closed) | `parse_guided()` strictly validates the JSON; `covered=false` → refusal; unparseable JSON from a server that *tried* to constrain → refusal | `main.answer` post-parse handling |

The schema file `guided_answer_schema.json` is a **mirror** of the Python
constant for review/ops tooling. A unit test
(`tests/unit/test_guided_decoding.py`) asserts the copies never drift —
edit the Python constant, then re-mirror, never the other way round.

## Turning it on / off / renaming the wire field

Environment variables on the `guideline-rag` service:

```bash
GUIDED_DECODING=1            # default; 0/false/no/off = legacy text contract
GUIDED_JSON_FIELD=guided_json  # vLLM's request field for schema-guided decoding
```

Notes for the GPU host session (`make up-gpu`):

- Current vLLM releases accept `guided_json` on `/v1/chat/completions`
  (xgrammar/outlines backends). Newer builds group the same feature under
  a `structured_outputs` object; if your vLLM deprecation-warns on
  `guided_json`, set `GUIDED_JSON_FIELD=structured_outputs` and check
  whether the schema needs wrapping (`{"schema": ...}`) per your vLLM
  version's docs — no code change needed either way.
- Servers that silently ignore the field degrade gracefully: the answer
  comes back as free text, `parse_guided()` returns `None`, and the legacy
  cite-or-refuse text contract runs unchanged.
- The mock/extractive mode (no LLM reachable) never produces guided JSON;
  eval numbers are therefore generator-mode-agnostic by construction.
