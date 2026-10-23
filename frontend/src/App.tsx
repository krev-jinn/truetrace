import React, { useState, useEffect } from 'react';
import { 
  Shield, FileText, GitCommit, CheckCircle2, 
  Database, Radio, Play, Download, FolderSearch, Plus 
} from 'lucide-react';

import { Investigation, EvidenceFile } from './types';
import { 
  fetchInvestigations, fetchEvidenceFiles, createInvestigation 
} from './api';

import { Navbar } from './components/Navbar';
import { OverviewView } from './components/OverviewView';
import { AttackGraphView } from './components/AttackGraphView';
import { ClaimInspectorView } from './components/ClaimInspectorView';
import { EvidenceExplorerView } from './components/EvidenceExplorerView';
import { SensorsView } from './components/SensorsView';
import { ScenariosView } from './components/ScenariosView';
import { ReportView } from './components/ReportView';
import { InvestigationManagerView } from './components/InvestigationManagerView';

export function App() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [activeInvId, setActiveInvId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [evidenceFiles, setEvidenceFiles] = useState<EvidenceFile[]>([]);
  const [showNewModal, setShowNewModal] = useState<boolean>(false);
  const [newCaseName, setNewCaseName] = useState<string>('');
  const [newCaseDesc, setNewCaseDesc] = useState<string>('');

  const loadData = async () => {
    try {
      const invList = await fetchInvestigations();
      setInvestigations(invList);
      if (invList.length > 0) {
        if (!activeInvId || !invList.some((i) => i.id === activeInvId)) {
          setActiveInvId(invList[0].id);
        }
      }
    } catch (err) {
      console.error('Error fetching investigations:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (activeInvId) {
      fetchEvidenceFiles(activeInvId)
        .then(setEvidenceFiles)
        .catch(console.error);
    } else {
      setEvidenceFiles([]);
    }
  }, [activeInvId]);

  const activeInv = investigations.find((i) => i.id === activeInvId) || null;

  const handleScenarioExecuted = (newInvId: string) => {
    loadData();
    setActiveInvId(newInvId);
    setActiveTab('graph');
  };

  const handleCreateNewCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCaseName.trim()) return;
    try {
      const inv = await createInvestigation(newCaseName, newCaseDesc);
      setNewCaseName('');
      setNewCaseDesc('');
      setShowNewModal(false);
      await loadData();
      setActiveInvId(inv.id);
      setActiveTab('overview');
    } catch (err: any) {
      alert(`Error creating case: ${err.message}`);
    }
  };

  return (
    <div className="app-container">
      <Navbar
        investigations={investigations}
        activeInv={activeInv}
        onSelectInv={(id) => setActiveInvId(id)}
        onNewInvModal={() => setShowNewModal(true)}
        onRefresh={loadData}
      />

      {/* Primary Workbench Tab Navigation */}
      <nav className="nav-links">
        <button
          className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <FileText size={15} /> Overview & Sources
        </button>
        <button
          className={`nav-tab ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          <GitCommit size={15} /> Attack Graph
        </button>
        <button
          className={`nav-tab ${activeTab === 'claims' ? 'active' : ''}`}
          onClick={() => setActiveTab('claims')}
        >
          <CheckCircle2 size={15} /> Claim Inspector
        </button>
        <button
          className={`nav-tab ${activeTab === 'evidence' ? 'active' : ''}`}
          onClick={() => setActiveTab('evidence')}
        >
          <Database size={15} /> Evidence Explorer
        </button>
        <button
          className={`nav-tab ${activeTab === 'sensors' ? 'active' : ''}`}
          onClick={() => setActiveTab('sensors')}
        >
          <Radio size={15} /> Sensor Observability
        </button>
        <button
          className={`nav-tab ${activeTab === 'scenarios' ? 'active' : ''}`}
          onClick={() => setActiveTab('scenarios')}
        >
          <Play size={15} /> Scenario Runner
        </button>
        <button
          className={`nav-tab ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          <Download size={15} /> Report & Export
        </button>
        <button
          className={`nav-tab ${activeTab === 'cases' ? 'active' : ''}`}
          onClick={() => setActiveTab('cases')}
        >
          <FolderSearch size={15} /> Investigation Manager
        </button>
      </nav>

      {/* Main View Area */}
      <main className="main-content">
        {activeTab === 'overview' && (
          <OverviewView
            investigation={activeInv}
            evidenceFiles={evidenceFiles}
            onRefresh={loadData}
            onNavigateTab={setActiveTab}
          />
        )}

        {activeTab === 'graph' && activeInvId && (
          <AttackGraphView investigationId={activeInvId} />
        )}

        {activeTab === 'claims' && activeInvId && (
          <ClaimInspectorView investigationId={activeInvId} />
        )}

        {activeTab === 'evidence' && activeInvId && (
          <EvidenceExplorerView investigationId={activeInvId} />
        )}

        {activeTab === 'sensors' && activeInvId && (
          <SensorsView investigationId={activeInvId} />
        )}

        {activeTab === 'scenarios' && (
          <ScenariosView onScenarioExecuted={handleScenarioExecuted} />
        )}

        {activeTab === 'reports' && activeInvId && (
          <ReportView investigationId={activeInvId} />
        )}

        {activeTab === 'cases' && (
          <InvestigationManagerView
            investigations={investigations}
            activeInvId={activeInvId}
            onSelectInv={(id) => setActiveInvId(id)}
            onRefresh={loadData}
          />
        )}
      </main>

      {/* Global Quick Create Case Modal */}
      {showNewModal && (
        <div className="modal-overlay" onClick={() => setShowNewModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="card-header">
              <div className="card-title">
                <img src="/truetrace_icon.png" alt="TrueTrace" style={{ height: '22px', width: 'auto' }} /> Initialize New Investigation Case
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                onClick={() => setShowNewModal(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateNewCase}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Case Identifier / Name:
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Case-2026-001: APT34 Exfiltration Probe"
                  value={newCaseName}
                  onChange={(e) => setNewCaseName(e.target.value)}
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

              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  Research Hypothesis & Case Description:
                </label>
                <textarea
                  rows={3}
                  placeholder="Notes on host endpoint audit logs, suspected network activity, and sensor topology."
                  value={newCaseDesc}
                  onChange={(e) => setNewCaseDesc(e.target.value)}
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

              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                Initialize Investigation
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
