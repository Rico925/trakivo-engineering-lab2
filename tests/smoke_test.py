from pathlib import Path
import ast, subprocess
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT/'src/python/brain').glob('*.py'):
 ast.parse(p.read_text(),filename=str(p)); print('PASS Python syntax:',p.relative_to(ROOT))
for p in [ROOT/'src/node/gateway/server.js', ROOT/'src/node/gateway/server.test.js']:
 r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if r.returncode: raise SystemExit(r.stderr)
 print('PASS Node syntax:',p.relative_to(ROOT))
source=(ROOT/'frontend/src/CommandCenter.tsx').read_text()
for item in ['SIMULATED','/experiment/run','/explain','SAVE EXPERIMENT VERSION','ENGINEERING DECISION REPLAY','prediction','hypothesis','/telemetry/import','/telemetry/compare','SAVE COMPARISON WITH CURRENT EXPERIMENT']:
 assert item in source,item
assert 'Math.random()' not in source
print('PASS experiment UI contract checks')
subprocess.run(['python3', str(ROOT/'tests/test_brain.py')], check=True)
subprocess.run(['python3', str(ROOT/'tests/test_experiment_model.py')], check=True)
print('All dependency-free smoke checks passed.')
