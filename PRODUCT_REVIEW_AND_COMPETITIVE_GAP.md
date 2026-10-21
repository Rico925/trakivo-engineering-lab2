# TRAKIVO product and code re-review

**Review date:** 20 October 2026  
**Basis:** current prototype source, TRAKIVO Engineering/AI/Data Rules guide, TRAKIVO focused PRD, earlier VECTERA PRD, and public product documentation reviewed for this pass.

## Executive verdict

The project has a promising learning workflow, but it is not yet a differentiated motorsport engineering platform. It is currently a polished single-scenario educational calculator with browser-local history and an optional AI explanation. The strongest idea is not “AI explains a car”; it is the repeatable learning loop: **question → hypothesis → prediction → controlled change → deterministic model → evidence-based explanation → learner conclusion → preserved experiment**.

Keep the three-pillar direction:
1. Engineering Experiment Lab — first and primary workflow.
2. Scenario Prediction Lab — later, reusing the same model/data contract.
3. Engineering Decision Replay — saved versions, comparisons, assumptions, and reproducibility.

Failed and unexpected results should remain a shared capability, not a fourth pillar in the first release.

## Code review findings

### Fixed in this revision
- Added configurable OpenAI-compatible AI provider support: Groq is the default, and BLACKBOX AI remains selectable.
- The backend reads `AI_PROVIDER` plus the selected provider credentials/model/base URL (`GROQ_API_KEY` / `GROQ_MODEL` / `GROQ_BASE_URL`, or the corresponding `BLACKBOX_*` variables); no key is placed in frontend code or bundled in this ZIP.
- The selected model ID is configurable and must be checked against the user's provider account access and current catalogue.
- The explanation endpoint forwards only an allowlist of structured experiment fields instead of the entire client-provided object.
- The explanation remains optional. Deterministic model output works when the key is absent or the provider fails.
- Removed the legacy Groq SDK/key read from the old telemetry helper and removed its fabricated numeric confidence values.
- Added `.env.example`, secret/build-artifact exclusions in `.gitignore`, and mocked provider tests. Tests do not use a real API key or make a live provider call.

### Verified in this environment
- Python syntax checks passed.
- Node syntax checks passed.
- Engineering model tests passed, including baseline, direction of trade-off, parameter-range rejection, and required prediction/hypothesis.
- Provider tests passed for no-key fallback, configured endpoint construction, evidence allowlisting, and not forwarding the fake test key into the prompt.
- Dependency-free smoke checks passed.

### Not verified / must not be claimed
- A live provider API request was not made. Account access, model availability, quotas, billing, and exact model identifier still need confirmation in the user's account.
- The frontend production build could not be repeated in this clean extracted environment because npm dependency installation timed out and `react` was therefore unavailable. The user previously reported a successful local TypeScript/Vite build; this re-review does not independently reproduce that build.
- `package.json` still uses `latest` dependency tags and there is no lockfile in this package. This makes installs non-reproducible. Pin exact tested versions and commit a lockfile before a competition submission.
- Experiment history uses browser `localStorage`, not Supabase or server-side storage. It is not a durable, shared, immutable audit record.
- The Node/gRPC/C++ telemetry scaffold remains legacy and is not part of the current UI-to-model workflow. Do not demo it as integrated or production-ready.
- The gearing model is educational arithmetic with assumed constants. It has not been validated against a vehicle, reference cases, or an engineer's review.

## Engineering model concerns

The model assumes constant engine torque at 8,000 RPM, a fixed 2.00:1 gear ratio, 90% drivetrain efficiency, and 0.330 m effective wheel radius. It calculates wheel torque, idealised tractive force, and theoretical speed at fixed RPM. It does not model engine torque curves, tyre slip, drag, gear shifts, gradient, or lap time.

That is acceptable as a narrowly scoped teaching example if it is labelled honestly. It is not yet a vehicle-dynamics simulator, nor evidence of real-world performance. Do not imply that a ratio change will improve a real car without vehicle-specific data and validation.

## Competitive landscape: adjacent alternatives, not a complete market census

