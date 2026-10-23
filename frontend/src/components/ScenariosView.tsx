import React, { useState, useEffect } from 'react';
import { 
  Play, CheckCircle2, XCircle, HelpCircle, 
  Terminal, ShieldCheck, Cpu, ArrowRight, Zap
} from 'lucide-react';
import { ScenarioMeta } from '../types';
import { fetchScenarios, runScenario } from '../api';

interface ScenariosViewProps {
  onScenarioExecuted: (invId: string) => void;
}

export const ScenariosView: React.FC<ScenariosViewProps> = ({ onScenarioExecuted }) => {
  const [scenarios, setScenarios] = useState<ScenarioMeta[]>([]);
  const [runningId, setRunningId] = useState<string | null>(null);

  useEffect(() => {
    fetchScenarios().then(setScenarios).catch(console.error);
  }, []);

  const handleRun = async (scenId: string) => {
    setRunningId(scenId);
    try {
      const res = await runScenario(scenId);
      if (res.investigation_id) {
        onScenarioExecuted(res.investigation_id);
      }
    } catch (err: any) {
      alert(`Scenario execution error: ${err.message}`);
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div>
      <div className="card" style={{ background: '#0e1628', borderColor: 'var(--border-focus)' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#fff', marginBottom: '0.4rem' }}>
          Reproducible Scientific Benchmarks & Controlled Live Experiments
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          These automated test scenarios exercise the verification engine with real host provenance, independent packet evidence, and genuine OS socket calls. Executing a scenario initializes a clean investigation, parses raw artifacts, applies invariant arbitration rules, and synthesizes both candidate and refined attack graphs.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
        {scenarios.map((scen) => {
          const isLive = scen.type === 'LIVE_SOCKET_EXECUTION';
          const verdict = scen.expected_verdict;
          return (
            <div key={scen.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <span className={`badge badge-${verdict.toLowerCase()}`}>
                    {verdict === 'SUPPORTED' && <CheckCircle2 size={12} />}
                    {verdict === 'CONTRADICTED' && <XCircle size={12} />}
                    {verdict === 'UNRESOLVED' && <HelpCircle size={12} />}
                    Expected: {verdict}
                  </span>

                  <span className="badge badge-neutral" style={{ fontSize: '0.68rem', gap: '4px' }}>
                    {isLive ? <Zap size={11} color="var(--cyan-primary)" /> : <Terminal size={11} />}
                    {isLive ? 'LIVE LOCAL SOCKET' : 'DARPA TC FIXTURE'}
                  </span>
                </div>

                <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', marginBottom: '0.5rem' }}>
                  {scen.title}
                </h4>

                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '1rem' }}>
                  {scen.description}
                </p>
              </div>

              <button
                className="btn btn-primary"
                style={{ width: '100%', fontSize: '0.85rem' }}
                onClick={() => handleRun(scen.id)}
                disabled={runningId !== null}
              >
                {runningId === scen.id ? (
                  <span>Executing Pipeline...</span>
                ) : (
                  <>
                    <Play size={14} /> Execute & Inspect In Graph <ArrowRight size={14} />
                  </>
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
