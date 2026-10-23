import React, { useState } from 'react';
import { 
  FolderPlus, Trash2, ArrowRight, Calendar, Activity, 
  FolderSearch, Plus 
} from 'lucide-react';
import { Investigation } from '../types';
import { createInvestigation, deleteInvestigation } from '../api';

interface InvestigationManagerViewProps {
  investigations: Investigation[];
  activeInvId: string | null;
  onSelectInv: (id: string) => void;
  onRefresh: () => void;
}

export const InvestigationManagerView: React.FC<InvestigationManagerViewProps> = ({
  investigations,
  activeInvId,
  onSelectInv,
  onRefresh
}) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    try {
      const inv = await createInvestigation(name, desc);
      setName('');
      setDesc('');
      setShowCreateModal(false);
      onRefresh();
      onSelectInv(inv.id);
    } catch (err: any) {
      alert(`Creation error: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete investigation '${name}'?`)) return;
    try {
      await deleteInvestigation(id);
      onRefresh();
    } catch (err: any) {
      alert(`Delete error: ${err.message}`);
    }
  };

  return (
    <div>
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <FolderSearch size={18} color="var(--cyan-primary)" /> Investigation Workspaces
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            <Plus size={14} /> New Investigation
          </button>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Investigation Name</th>
                <th>Case ID</th>
                <th>Created At</th>
                <th>Status</th>
                <th>Evidence Files</th>
                <th>Claims</th>
                <th>Arbitration Verdicts</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {investigations.map((inv) => {
                const isActive = inv.id === activeInvId;
                const stats = inv.stats || {};
                return (
                  <tr key={inv.id} style={{ background: isActive ? 'rgba(6, 182, 212, 0.05)' : undefined }}>
                    <td style={{ fontWeight: 600, color: isActive ? 'var(--cyan-primary)' : '#fff' }}>
                      {inv.name}
                      {isActive && <span className="badge badge-neutral" style={{ marginLeft: '8px' }}>ACTIVE</span>}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.78rem' }}>{inv.id}</td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      {new Date(inv.created_at).toLocaleString()}
                    </td>
                    <td>
                      <span className="badge badge-supported">{inv.status}</span>
                    </td>
                    <td>{stats.evidence_files || 0}</td>
                    <td>{stats.claims || 0}</td>
                    <td>
                      <span style={{ color: 'var(--supported)', marginRight: '6px' }}>{stats.supported || 0}S</span>
                      <span style={{ color: 'var(--contradicted)', marginRight: '6px' }}>{stats.contradicted || 0}C</span>
                      <span style={{ color: 'var(--unresolved)' }}>{stats.unresolved || 0}U</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
                        {!isActive && (
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
                            onClick={() => onSelectInv(inv.id)}
                          >
                            Switch To
                          </button>
                        )}
                        <button
                          className="btn btn-danger"
                          style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
                          onClick={() => handleDelete(inv.id, inv.name)}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {investigations.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No investigations created yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="card-header">
              <div className="card-title">
                <FolderPlus size={18} color="var(--cyan-primary)" /> Create New Investigation Case
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                onClick={() => setShowCreateModal(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreate}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Investigation Title:
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Incident-2026-042: Edge Gateway Exfiltration"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    color: '#fff',
                    fontSize: '0.85rem'
                  }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Case Notes / Research Context:
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. DARPA TC CADETS host logs paired with switch tap packet captures."
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    color: '#fff',
                    fontSize: '0.85rem'
                  }}
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={creating}>
                {creating ? 'Initializing...' : 'Create Case'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