| Alternative | Publicly described strength | TRAKIVO implication |
|---|---|---|
| Formula Lab | Motorsport engineering education positioned around real scenarios and industry experience. | Do not compete on course content alone. Give learners an interactive experiment they can run, inspect, and revisit. |
| Formula Bharat Academy | Virtual and on-site education for Formula Student and real-world engineering. | India-specific Formula Student students are a credible early user group to interview and pilot with. The product needs educator/team workflows to complement courses and workshops. |
| MoTeC i2 | Deep logged-data analysis, plots, overlays, reports, maths channels, track analysis, and video/data integration. | Do not attempt to beat mature telemetry analysis software on channel count or professional analysis. TRAKIVO's early value should be structured learning, hypothesis/prediction discipline, and model transparency. |
| Marple | High-frequency motorsport/automotive data analysis and shared team data; publicly offers Formula Student teams access through a sponsorship programme. | Telemetry analysis is already a mature need. TRAKIVO must make learning and reasoning traceable rather than merely adding charts. |
| Race Technology Analysis | Data logger analysis, lap-time/speed calculations, video/data analysis, user-defined maths and simulation features. | A generic dashboard or simple numerical calculator will not be enough to stand out. |
| AiM RaceStudio 3 Analysis | Session/lap analysis, data-video integration, track maps, maths channels, and reports. | A generic telemetry dashboard is not a strong differentiator. Build a workflow that teaches why a result follows from explicit assumptions and what remains unknown. |

These products do not all serve exactly the same job or audience. Treat them as adjacent alternatives and interview users before declaring a direct competitive advantage.

Sources reviewed:
- Groq API documentation: https://console.groq.com/docs/api-reference and https://console.groq.com/docs/quickstart. BLACKBOX AI documentation remains relevant when `AI_PROVIDER=blackbox` is selected: https://docs.blackbox.ai/api-reference/authentication and https://docs.blackbox.ai/api-reference/introduction
- Formula Lab: https://formulalab.io/
- Formula Bharat Academy: https://formulabharat.com/programs/academy/
- MoTeC i2: https://motec.com.au/products/i2
- Marple for Students: https://www.marpledata.com/marple-for-students
- Race Technology Analysis: https://server.race-technology.com/gb/racing/software/analysis-software
- AiM RaceStudio 3 Analysis documentation: https://www.aim-sportline.com/docs/racestudio3/manual/html/analysis.html

## Best improvement direction

### Priority 1: make the first experiment educationally meaningful
- Explain what a final-drive ratio is in plain language, with a simple drivetrain diagram or worked example.
- Show the formula chain and units behind each output, not just the final values.
- Ask the learner to explain *why* they predicted a result, not only type a prediction.
- After the run, explicitly compare prediction with result: matched, partially matched, contradicted, or cannot determine. This classification must be deterministic or learner-selected, not invented by the model.
- Let the learner record an unexpected/neutral result and what they would test next.

### Priority 2: make the model defensible
- Add hand-calculated reference cases and invariant/property tests (e.g. higher final drive increases calculated wheel torque under the fixed assumptions and reduces theoretical speed at fixed engine RPM).
- Add an engineer-reviewed validation note and state what reference source was used.
- Use sensible precision and keep units adjacent to values.
- Do not show confidence percentages until a calibrated, evaluated method exists.

### Priority 3: make experiment history trustworthy
- Persist immutable versions with input values, original prediction, hypothesis, model version, assumptions, outputs, explanation model/prompt version, timestamps, and learner conclusion.
- For the hackathon demo, browser-local storage can be acceptable if clearly disclosed. For a multi-user pilot, add Supabase, authentication, row-level access controls, and server-side validation.
- Make comparisons refuse or flag incompatible model versions or assumptions.

### Priority 4: use the configured AI provider as a tutor, not an engine
- Keep all credentials server-side.
- Test a small evaluation set of explanation prompts for unsupported claims, incorrect numerical paraphrases, and useful student-level teaching.
- If the provider fails, preserve the calculated result and allow the learner to continue.
- Confirm the selected provider model, endpoint, pricing, quotas, and terms in the user's own account before a live demo.

### Priority 5: prove learning and demand

The earlier VECTERA PRD proposed controlled engineering cases, expert review, and pre/post learning checks. Reuse that validation discipline without automatically importing VECTERA's telemetry-diagnosis scope into TRAKIVO's first scenario.

Recommended first pilot:
1. Create 10–20 small, hand-checked gearing cases with known outputs.
2. Ask 5–8 motorsport/Formula Student learners to complete the experiment without help.
3. Measure completion, whether learners can explain the trade-off in their own words, and whether they can make a better prediction on a new case.
4. Have an experienced vehicle/vehicle-dynamics engineer review assumptions and wording.
5. Change the product based on observed confusion, not only positive opinions.

Do not present these pilot counts as statistically representative. They are a practical early usability check.

## Decision

**Keep the core concept, improve the learning loop, and resist adding more pillars right now.** The strongest next release is not a larger dashboard. It is a single experiment that teaches a defensible cause-and-effect relationship, preserves what the learner thought before the run, explains the calculated result, and can be repeated and reviewed.
