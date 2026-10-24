import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, XCircle, HelpCircle, Filter, 
  Search, ShieldAlert, FileText, ArrowRight, RefreshCw 
} from 'lucide-react';
import { NetworkClaim, ArbitrationResult, Verdict } from '../types';
import { fetchClaims, fetchArbitrationResults } from '../api';

interface ClaimInspectorViewProps {
  investigationId: string;
}

export const ClaimInspectorView: React.FC<ClaimInspectorViewProps> = ({ investigationId }) => {
  const [claims, setClaims] = useState<NetworkClaim[]>([]);
  const [results, setResults] = useState<ArbitrationResult[]>([]);
  const [filterVerdict, setFilterVerdict] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedClaim, setSelectedClaim] = useState<{ claim: NetworkClaim; arb?: ArbitrationResult } | null>(null);

  const loadData = () => {
    if (investigationId) {
      Promise.all([
        fetchClaims(investigationId),
        fetchArbitrationResults(investigationId)
      ]).then(([cList, rList]) => {
        setClaims(cList);
        setResults(rList);
      }).catch(console.error);
    }
  };

  useEffect(() => {
    loadData();
  }, [investigationId]);

  const arbMap = new Map<string, ArbitrationResult>();
  results.forEach((r) => arbMap.set(r.claim_id, r));

  const filtered = claims.filter((c) => {
    const arb = arbMap.get(c.id);
    const v = arb ? arb.verdict : 'UNRESOLVED';
    if (filterVerdict !== 'ALL' && v !== filterVerdict) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        c.dst_ip.toLowerCase().includes(q) ||
        c.description.toLowerCase().includes(q) ||
        c.claim_type.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div>
      {/* Filters Toolbar */}
      <div className="card" style={{ padding: '0.75rem 1.25rem', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={16} color="var(--text-muted)" />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500 }}>Verdict:</span>
            {['ALL', 'SUPPORTED', 'CONTRADICTED', 'UNRESOLVED'].map((cat) => (
              <button
                key={cat}
                onClick={() => setFilterVerdict(cat)}
                style={{
                  padding: '0.25rem 0.65rem',
                  borderRadius: '4px',
                  border: '1px solid var(--border)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: filterVerdict === cat ? 'rgba(6, 182, 212, 0.15)' : 'var(--bg-secondary)',
                  color: filterVerdict === cat ? 'var(--cyan-primary)' : 'var(--text-muted)',
                  borderColor: filterVerdict === cat ? 'var(--cyan-primary)' : 'var(--border)'
                }}
              >
                {cat}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Search size={14} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search IP, flow, or process..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                padding: '0.35rem 0.65rem',
                fontSize: '0.8rem',
                color: '#fff',
                width: '200px'
              }}
            />
            <button
              className="btn btn-secondary"
              style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
              onClick={loadData}
              title="Refresh claims"
            >
              <RefreshCw size={13} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="card" style={{ padding: 0 }}>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Verdict</th>
                <th>Claim ID</th>
                <th>Hypothesis Type</th>
                <th>Flow 5-Tuple</th>
                <th>Timestamp</th>
                <th>Applied Invariant Rule</th>
                <th>Reasoning Summary</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => {
                const arb = arbMap.get(c.id);
                const verdict = arb?.verdict || 'UNRESOLVED';
                return (
                  <tr key={c.id}>
                    <td>
                      <span className={`badge badge-${verdict.toLowerCase()}`}>
                        {verdict === 'SUPPORTED' && <CheckCircle2 size={12} />}
                        {verdict === 'CONTRADICTED' && <XCircle size={12} />}
                        {verdict === 'UNRESOLVED' && <HelpCircle size={12} />}
                        {verdict}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.78rem' }}>{c.id}</td>
                    <td>
                      <span className="badge badge-neutral">{c.claim_type}</span>
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                      {c.src_ip}:{c.src_port || '*'} &rarr; {c.dst_ip}:{c.dst_port}
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {c.timestamp_iso ? new Date(c.timestamp_iso).toLocaleTimeString() : c.timestamp}
                    </td>
                    <td>
                      <code style={{ fontSize: '0.75rem', color: 'var(--cyan-primary)' }}>
                        {arb?.applied_rule || 'Pending'}
                      </code>
                    </td>
                    <td style={{ fontSize: '0.8rem', maxWidth: '320px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {arb?.reasoning || c.description}
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => setSelectedClaim({ claim: c, arb })}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    No network claims matching current filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Claim Detail Modal */}
      {selectedClaim && (
        <div className="modal-overlay" onClick={() => setSelectedClaim(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="card-header">
              <div className="card-title">
                <FileText size={18} color="var(--cyan-primary)" />
                Claim Arbitration Details ({selectedClaim.claim.id})
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                onClick={() => setSelectedClaim(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Claimed Description</div>
              <p style={{ fontSize: '0.85rem', color: '#fff', fontWeight: 500 }}>
                {selectedClaim.claim.description}
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ background: 'var(--bg-primary)', padding: '0.6rem', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Target Flow</span>
                <span style={{ fontSize: '0.82rem', fontFamily: 'monospace' }}>
                  {selectedClaim.claim.src_ip}:{selectedClaim.claim.src_port || '*'} &rarr; {selectedClaim.claim.dst_ip}:{selectedClaim.claim.dst_port}
                </span>
              </div>
              <div style={{ background: 'var(--bg-primary)', padding: '0.6rem', borderRadius: '4px' }}>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>Verdict</span>
                <span className={`badge badge-${selectedClaim.arb?.verdict.toLowerCase() || 'unresolved'}`}>
                  {selectedClaim.arb?.verdict || 'UNRESOLVED'}
                </span>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Applied Invariant Rule</span>
              <code style={{ fontSize: '0.8rem', color: 'var(--cyan-primary)', background: 'var(--bg-primary)', padding: '4px 8px', borderRadius: '4px', display: 'block' }}>
                {selectedClaim.arb?.applied_rule || 'INV-OBS-00: Unarbitrated'}
              </code>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Formal Reasoning</span>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-main)', background: 'var(--bg-primary)', padding: '0.75rem', borderRadius: '4px', lineHeight: 1.5 }}>
                {selectedClaim.arb?.reasoning || 'No arbitration result recorded.'}
              </p>
            </div>

            {selectedClaim.arb?.observability_reasoning && (
              <div style={{ marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Observability Telemetry</span>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', background: 'var(--bg-primary)', padding: '0.6rem', borderRadius: '4px' }}>
                  {selectedClaim.arb.observability_reasoning}
                </p>
              </div>
            )}

            {selectedClaim.arb?.matching_evidence_summaries && selectedClaim.arb.matching_evidence_summaries.length > 0 && (
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                  Matched Wire Packets ({selectedClaim.arb.matching_evidence_summaries.length})
                </span>
                <div style={{ maxHeight: '140px', overflowY: 'auto', background: 'var(--bg-primary)', borderRadius: '4px', padding: '0.5rem' }}>
                  {selectedClaim.arb.matching_evidence_summaries.map((s, idx) => (
                    <div key={idx} style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--cyan-primary)', marginBottom: '3px' }}>
                      &bull; {s}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
