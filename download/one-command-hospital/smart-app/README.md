# SMART on FHIR Widget (stub — Phase 1)

The in-EHR surface: a clinician highlights a note or opens the app from the
OpenEMR patient context, types a question, and sees the cited answer.

## Planned shape

- React + `@medplum/react` components; OIDC via Medplum; SMART App Launch
  (`launch/patient` + `launch/encounter`) from OpenEMR's FHIR context.
- Calls `ai-mediator /process` with `{question, contextText, patientId, userId}`.
- Renders: answer (or refusal), citations as chips (`ANTICOAG-BRIDGE §3 · v3.0`),
  grounding badge from the verifier, and a **Sign / Escalate** pair that closes
  the audit loop (`human_action` in the FHIR Communication payload).

## Acceptance for Phase 1

1. Launches inside OpenEMR iframe with patient context.
2. One question → cited answer rendered in < 5 s (warm cache).
3. Sign-off writes `human_action: signed_off` back to the Communication.
