import React, { useState, useEffect } from 'react';
import { 
  Radio, ShieldAlert, CheckCircle2, AlertTriangle, 
  Settings, RefreshCw, Plus, Edit2
} from 'lucide-react';
import { SensorConfig } from '../types';
import { fetchSensors, updateSensor } from '../api';

interface SensorsViewProps {
  investigationId: string;
}

export const SensorsView: React.FC<SensorsViewProps> = ({ investigationId }) => {
  const [sensors, setSensors] = useState<SensorConfig[]>([]);
  const [editingSensor, setEditingSensor] = useState<SensorConfig | null>(null);
  const [cidrInput, setCidrInput] = useState('');

  const loadSensors = () => {
    if (investigationId) {
      fetchSensors(investigationId).then(setSensors).catch(console.error);
    }
  };

  useEffect(() => {
    loadSensors();
  }, [investigationId]);

  const handleToggleDrop = async (sensor: SensorConfig) => {
    try {
      const updated: SensorConfig = {
        ...sensor,
        packet_loss_detected: !sensor.packet_loss_detected
      };
      await updateSensor(sensor.id, updated);
      loadSensors();
    } catch (err: any) {
      alert(`Error toggling loss: ${err.message}`);
    }
  };

  const handleSaveCidrs = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSensor) return;
    const cidrs = cidrInput.split(',').map((s) => s.trim()).filter(Boolean);
    try {
      await updateSensor(editingSensor.id, {
        ...editingSensor,
        monitored_cidrs: cidrs
      });
      setEditingSensor(null);
      loadSensors();
    } catch (err: any) {
      alert(`Error updating CIDRs: ${err.message}`);
    }
  };

  return (
    <div>
      {/* Sensor Observability Thesis Banner */}
      <div className="card" style={{ background: '#0e172a', borderColor: '#1e3a8a' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8', marginBottom: '0.4rem' }}>
          Observability-Aware Invariant Baseline
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          In TrueTrace, network sensors define the empirical visibility envelope. If an event falls outside a sensor's monitored CIDR range, or if the sensor recorded hardware packet ring drops, the arbitration engine rigorously enforces the fundamental epistemic invariant: <strong>absence of evidence is NOT evidence of absence</strong>. Such claims are preserved as <code>UNRESOLVED</code>.
        </p>
      </div>

      {/* Sensors Table */}
      <div className="card" style={{ padding: 0 }}>
        <div className="card-header" style={{ padding: '1rem 1.25rem', marginBottom: 0 }}>
          <div className="card-title">
            <Radio size={18} color="var(--cyan-primary)" /> Registered Network Sensors & Taps
          </div>
          <button className="btn btn-secondary" style={{ padding: '0.3rem 0.65rem' }} onClick={loadSensors}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Sensor ID</th>
                <th>Sensor Name</th>
                <th>Interface</th>
                <th>Monitored CIDR Ranges</th>
                <th>Hardware Loss Flag</th>
                <th>State</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sensors.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.78rem' }}>{s.id}</td>
                  <td style={{ fontWeight: 600 }}>{s.sensor_name}</td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>{s.interface}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {s.monitored_cidrs.map((c) => (
                        <span key={c} className="badge badge-neutral" style={{ fontSize: '0.72rem' }}>
                          {c}
                        </span>
                      ))}
                      {s.monitored_cidrs.length === 0 && (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>No CIDRs</span>
                      )}
                    </div>
                  </td>
                  <td>
                    {s.packet_loss_detected ? (
                      <span className="badge badge-contradicted" style={{ gap: '4px' }}>
                        <AlertTriangle size={12} /> PACKET LOSS FLAGGED
                      </span>
                    ) : (
                      <span className="badge badge-supported" style={{ gap: '4px' }}>
                        <CheckCircle2 size={12} /> LOSSLESS (100% OK)
                      </span>
                    )}
                  </td>
                  <td>
                    <span className="badge badge-neutral">{s.status}</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
                        onClick={() => {
                          setEditingSensor(s);
                          setCidrInput(s.monitored_cidrs.join(', '));
                        }}
                      >
                        <Edit2 size={12} /> Edit CIDRs
                      </button>
                      <button
                        className={`btn ${s.packet_loss_detected ? 'btn-success' : 'btn-danger'}`}
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
                        onClick={() => handleToggleDrop(s)}
                      >
                        {s.packet_loss_detected ? 'Clear Loss' : 'Simulate Loss'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {sensors.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No sensors registered for this investigation.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit CIDRs Modal */}
      {editingSensor && (
        <div className="modal-overlay" onClick={() => setEditingSensor(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="card-header">
              <div className="card-title">
                <Settings size={18} color="var(--cyan-primary)" /> Edit Sensor Monitored CIDRs
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                onClick={() => setEditingSensor(null)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveCidrs}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Monitored IPv4 Subnets (comma-separated):
                </label>
                <input
                  type="text"
                  value={cidrInput}
                  onChange={(e) => setCidrInput(e.target.value)}
                  placeholder="e.g. 192.168.1.0/24, 198.51.100.0/24"
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    color: '#fff',
                    fontFamily: 'monospace',
                    fontSize: '0.85rem'
                  }}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '4px', display: 'block' }}>
                  Restricting CIDRs will trigger the observability check to classify out-of-scope communications as UNRESOLVED.
                </span>
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                Save Sensor Scope
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
