import React, { useState, useEffect } from 'react';
import { 
  FileText, Activity, Search, Database, Code, ArrowUpRight
} from 'lucide-react';
import { HostEvent, NetworkPacket } from '../types';
import { fetchHostEvents, fetchNetworkPackets } from '../api';

interface EvidenceExplorerViewProps {
  investigationId: string;
}

export const EvidenceExplorerView: React.FC<EvidenceExplorerViewProps> = ({ investigationId }) => {
  const [activeSubTab, setActiveSubTab] = useState<'HOST' | 'NETWORK'>('HOST');
  const [hostEvents, setHostEvents] = useState<HostEvent[]>([]);
  const [packets, setPackets] = useState<NetworkPacket[]>([]);
  const [search, setSearch] = useState('');
  const [rawRecordModal, setRawRecordModal] = useState<any | null>(null);

  useEffect(() => {
    if (investigationId) {
      fetchHostEvents(investigationId).then(setHostEvents).catch(console.error);
      fetchNetworkPackets(investigationId).then(setPackets).catch(console.error);
    }
  }, [investigationId]);

  const filteredHostEvents = hostEvents.filter((e) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (e.process_name && e.process_name.toLowerCase().includes(q)) ||
      (e.file_path && e.file_path.toLowerCase().includes(q)) ||
      (e.dst_ip && e.dst_ip.toLowerCase().includes(q)) ||
      e.event_type.toLowerCase().includes(q)
    );
  });

  const filteredPackets = packets.filter((p) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      p.src_ip.includes(q) ||
      p.dst_ip.includes(q) ||
      p.tcp_flags.join(',').toLowerCase().includes(q) ||
      p.summary.toLowerCase().includes(q)
    );
  });

  return (
    <div>
      {/* Subtab Selector */}
      <div className="card" style={{ padding: '0.75rem 1.25rem', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setActiveSubTab('HOST')}
              style={{
                padding: '0.35rem 0.85rem',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                background: activeSubTab === 'HOST' ? 'rgba(2, 132, 199, 0.2)' : 'var(--bg-secondary)',
                color: activeSubTab === 'HOST' ? 'var(--cyan-primary)' : 'var(--text-muted)',
                borderColor: activeSubTab === 'HOST' ? 'var(--cyan-primary)' : 'var(--border)',
                fontWeight: 600,
                fontSize: '0.8rem',
                cursor: 'pointer'
              }}
            >
              Host Audit Events ({hostEvents.length})
            </button>
            <button
              onClick={() => setActiveSubTab('NETWORK')}
              style={{
                padding: '0.35rem 0.85rem',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                background: activeSubTab === 'NETWORK' ? 'rgba(16, 185, 129, 0.2)' : 'var(--bg-secondary)',
                color: activeSubTab === 'NETWORK' ? 'var(--supported)' : 'var(--text-muted)',
                borderColor: activeSubTab === 'NETWORK' ? 'var(--supported)' : 'var(--border)',
                fontWeight: 600,
                fontSize: '0.8rem',
                cursor: 'pointer'
              }}
            >
              Network Packet Captures ({packets.length})
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Search size={14} color="var(--text-muted)" />
            <input
              type="text"
              placeholder={`Filter ${activeSubTab === 'HOST' ? 'processes, paths, IPs' : 'IPs, flags, summaries'}...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                padding: '0.35rem 0.65rem',
                fontSize: '0.8rem',
                color: '#fff',
                width: '240px'
              }}
            />
          </div>
        </div>
      </div>

      {/* Tables */}
      <div className="card" style={{ padding: 0 }}>
        {activeSubTab === 'HOST' ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Event ID</th>
                  <th>Action Type</th>
                  <th>Process</th>
                  <th>PID / PPID</th>
                  <th>File / Target</th>
                  <th>Socket 5-Tuple</th>
                  <th>Ret Code</th>
                  <th>Raw</th>
                </tr>
              </thead>
              <tbody>
                {filteredHostEvents.map((e) => (
                  <tr key={e.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{e.id}</td>
                    <td>
                      <span className="badge badge-neutral">{e.event_type}</span>
                    </td>
                    <td style={{ fontWeight: 500 }}>{e.process_name || 'N/A'}</td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                      {e.process_id !== null ? e.process_id : '?'}{e.parent_process_id ? ` (from ${e.parent_process_id})` : ''}
                    </td>
                    <td style={{ fontSize: '0.78rem', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {e.file_path || (e.dst_ip ? `${e.dst_ip}:${e.dst_port}` : '-')}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      {e.dst_ip ? `${e.src_ip || '*'}:${e.src_port || '*'} -> ${e.dst_ip}:${e.dst_port}` : '-'}
                    </td>
                    <td style={{ fontSize: '0.78rem' }}>{e.return_code}</td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.2rem 0.4rem', fontSize: '0.7rem' }}
                        onClick={() => setRawRecordModal(e.raw_record)}
                      >
                        JSON
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredHostEvents.length === 0 && (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                      No host provenance events recorded.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Frame ID</th>
                  <th>Timestamp</th>
                  <th>Protocol</th>
                  <th>Source</th>
                  <th>Destination</th>
                  <th>TCP Flags</th>
                  <th>Payload</th>
                  <th>Sensor ID</th>
                  <th>Summary</th>
                </tr>
              </thead>
              <tbody>
                {filteredPackets.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>{p.id}</td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {p.timestamp_iso ? new Date(p.timestamp_iso).toLocaleTimeString() : p.timestamp.toFixed(4)}
                    </td>
                    <td>
                      <span className="badge badge-neutral">{p.protocol}</span>
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.78rem' }}>
                      {p.src_ip}:{p.src_port}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.78rem' }}>
                      {p.dst_ip}:{p.dst_port}
                    </td>
                    <td>
                      {p.tcp_flags.map((f) => (
                        <span 
                          key={f} 
                          className="badge" 
                          style={{ 
                            marginRight: '3px', 
                            fontSize: '0.65rem',
                            background: f === 'RST' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(6, 182, 212, 0.15)',
                            color: f === 'RST' ? '#ef4444' : '#06b6d4'
                          }}
                        >
                          {f}
                        </span>
                      ))}
                    </td>
                    <td style={{ fontSize: '0.78rem' }}>{p.payload_len} B</td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{p.sensor_id}</td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{p.summary}</td>
                  </tr>
                ))}
                {filteredPackets.length === 0 && (
                  <tr>
                    <td colSpan={9} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                      No network packet capture frames recorded.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Raw Record Modal */}
      {rawRecordModal && (
        <div className="modal-overlay" onClick={() => setRawRecordModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="card-header">
              <div className="card-title">
                <Code size={18} color="var(--cyan-primary)" /> Raw Record Payload
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                onClick={() => setRawRecordModal(null)}
              >
                ✕
              </button>
            </div>
            <pre style={{ fontSize: '0.75rem', background: '#0a0e17', padding: '1rem', borderRadius: '4px', overflowX: 'auto', maxHeight: '350px' }}>
              {JSON.stringify(rawRecordModal, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
