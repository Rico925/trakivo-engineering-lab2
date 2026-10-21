import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src/python/brain'))
from experiment_model import run_experiment, MODEL_VERSION

def test_baseline_has_zero_deltas():
    r = run_experiment(3.5, 'Baseline prediction', 'Baseline hypothesis')
    assert r['model_version'] == MODEL_VERSION
    assert r['evidence_label'] == 'SIMULATED'
    assert all(v == 0 for v in r['delta_vs_baseline'].values())

def test_higher_final_drive_tradeoff():
    low = run_experiment(3.0, 'Lower torque', 'Lower ratio lowers wheel torque')
    high = run_experiment(4.0, 'Higher torque', 'Higher ratio raises wheel torque')
    assert high['result']['wheel_torque_nm'] > low['result']['wheel_torque_nm']
    assert high['result']['theoretical_speed_kmh'] < low['result']['theoretical_speed_kmh']

def test_range_validation():
    try:
        run_experiment(5.1, 'Prediction', 'Hypothesis')
    except ValueError:
        pass
    else:
        raise AssertionError('out-of-range input accepted')

def test_requires_prediction_and_hypothesis():
    for prediction, hypothesis in [('', 'hypothesis'), ('prediction', '')]:
        try: run_experiment(3.5, prediction, hypothesis)
        except ValueError: continue
        raise AssertionError('missing pre-run record accepted')

if __name__ == '__main__':
    for test in [test_baseline_has_zero_deltas, test_higher_final_drive_tradeoff, test_range_validation, test_requires_prediction_and_hypothesis]:
        test(); print('PASS', test.__name__)
