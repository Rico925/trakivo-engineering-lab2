"""Legacy telemetry summary scaffold. No external model or invented confidence scores."""
from rag_manager import TrakivoRAG


class TrakivoBrain:
    def __init__(self):
        self.rag = TrakivoRAG()

    def analyze_frames(self, frames):
        if not frames:
            return {
                "observation": "No telemetry frames returned for this distance range.",
                "reasoning": "There is insufficient data to infer a mechanical or sensor fault.",
                "lesson": "Check the engine connection and choose a range containing telemetry.",
                "severity": "info",
                "evidence_label": "UNKNOWN",
            }

        def num(frame, key):
            try:
                return float(frame.get(key, 0) or 0)
            except (TypeError, ValueError):
                return 0.0

        anomalies = [frame for frame in frames if frame.get("is_anomaly")]
        vmax = max(num(frame, "speed_kmh") for frame in frames)
        if anomalies:
            kinds = sorted({str(frame.get("anomaly_type") or "unspecified anomaly") for frame in anomalies})
            observation = (
                f"Telemetry flags {len(anomalies)} anomalous frame(s): {', '.join(kinds)}. "
                f"Maximum recorded speed is {vmax:.1f} km/h."
            )
            severity = "warning"
        else:
            observation = (
                f"Received {len(frames)} telemetry frames. Maximum recorded speed is {vmax:.1f} km/h; "
                "no frame-level anomaly flag was set."
            )
            severity = "info"

        context = self.rag.retrieve_context(observation)
        reasoning = (
            f"This is a descriptive summary, not proof of mechanical failure. Engineering context: {context} "
            "Validate sensor calibration, operating conditions, and series-specific limits before making a safety "
            "or setup decision."
        )
        lesson = (
            "Separate observation from interpretation. Confirm the signal and compare it with a validated baseline "
            "before deciding what caused it."
        )
        return {
            "observation": observation,
            "reasoning": reasoning,
            "lesson": lesson,
            "severity": severity,
            "evidence_label": "MEASURED",
        }


brain = TrakivoBrain()
