# TRAKIVO test report

## Checks run in this package revision

- Python test suite: **14 passed** (`python -m pytest -q`).
- Package-style API import: **passed** (`PYTHONPATH=src/python python -c "from brain.api import app; print(app.title)"`).
- Python bytecode compilation: **passed** (`python -m compileall -q src/python/brain`).
- Node gateway syntax check: **passed**.
- Node gateway tests: **2 passed**.
- Frontend dependency installation/build: **not verified in this environment**. `npm install` timed out before completion; therefore no claim is made that the React production build succeeds.
- Live Groq API: **not tested**. Provider tests use mocked responses and no real API key.
- Supabase schema: **not applied to a live Supabase project** and not integrated into the running app.
- Browser end-to-end testing: **not performed**.

## Known limitations

- Gearing outputs come from a simplified illustrative model, not a validated vehicle model.
- Telemetry CSV parsing and distance-aligned interpolation are prototype analysis, not professional logger validation or timing software.
- Experiment history is stored in browser `localStorage`, not a database or cross-device account.
- The knowledge-graph HTML is a local mockup. Search filters sample records; event archiving is page-local and does not create a permanent verified case study.
- Node/C++/gRPC files are legacy scaffolding and are not part of the current frontend-to-Python workflow.
