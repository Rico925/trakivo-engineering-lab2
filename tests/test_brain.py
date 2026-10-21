import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src/python/brain"))
from brain_orchestrator import TrakivoBrain

def test_empty_slice_is_not_a_fault_claim():
    result=TrakivoBrain().analyze_frames([])
    assert result["severity"]=="info" and result["evidence_label"]=="UNKNOWN"
    assert "confidence" not in result
    assert "No telemetry" in result["observation"]

def test_anomaly_flag_is_reported_without_causal_claim():
    result=TrakivoBrain().analyze_frames([{"speed_kmh":288,"is_anomaly":True,"anomaly_type":"DemoSensorSpike"}])
    assert result["severity"]=="warning"
    assert "confidence" not in result
    assert "DemoSensorSpike" in result["observation"]
    assert "not proof" in result["reasoning"]

if __name__=="__main__":
    test_empty_slice_is_not_a_fault_claim()
    test_anomaly_flag_is_reported_without_causal_claim()
    print("PASS Python analysis behavior tests")
