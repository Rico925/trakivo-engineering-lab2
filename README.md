# TRAKIVO Engineering Experiment Lab (prototype v0.2)

This package is refocused on the first TRAKIVO pillar: a narrow, reproducible educational experiment. The UI supports a single setup parameter, records a prediction and hypothesis before running, compares the deterministic model result with a baseline, and saves/reopens versions in browser-local storage. Groq is the default optional AI provider (BLACKBOX AI can also be selected) and is used only to explain the supplied result, never to produce the numerical output.

## What the first scenario models

**Final-drive ratio trade-off** with fixed illustrative inputs: engine torque 300 N·m, selected gear ratio 2.00:1, drivetrain efficiency 0.90, wheel radius 0.330 m, and engine speed 8,000 RPM. It calculates wheel torque, idealised tractive force, and theoretical speed at that fixed RPM. These are model outputs, not measurements or validated real-vehicle predictions. Aerodynamics, torque curve, tyre slip, gear shifts, gradients, and other real-world effects are not modelled. It does not predict lap time, grip, tyre wear, reliability, or safety.

The parameter range is 2.5 to 5.0 (dimensionless), baseline 3.5. The formula and assumptions are in `src/python/brain/experiment_model.py`.

## Run locally

1. From the repository root, create and activate a virtual environment, then start the Python API:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r src/python/brain/requirements.txt
   cp .env.example .env  # optional; edit .env to add your private Groq key
   PYTHONPATH=src/python python -m uvicorn brain.api:app --host 127.0.0.1 --port 8000
   ```
2. In a second terminal, start the frontend:
   ```bash
   cd frontend
   cp .env.example .env  # optional; only needed to override the default API URL
   npm install
   npm run dev
   ```
3. Open the Vite local URL printed in the terminal.

## Optional AI explanation with Groq (or BLACKBOX AI)

The engineering calculation does not need an AI key. To enable explanations, copy `.env.example` to `.env` and add your own Groq API key:

```dotenv
AI_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Run the backend from `src/python/brain` as shown above. `python-dotenv` loads the local `.env` file for development. Keep `.env` private and never put the key in frontend variables, React code, screenshots, or source control. The default model is configurable with `GROQ_MODEL`; confirm current model availability and rate limits in your Groq account.

To use BLACKBOX AI instead, set `AI_PROVIDER=blackbox` and configure `BLACKBOX_API_KEY`, `BLACKBOX_MODEL`, and `BLACKBOX_BASE_URL` in `.env`. Only the selected provider is called. The API key remains on the backend. Without a key, the deterministic experiment still runs and the explanation endpoint reports that AI is not configured.

The provider is an explanation layer only. It does not calculate or validate engineering outputs. The numerical model remains deterministic and currently illustrative.

## Validation

From the repository root, with the backend dependencies installed:

```bash
python -m pytest -q
```

For the frontend production type-check/build:

```bash
cd frontend
npm install
npm run build
```

The frontend dependencies are pinned to compatible versions rather than `latest`; commit the generated `frontend/package-lock.json` after a successful install to make installs reproducible.

## Known limitations and not-yet-built requirements

- This is a prototype model with documented illustrative constants, not validated against reference vehicle data or reviewed by a motorsport engineer. Do not use for real setup decisions.
- Saved experiments use `localStorage` on the current browser only. There is no account, Supabase persistence, server-side immutable audit log, or cross-device sync yet.
- The app captures the prediction before the user can run the model, but it does not yet cryptographically lock that prediction or preserve a server audit trail.
- The AI explanation endpoint is tested with mocked provider responses only. A live Groq or BLACKBOX AI account/key has not been tested in this environment.
- The legacy Node/gRPC telemetry scaffold remains in `src/node`, `src/cpp`, and `src/proto`; it is not used by the Engineering Experiment Lab UI and should not be treated as part of this end-to-end workflow.
- No full-stack deployment or production security review has been performed.

## Website and database boundary

The main website is the React/Vite app in `frontend/`. The separate knowledge-graph HTML concept is kept in `examples/knowledge-graph-concept.html` as a visual prototype only. It uses local illustrative examples and is not connected to Supabase, pgvector, real-time telemetry, or an AI/RAG pipeline. The SQL starter schema in `supabase/schema.sql` is a separate foundation; the application does not yet persist experiment records to it.

## Telemetry import and lap comparison (prototype)

The Python API now exposes a first CSV-to-comparison workflow. See [`TELEMETRY_SCHEMA.md`](TELEMETRY_SCHEMA.md) for the normalized contract and [`examples/demo_telemetry.csv`](examples/demo_telemetry.csv) for synthetic sample data:

- `POST /telemetry/import` accepts JSON `{ "csv_text": "..." }`, validates and normalizes supported columns, and returns a lap summary without returning the full sample payload.
- `POST /telemetry/compare` accepts `{ "csv_text": "...", "reference_lap": "1.0", "comparison_lap": "2.0" }` and returns a 101-point speed comparison interpolated onto the shared distance range.
- The frontend Telemetry Analysis panel can select a CSV, review detected laps and compare two laps.

### Normalized telemetry schema v1.0

| Channel | Normalized name | Expected unit / meaning |
| --- | --- | --- |
| Time | `time_s` | Seconds; retained for future time-based workflows |
| Distance | `distance_m` | Metres; required for distance-aligned comparison |
| Speed | `speed_kmh` | Kilometres per hour; required |
| Throttle | `throttle_pct` | Percentage-like source values; units are not auto-converted |
| Brake | `brake_pct` | Percentage-like source values; units are not auto-converted |
| Lap | `lap` / internal `lap_id` | Source lap marker where provided; otherwise distance reset inference |
| GPS | `latitude`, `longitude` | Source coordinates, if present |

Recognized aliases include `speed`, `speed_kph`, `vehicle_speed`, `distance`, `lap_distance`, `throttle`, `accelerator`, `brake`, `lap_number`, and common unit-labelled headers. Units are not guessed or converted. Imported files are treated as user-provided data, not independently authenticated measurements.

### Prototype boundaries

- CSV limit: 10 MB and 250,000 non-empty rows.
- Lap comparison requires distance and speed samples for both laps. Time-only CSVs can be imported for inspection but cannot yet be distance-aligned.
- Lap boundaries are read from a lap column when present. Otherwise, a drop in distance by more than one metre is used as an **inferred** lap boundary.
- Comparison uses linear interpolation over overlapping distance, not sector-aware synchronization, GPS map matching, sensor calibration, or professional telemetry timing algorithms.
- Experiment history remains browser-local. Durable database-backed projects and Decision Replay are not implemented in this milestone.
- The gearing model remains an illustrative deterministic calculation, not a validated vehicle simulator. AI explanations remain optional and separate from numerical analysis.

### API smoke examples

```bash
curl -X POST http://127.0.0.1:8000/telemetry/import \
  -H 'Content-Type: application/json' \
  -d '{"csv_text":"lap,distance_m,speed_kmh\\n1,0,40\\n1,50,60\\n2,0,42\\n2,50,65\\n"}'
```

Run tests from the project root with `python -m pytest -q`.
