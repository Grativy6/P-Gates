# P-Gates: PPP Route Auditor

P-Gates is a small mock-mode analysis and drafting aid for keeping a report's evidence, consequential use, affected burdens, and human-facing explanation distinct. It is not a decision-maker and does not create legal, ethical, or institutional authority.

## Demo

The built-in fictional facial-recognition example shows how “possible candidate” and “identity unverified” can be compressed into “identified as suspect.” The app displays PAL, PECAN, PEA, and SEED panels plus a phrase-level trace and JSON/Markdown export.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Testing

Run the full test suite locally with:

```powershell
python -m pytest
```

GitHub Actions runs the same mocked, offline suite for pushes and pull requests to `main`. CI does not make live API requests and does not require `OPENAI_API_KEY`.

## Providers

Mock mode is the default and makes no network request. OpenAI live mode uses the Responses API with a typed structured-output schema. It reads `OPENAI_API_KEY` only from the server process environment; the browser never receives it. Set the provider selector to **OpenAI live mode** to make a live request.

The live provider sends only the submitted text and the four short MVP references under `framework/mvp/`. It does not send the corpus or the private Riemann Ledger. It records the provider, returned model ID, timestamp, framework-manifest version, and token counts when supplied by the API.

For diagnostics, the live path first uses a normal Responses API call with strict JSON Schema, then validates the returned JSON locally. It preserves safe metadata only: request/response IDs, HTTP and response status when available, returned model, token counts, JSON shape, incomplete/refusal state, and validation locations. It never preserves logs of the API key, headers, framework prompt, full user text, or private corpus content.

## Corpus boundary

`PAL Package/` is a source corpus and has not been modified. The Riemann Ledger is private and is excluded from application prompts, fixtures, exports, UI, tests, and this README.
