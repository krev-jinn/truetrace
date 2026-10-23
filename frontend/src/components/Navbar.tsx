import React from 'react';
import { Plus, RefreshCw, FolderSearch } from 'lucide-react';
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
        <img 
          src="/truetrace_logo.png" 
          alt="TrueTrace — From Logs To Truth" 
          style={{ height: '46px', width: 'auto', objectFit: 'contain' }}
        />
        <div style={{ borderLeft: '1px solid var(--border)', paddingLeft: '0.75rem', marginLeft: '0.25rem' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--cyan-primary)', letterSpacing: '0.08em' }}>
            VERIFICATION WORKBENCH
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Observability-Aware Invariant Arbitration
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
