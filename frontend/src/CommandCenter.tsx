import React, { useEffect, useState } from 'react';

const API_BASE = import.meta.env.VITE_EXPERIMENT_API_URL ?? 'http://127.0.0.1:8000';
type Run = {
  id: string; savedAt: string; model_version: string; evidence_label: string;
  parameter: { name: string; unit: string; value: number; baseline: number; minimum: number; maximum: number };
  prediction: string; hypothesis: string; fixed_inputs: Record<string, number>;
  baseline: Record<string, number>; result: Record<string, number>; delta_vs_baseline: Record<string, number>;
  assumptions: string[]; limitations: string; uncertainty: string; telemetry_comparison?: any;
};
type SavedRun = Run & { conclusion: string };
const STORE_KEY = 'trakivo.experimentRuns.v1';
const metricLabels: Record<string, { label: string; unit: string }> = {
  wheel_torque_nm: { label: 'Wheel torque', unit: 'N·m' },
  tractive_force_n: { label: 'Idealised tractive force', unit: 'N' },
  theoretical_speed_kmh: { label: 'Theoretical speed at fixed RPM', unit: 'km/h' },
};

export const CommandCenter: React.FC = () => {
  const [ratio, setRatio] = useState(3.5);
  const [prediction, setPrediction] = useState('Higher final-drive ratio will increase wheel torque and reduce theoretical speed at the same engine RPM.');
  const [hypothesis, setHypothesis] = useState('Increasing final-drive ratio trades theoretical speed for wheel torque in this simplified gearing model.');
  const [conclusion, setConclusion] = useState('');
  const [run, setRun] = useState<Run | null>(null);
  const [saved, setSaved] = useState<SavedRun[]>([]);
  const [selectedCompare, setSelectedCompare] = useState('');
  const [explanation, setExplanation] = useState('');
  const [busy, setBusy] = useState(false);
  const [explainBusy, setExplainBusy] = useState(false);
  const [error, setError] = useState('');
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [telemetryCsv, setTelemetryCsv] = useState('');
  const [telemetryName, setTelemetryName] = useState('');
  const [telemetryInfo, setTelemetryInfo] = useState<any>(null);
  const [telemetryComparison, setTelemetryComparison] = useState<any>(null);
  const [referenceLap, setReferenceLap] = useState('');
  const [comparisonLap, setComparisonLap] = useState('');
  const [telemetryBusy, setTelemetryBusy] = useState(false);

  useEffect(() => {
    try { const raw = localStorage.getItem(STORE_KEY); if (raw) setSaved(JSON.parse(raw) as SavedRun[]); } catch { setError('Saved experiment history could not be read from this browser.'); }
    fetch(`${API_BASE}/health`).then(r => { if (!r.ok) throw new Error('offline'); return r.json(); }).then(() => setApiStatus('online')).catch(() => setApiStatus('offline'));
  }, []);

  const persist = (runs: SavedRun[]) => { setSaved(runs); try { localStorage.setItem(STORE_KEY, JSON.stringify(runs)); } catch { setError('Browser storage is full. Export or remove older experiments.'); } };
  const runExperiment = async () => {
    setBusy(true); setError(''); setExplanation('');
    try {
      const response = await fetch(`${API_BASE}/experiment/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ final_drive_ratio: ratio, prediction, hypothesis }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || data.error || `Experiment failed (${response.status})`);
      setRun({ ...data, id: crypto.randomUUID(), savedAt: new Date().toISOString() });
    } catch (e) { setError(e instanceof Error ? e.message : 'Experiment failed.'); }
    finally { setBusy(false); }
  };
  const saveRun = () => {
    if (!run) return;
    const record: SavedRun = { ...run, conclusion };
    persist([record, ...saved.filter(s => s.id !== run.id)]);
  };
  const saveRunWithTelemetry = () => {
    if (!run || !telemetryComparison) return;
    const attached = { ...run, telemetry_comparison: telemetryComparison };
    setRun(attached);
    const record: SavedRun = { ...attached, conclusion };
    persist([record, ...saved.filter(s => s.id !== run.id)]);
  };
  const loadRun = (id: string) => {
    const found = saved.find(s => s.id === id); if (!found) return;
    setRun(found); setRatio(found.parameter.value); setPrediction(found.prediction); setHypothesis(found.hypothesis); setConclusion(found.conclusion); setTelemetryComparison(found.telemetry_comparison ?? null); setExplanation('');
  };
  const explain = async () => {
    if (!run) return;
    setExplainBusy(true); setError('');
    try {
      const response = await fetch(`${API_BASE}/explain`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ experiment: run }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'AI explanation request failed.');
      setExplanation(data.explanation || data.message || 'AI provider is not configured.');
    } catch (e) { setError(e instanceof Error ? e.message : 'Explanation unavailable.'); }
    finally { setExplainBusy(false); }
  };
  const compare = saved.find(s => s.id === selectedCompare);

  const importTelemetry = async (file?: File) => {
    if (!file) return;
    setTelemetryBusy(true); setError(''); setTelemetryComparison(null); setTelemetryInfo(null);
    try {
      const csvText = await file.text();
      const response = await fetch(`${API_BASE}/telemetry/import`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ csv_text: csvText }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Telemetry import failed (${response.status})`);
      setTelemetryCsv(csvText); setTelemetryName(file.name); setTelemetryInfo(data);
      if (data.laps?.length >= 2) { setReferenceLap(String(data.laps[0].lap_id)); setComparisonLap(String(data.laps[1].lap_id)); }
    } catch (e) { setError(e instanceof Error ? e.message : 'Telemetry import failed.'); }
    finally { setTelemetryBusy(false); }
  };

  const compareTelemetry = async () => {
    if (!telemetryCsv || !referenceLap || !comparisonLap) return;
    setTelemetryBusy(true); setError('');
    try {
      const response = await fetch(`${API_BASE}/telemetry/compare`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ csv_text: telemetryCsv, reference_lap: referenceLap, comparison_lap: comparisonLap }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Lap comparison failed (${response.status})`);
      setTelemetryComparison(data);
    } catch (e) { setError(e instanceof Error ? e.message : 'Lap comparison failed.'); }
    finally { setTelemetryBusy(false); }
  };

  return <div className="app-shell">
    <header className="topbar"><div><h1>TRAKIVO <span>ENGINEERING LAB</span></h1><p>HYPOTHESIS → CONTROLLED CHANGE → MODEL → LEARNING RECORD</p></div><div className="status">API: <strong className={apiStatus}>{apiStatus.toUpperCase()}</strong></div></header>
    {error && <div role="alert" className="error-banner">{error}</div>}
    <div className="scope-banner"><strong>Prototype boundary</strong> This is an educational gearing calculation, not a validated vehicle simulator. Outputs are simulated, not measured.</div>
    <main className="experiment-layout">
      <section className="panel"><div className="panel-heading"><h2>01 / DEFINE YOUR EXPERIMENT</h2><span className="tag">ONE PARAMETER</span></div>
        <label className="field-label" htmlFor="scenario">Prepared scenario</label><div id="scenario" className="scenario-card"><strong>Final-drive gearing trade-off</strong><p>Explore how a gear reduction changes idealised wheel torque and theoretical speed at a fixed engine RPM.</p></div>
        <div className="parameter-head"><label className="field-label" htmlFor="ratio">Final drive ratio</label><strong>{ratio.toFixed(1)}:1</strong></div>
        <input id="ratio" className="range" type="range" min="2.5" max="5" step="0.1" value={ratio} onChange={e => setRatio(Number(e.target.value))} />
        <div className="range-labels"><span>2.5:1 · lower reduction</span><span>5.0:1 · higher reduction</span></div>
        <p className="helper">Dimensionless ratio. Allowed range: 2.5 to 5.0. Baseline: 3.5:1.</p>
        <label className="field-label" htmlFor="hypothesis">Hypothesis</label><textarea id="hypothesis" value={hypothesis} onChange={e => setHypothesis(e.target.value)} rows={3} maxLength={1000}/>
        <label className="field-label" htmlFor="prediction">My prediction (record before run)</label><textarea id="prediction" value={prediction} onChange={e => setPrediction(e.target.value)} rows={3} maxLength={1000}/>
        <button onClick={runExperiment} disabled={busy || apiStatus !== 'online'}>{busy ? 'RUNNING MODEL…' : 'RUN SIMULATED EXPERIMENT'}</button>
        <p className="helper">The deterministic calculation runs before any AI explanation. No API key is needed to calculate results.</p>
      </section>
      <section className="panel results-panel"><div className="panel-heading"><h2>02 / MODEL REPORT</h2>{run && <span className="tag simulated">● {run.evidence_label}</span>}</div>
        {!run ? <div className="empty"><b>Waiting for an experiment</b><p>Record your prediction, then run the model to see the baseline comparison.</p></div> : <>
          <div className="result-summary"><div><span>MODEL VERSION</span><strong>{run.model_version}</strong></div><div><span>PARAMETER</span><strong>{run.parameter.value.toFixed(1)}:1</strong></div><div><span>EVIDENCE TYPE</span><strong>SIMULATED</strong></div></div>
          <div className="metric-grid">{Object.entries(metricLabels).map(([key, meta]) => <div className="metric" key={key}><span>{meta.label}</span><strong>{run.result[key].toLocaleString(undefined, { maximumFractionDigits: 1 })}</strong><small>{meta.unit}</small><div className={run.delta_vs_baseline[key] >= 0 ? 'delta' : 'delta negative'}>{run.delta_vs_baseline[key] > 0 ? '+' : ''}{run.delta_vs_baseline[key].toLocaleString(undefined, { maximumFractionDigits: 1 })} {meta.unit} vs baseline</div></div>)}</div>
          <div className="compare-table"><h3>CHANGED SCENARIO VS BASELINE (3.5:1)</h3><table><thead><tr><th>Output</th><th>Baseline</th><th>This run</th></tr></thead><tbody>{Object.entries(metricLabels).map(([key, meta]) => <tr key={key}><td>{meta.label}</td><td>{run.baseline[key]} {meta.unit}</td><td>{run.result[key]} {meta.unit}</td></tr>)}</tbody></table></div>
          <div className="prediction-card"><strong>Prediction captured before run</strong><p>{run.prediction}</p><strong>Hypothesis</strong><p>{run.hypothesis}</p></div>
          <label className="field-label" htmlFor="conclusion">Learner conclusion (including neutral or unexpected results)</label><textarea id="conclusion" value={conclusion} onChange={e => setConclusion(e.target.value)} rows={3} maxLength={2000} placeholder="What did the model show? Did it match your prediction? What remains unknown?" />
          <div className="button-row"><button onClick={saveRun} className="secondary">SAVE EXPERIMENT VERSION</button><button onClick={explain} disabled={explainBusy} className="ai-button">{explainBusy ? 'ASKING AI…' : 'EXPLAIN WITH AI'}</button></div>
          {explanation && <div className="explanation"><h3>AI EXPLANATION · INTERPRETATION ONLY</h3><p>{explanation}</p></div>}
          <details className="assumptions"><summary>Assumptions, limits and unknowns</summary><ul>{run.assumptions.map(a => <li key={a}>{a}</li>)}</ul><p><strong>Limitations:</strong> {run.limitations}</p><p><strong>Uncertainty:</strong> {run.uncertainty}</p></details>
        </>}
      </section>
      <section className="panel telemetry-panel"><div className="panel-heading"><h2>03 / TELEMETRY ANALYSIS</h2><span className="tag">CSV · DISTANCE ALIGNED</span></div>
        <p className="helper">Import a CSV with speed and distance or time. Common headers such as <code>speed_kmh</code>, <code>speed_kph</code>, <code>distance_m</code>, <code>lap</code>, <code>throttle_pct</code> and <code>brake_pct</code> are recognized. Imported data is processed locally by this API; it is not uploaded to Groq.</p>
        <label className="upload-drop"><span>{telemetryBusy ? 'PROCESSING TELEMETRY…' : telemetryName ? `SELECTED: ${telemetryName}` : 'SELECT A TELEMETRY CSV FILE'}</span><input type="file" accept=".csv,text/csv" onChange={e => importTelemetry(e.target.files?.[0])} disabled={telemetryBusy || apiStatus !== 'online'} /></label>
        {telemetryInfo && <><div className="result-summary telemetry-summary"><div><span>ROWS IMPORTED</span><strong>{telemetryInfo.row_count.toLocaleString()}</strong></div><div><span>LAPS DETECTED</span><strong>{telemetryInfo.lap_count}</strong></div><div><span>SCHEMA</span><strong>{telemetryInfo.schema_version}</strong></div></div>
          <p className="helper">Lap detection: {telemetryInfo.lap_detection}. Channels: {telemetryInfo.normalized_channels.join(', ')}.</p>
          <div className="lap-selectors"><label className="field-label">Reference lap<select value={referenceLap} onChange={e => { setReferenceLap(e.target.value); setTelemetryComparison(null); }}><option value="">Select lap</option>{telemetryInfo.laps.map((lap: any) => <option key={lap.lap_id} value={String(lap.lap_id)}>Lap {lap.lap_id} · {lap.samples} samples</option>)}</select></label><label className="field-label">Comparison lap<select value={comparisonLap} onChange={e => { setComparisonLap(e.target.value); setTelemetryComparison(null); }}><option value="">Select lap</option>{telemetryInfo.laps.map((lap: any) => <option key={lap.lap_id} value={String(lap.lap_id)}>Lap {lap.lap_id} · {lap.samples} samples</option>)}</select></label><button onClick={compareTelemetry} disabled={telemetryBusy || !referenceLap || !comparisonLap || referenceLap === comparisonLap}>COMPARE LAPS</button></div>
          <div className="compare-table"><h3>IMPORTED LAP SUMMARY</h3><table><thead><tr><th>Lap</th><th>Samples</th><th>Distance range</th><th>Mean speed</th><th>Max speed</th></tr></thead><tbody>{telemetryInfo.laps.map((lap: any) => <tr key={lap.lap_id}><td>{lap.lap_id}</td><td>{lap.samples}</td><td>{lap.distance_start_m == null ? 'N/A' : `${lap.distance_start_m}–${lap.distance_end_m} m`}</td><td>{lap.mean_speed_kmh} km/h</td><td>{lap.max_speed_kmh} km/h</td></tr>)}</tbody></table></div>
        </>}
        {telemetryComparison && <><div className="metric-grid telemetry-metrics"><div className="metric"><span>MEAN SPEED DELTA</span><strong>{telemetryComparison.summary.mean_speed_delta_kmh > 0 ? '+' : ''}{telemetryComparison.summary.mean_speed_delta_kmh}</strong><small>km/h · comparison minus reference</small></div><div className="metric"><span>MAX POSITIVE DELTA</span><strong>{telemetryComparison.summary.max_positive_speed_delta_kmh}</strong><small>km/h</small></div><div className="metric"><span>MAX NEGATIVE DELTA</span><strong>{telemetryComparison.summary.max_negative_speed_delta_kmh}</strong><small>km/h</small></div></div>
          <div className="compare-table"><h3>SPEED TRACE · DISTANCE ALIGNED</h3><table><thead><tr><th>Distance (m)</th><th>Reference (km/h)</th><th>Comparison (km/h)</th><th>Delta (km/h)</th></tr></thead><tbody>{telemetryComparison.trace.filter((_: any, i: number) => i % 10 === 0 || i === telemetryComparison.trace.length - 1).map((point: any) => <tr key={point.distance_m}><td>{point.distance_m}</td><td>{point.reference_speed_kmh}</td><td>{point.comparison_speed_kmh}</td><td>{point.delta_speed_kmh > 0 ? '+' : ''}{point.delta_speed_kmh}</td></tr>)}</tbody></table></div>
          <details className="assumptions"><summary>Alignment method and limitations</summary><p>{telemetryComparison.alignment}. {telemetryComparison.limitations}</p></details>
          <div className="button-row"><button className="secondary" onClick={saveRunWithTelemetry} disabled={!run}>SAVE COMPARISON WITH CURRENT EXPERIMENT</button></div>
          {!run && <p className="helper">Run an Engineering Experiment first to save this telemetry comparison alongside its hypothesis and model evidence.</p>}
        </>}
      </section>
      <section className="panel history-panel"><div className="panel-heading"><h2>04 / ENGINEERING DECISION REPLAY</h2><span className="tag">LOCAL HISTORY</span></div>
        {saved.length === 0 ? <p className="helper">Saved versions will appear here. They are stored in this browser only, not synced to an account or database.</p> : <>
          <div className="history-list">{saved.map((s, i) => <div className="history-item" key={s.id}><div><strong>{s.parameter.value.toFixed(1)}:1 final drive</strong><span>{new Date(s.savedAt).toLocaleString()} · {s.model_version}</span><small>SIMULATED · {s.conclusion ? 'Conclusion saved' : 'No conclusion yet'}</small></div><button className="small-button" onClick={() => loadRun(s.id)}>REOPEN</button></div>)}</div>
          <div className="compare-controls"><label className="field-label" htmlFor="compare">Compare current result with saved version</label><select id="compare" value={selectedCompare} onChange={e => setSelectedCompare(e.target.value)}><option value="">Choose saved version</option>{saved.map(s => <option key={s.id} value={s.id}>{s.parameter.value.toFixed(1)}:1 · {new Date(s.savedAt).toLocaleString()}</option>)}</select></div>
          {compare && run && <div className="compare-table"><h3>VERSION COMPARISON</h3><table><thead><tr><th>Output</th><th>Saved</th><th>Current</th></tr></thead><tbody>{Object.entries(metricLabels).map(([key, meta]) => <tr key={key}><td>{meta.label}</td><td>{compare.result[key]} {meta.unit}</td><td>{run.result[key]} {meta.unit}</td></tr>)}</tbody></table><p className="helper">Check model versions and assumptions before interpreting a comparison.</p></div>}
        </>}
      </section>
    </main>
    <footer className="site-footer">TRAKIVO is for engineering education. These outputs are not validated for real vehicle setup or safety decisions.</footer>
  </div>;
};
