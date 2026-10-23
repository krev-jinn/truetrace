import React, { useState } from 'react';
import { 
  FileText, Network, CheckCircle2, XCircle, HelpCircle, 
  Upload, Play, HardDrive, ShieldCheck, AlertTriangle
} from 'lucide-react';
import { Investigation, EvidenceFile } from '../types';
import { uploadEvidenceFile, runArbitration } from '../api';

interface OverviewViewProps {
  investigation: Investigation | null;
  evidenceFiles: EvidenceFile[];
  onRefresh: () => void;
  onNavigateTab: (tab: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  investigation,
  evidenceFiles,
  onRefresh,
  onNavigateTab
}) => {
  const [uploading, setUploading] = useState(false);
  const [running, setRunning] = useState(false);
  const [uploadDesc, setUploadDesc] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  if (!investigation) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>No investigation selected. Select an investigation from the header or create one.</p>
      </div>
    );
  }

  const stats = investigation.stats || {};
  const sup = stats.supported || 0;
  const con = stats.contradicted || 0;
  const unr = stats.unresolved || 0;

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    try {
      await uploadEvidenceFile(investigation.id, selectedFile, uploadDesc);
      setSelectedFile(null);
      setUploadDesc('');
      onRefresh();
    } catch (err: any) {
      alert(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleRunArbitration = async () => {
    setRunning(true);
    try {
      await runArbitration(investigation.id);
      onRefresh();
      onNavigateTab('graph');
    } catch (err: any) {
      alert(`Arbitration error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      {/* Top Banner with Theoretical Guarantees */}
      <div className="card" style={{ background: 'linear-gradient(135deg, #0d1627 0%, #111d33 100%)', borderColor: 'var(--border-focus)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <img 
              src="/truetrace_icon.png" 
              alt="TrueTrace Emblem" 
              style={{ height: '54px', width: 'auto', objectFit: 'contain' }}
            />
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#fff', marginBottom: '0.25rem' }}>
                {investigation.name}
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {investigation.description || 'Forensic verification workspace initialized.'}
              </p>
            </div>
          </div>
          <button 
            className="btn btn-primary" 
            style={{ padding: '0.65rem 1.25rem', fontSize: '0.9rem' }}
            onClick={handleRunArbitration}
            disabled={running}
          >
            <Play size={16} /> {running ? 'Arbitrating...' : 'Run Invariant Arbitration'}
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="stats-grid">
        <div className="stat-box">
          <div className="stat-label">Host Events (Provenance)</div>
          <div className="stat-value">{stats.host_events || 0}</div>
          <div className="stat-meta">Process, file & socket calls</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Network Packets (Wire)</div>
          <div className="stat-value">{stats.network_packets || 0}</div>
          <div className="stat-meta">L3/L4 transport frames</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Network Hypotheses (Claims)</div>
          <div className="stat-value">{stats.claims || 0}</div>
          <div className="stat-meta">Extracted network actions</div>
        </div>
        <div className="stat-box" style={{ borderLeft: '4px solid var(--supported)' }}>
          <div className="stat-label" style={{ color: 'var(--supported)' }}>Supported Verdicts</div>
          <div className="stat-value" style={{ color: 'var(--supported)' }}>{sup}</div>
          <div className="stat-meta">Independently corroborated</div>
        </div>
        <div className="stat-box" style={{ borderLeft: '4px solid var(--contradicted)' }}>
          <div className="stat-label" style={{ color: 'var(--contradicted)' }}>Contradicted Verdicts</div>
          <div className="stat-value" style={{ color: 'var(--contradicted)' }}>{con}</div>
          <div className="stat-meta">Falsified by packet ground truth</div>
        </div>
        <div className="stat-box" style={{ borderLeft: '4px solid var(--unresolved)' }}>
          <div className="stat-label" style={{ color: 'var(--unresolved)' }}>Unresolved (Preserved)</div>
          <div className="stat-value" style={{ color: 'var(--unresolved)' }}>{unr}</div>
          <div className="stat-meta">Sensor blindspot / incomplete</div>
        </div>
      </div>

      {/* Evidence Files & Ingestion */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem' }}>
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <HardDrive size={18} color="var(--cyan-primary)" /> Ingested Evidence Sources
            </div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              {evidenceFiles.length} file(s) registered
            </span>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>SHA-256 Digest</th>
                  <th>Ingested At</th>
                </tr>
              </thead>
              <tbody>
                {evidenceFiles.map((ev) => (
                  <tr key={ev.id}>
                    <td style={{ fontWeight: 500 }}>{ev.file_name}</td>
                    <td>
                      <span className="badge badge-neutral">{ev.evidence_type}</span>
                    </td>
                    <td>{(ev.file_size_bytes / 1024).toFixed(1)} KB</td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-muted)' }} title={ev.sha256_hash}>
                      {ev.sha256_hash.substring(0, 16)}...
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {new Date(ev.ingested_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
                {evidenceFiles.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>
                      No evidence files ingested yet. Upload PCAP or Host JSON logs below or execute a scenario.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Upload Form */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Upload size={18} color="var(--cyan-primary)" /> Upload Evidence
            </div>
          </div>
          <form onSubmit={handleUpload}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                Select PCAP or Host JSON file:
              </label>
              <input
                type="file"
                accept=".pcap,.pcapng,.cap,.json,.jsonl"
                onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                style={{
                  width: '100%',
                  fontSize: '0.8rem',
                  color: 'var(--text-main)',
                  padding: '0.4rem',
                  background: 'var(--bg-secondary)',
                  borderRadius: '4px',
                  border: '1px solid var(--border)'
                }}
              />
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                Context Notes (Optional):
              </label>
              <input
                type="text"
                placeholder="e.g. Gateway tap capture at core switch"
                value={uploadDesc}
                onChange={(e) => setUploadDesc(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  fontSize: '0.85rem',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border)',
                  borderRadius: '4px',
                  color: '#fff'
                }}
              />
            </div>
            <button
              type="submit"
              className="btn btn-secondary"
              style={{ width: '100%' }}
              disabled={!selectedFile || uploading}
            >
              {uploading ? 'Processing & Hashing...' : 'Ingest Evidence'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
