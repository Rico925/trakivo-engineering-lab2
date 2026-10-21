# TRAKIVO telemetry schema v1.0

## Purpose

A small, explicit normalized contract for the first telemetry analysis workflow. It is designed for educational CSVs and future extension, not as a claim of compatibility with all logger exports.

## Channels

| Normalized field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `time_s` | number or null | no | Source time in seconds; not converted automatically |
| `distance_m` | number or null | one of distance/time | Source distance in metres; needed for current lap comparison |
| `speed_kmh` | number | yes | Source speed in km/h; values are not converted automatically |
| `throttle_pct` | number or null | no | Source throttle value; scale and units remain as provided |
| `brake_pct` | number or null | no | Source brake value; scale and units remain as provided |
| `lap_id` | number-like value | generated | Source lap marker or inferred lap index |
| `latitude` | number or null | no | GPS latitude if present |
| `longitude` | number or null | no | GPS longitude if present |

## API

- `POST /telemetry/import`: request `{ "csv_text": "..." }`; response includes schema version, evidence label, detected channels, lap summaries and row count. Raw normalized samples are intentionally omitted from this summary response.
- `POST /telemetry/compare`: request `{ "csv_text": "...", "reference_lap": "1.0", "comparison_lap": "2.0" }`; response includes comparison summary and a 101-point trace.

## Evidence and limitations

An imported file is labelled `MEASURED (user-imported; source not independently verified)`. Derived comparison outputs are labelled `CALCULATED from user-imported telemetry`. This is provenance labelling, not validation of the file's authenticity or sensor quality. The current alignment uses linear interpolation over overlapping distance. No lap time, grip, tyre wear, setup recommendation, or vehicle safety claim is produced.
