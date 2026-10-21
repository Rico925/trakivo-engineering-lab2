# TRAKIVO demo video script (about 2 minutes)

## Recording checklist

- Start the Python API and frontend before recording.
- Use only `examples/demo_telemetry.csv` or other synthetic/permitted data.
- Hide terminal environment variables and never show `.env` or an API key.
- If Groq is not configured, demonstrate the deterministic experiment and telemetry workflow without AI. Do not fake a successful AI call.
- Keep the browser address bar visible briefly so viewers understand this is a local prototype.

## Narration and screen plan

**0:00–0:15 | Problem and scope**

“TRAKIVO is an early engineering-learning prototype. The goal is to make the reasoning behind a setup experiment traceable: what we expected, what the model calculated, what the data shows, and what remains unknown. This is an educational prototype, not a validated vehicle simulator.”

**0:15–0:45 | Engineering Experiment Lab**

Show the final-drive ratio slider. Enter or retain a hypothesis and prediction, then run the experiment. Point to the baseline comparison and the SIMULATED evidence label.

“The current deterministic model explores a simplified gearing trade-off using declared fixed assumptions. It calculates wheel torque, idealised tractive force, and theoretical speed at fixed RPM. It does not estimate lap time or vehicle safety.”

**0:45–1:20 | Telemetry import and comparison**

Import `examples/demo_telemetry.csv`. Show detected laps, then compare two different laps. Explain that speed is linearly interpolated over the overlapping distance range.

“This workflow reads a supported CSV, reports its detected channels and laps, and compares speed over shared distance. The data is treated as user-provided and its authenticity is not independently verified.”

**1:20–1:40 | Decision record**

Save the current experiment, add a conclusion, then reopen it from local history. Explain that history is browser-local and not synced to a database.

**1:40–1:55 | Optional AI explanation**

If a real Groq key is configured, request an explanation and show the response. Explain that AI interprets supplied evidence and does not produce the deterministic numerical result. If the provider is unavailable, show the clear error/fallback instead of fabricating a response.

**1:55–2:05 | Roadmap and honesty**

“Next steps are repeatable frontend builds, durable project storage, deeper telemetry validation, and engineering validation against permitted reference data. The knowledge-graph SQL is a starter schema and is not yet connected to this app.”
