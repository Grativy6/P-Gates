# P-Gates repository guidance

## Corpus authority order

Treat `PAL Package/` as a versioned corpus, never as one flattened source.

1. `PPP_Kernel_v0.3_Supplementary_Integration_Draft.pdf` is the current public, independently verifiable integration record and the starting map.
2. `PAL_Spine_v1.3_Publish_Ready_Structural_Edition.pdf` controls PAL structural definitions.
3. `PECAN_v1.0_Public_Protocol_Specification.pdf` controls consequential crossing, authorization, provenance, receipts, and anti-backflow rules.
4. `PEA_Core_v1.0_Public_Ethical_Review_Specification.pdf` controls the declared ethical review layer.
5. Component specifications control over PPP within their own layer. PPP does not silently amend them.

## SEED status

`SEED_v0.1_Long_Form_Working_Draft.pdf` is chronologically newer than PPP v0.3 and is the primary development reference for SEED-specific concepts. It remains a working draft. PPP v0.3 controls public provenance and integration. Do not represent experimental SEED v0.1 additions as canonical or publicly adopted without an explicit source label.

## Privacy boundary

`Riemann_Ledger_v0.56_Private_Work_Draft_C3_Split_and_Handoff.pdf` is private. Do not read its substantive content for app work. Do not copy it into public prompts, fixtures, exports, repository documentation, tests, screenshots, or application UI. It does not prove the Riemann Hypothesis or PAL physically true.

## MVP scope

Keep P-Gates an analysis and drafting aid, not a decision-maker. The mock MVP has one input, one built-in facial-recognition example, PAL/PECAN/PEA/SEED panels, phrase-level trace, and Markdown/JSON export. It must preserve uncertainty and state that accountable human judgment remains required.

## Coding constraints

- Never modify corpus documents.
- Keep framework rules in separate reference/manifest files, not buried in application code.
- Use typed Pydantic schemas and tests.
- Mock mode is the default; no live OpenAI provider is included yet.
- A future live provider must read `OPENAI_API_KEY` only from the runtime environment; never log, commit, display, or hard-code it.
- Do not claim empirical validation, legal authority, ethical permission, or an autonomous institutional decision.
