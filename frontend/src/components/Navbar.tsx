import React from 'react';
import { Shield, Activity, Plus, RefreshCw, FolderSearch } from 'lucide-react';
import { Investigation } from '../types';

interface NavbarProps {
  investigations: Investigation[];
  activeInv: Investigation | null;
  onSelectInv: (id: string) => void;
  onNewInvModal: () => void;
  onRefresh: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  investigations,
  activeInv,
  onSelectInv,
  onNewInvModal,
  onRefresh
}) => {
  return (
    <header className="top-navbar">
      <div className="brand-section">
        <div className="brand-logo">
          <Shield size={22} />
        </div>
        <div>
          <div className="brand-title">
            TrueTrace <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--cyan-primary)' }}>v1.0-RESEARCH</span>
          </div>
          <div className="brand-subtitle">
            Network-Grounded Attack Trace Verification & Invariant Arbitration
          </div>
        </div>
      </div>

      <div className="case-selector-container">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FolderSearch size={16} color="var(--text-muted)" />
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500 }}>Active Case:</label>
          <select
            value={activeInv?.id || ''}
            onChange={(e) => onSelectInv(e.target.value)}
            style={{
              background: 'var(--bg-card)',
              color: 'var(--text-main)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '0.4rem 0.75rem',
              fontSize: '0.85rem',
              outline: 'none',
              maxWidth: '260px'
            }}
          >
            {investigations.map((inv) => (
              <option key={inv.id} value={inv.id}>
                {inv.name} ({inv.id})
              </option>
            ))}
            {investigations.length === 0 && <option value="">No Investigations</option>}
          </select>
        </div>

        <button className="btn btn-secondary" onClick={onRefresh} title="Refresh data">
          <RefreshCw size={14} />
        </button>

        <button className="btn btn-primary" onClick={onNewInvModal}>
          <Plus size={14} /> New Case
        </button>
      </div>
    </header>
  );
};
