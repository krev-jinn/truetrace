import React, { useState, useEffect, useMemo } from 'react';
import { 
  ReactFlow, Background, Controls, MiniMap, Node, Edge,
  Handle, Position, useNodesState, useEdgesState
} from '@xyflow/react';
import { 
  GitCommit, CheckCircle2, XCircle, HelpCircle, 
  Info, Cpu, FileCode, Globe, ShieldAlert, ArrowRight, RefreshCw
} from 'lucide-react';
import { fetchCandidateGraph, fetchRefinedGraph } from '../api';
import { FlowGraphResponse } from '../types';

interface AttackGraphViewProps {
  investigationId: string;
}

// Custom Node Component
const CustomNode = ({ data }: { data: any }) => {
  const nodeType = data.nodeType || 'PROCESS';
  
  let borderColor = '#0284c7';
  let Icon = Cpu;
  let typeLabel = 'PROCESS';

  if (nodeType === 'FILE') {
    borderColor = '#f59e0b';
    Icon = FileCode;
    typeLabel = 'FILE';
  } else if (nodeType === 'ENDPOINT') {
    borderColor = '#10b981';
    Icon = Globe;
    typeLabel = 'NETWORK ENDPOINT';
  }

  return (
    <div 
      className="flow-node"
      style={{ borderLeft: `4px solid ${borderColor}`, minWidth: '190px' }}
    >
      <Handle type="target" position={Position.Left} style={{ background: borderColor }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '4px' }}>
        <Icon size={14} color={borderColor} />
        <span style={{ fontSize: '0.68rem', fontWeight: 700, color: borderColor, textTransform: 'uppercase' }}>
          {typeLabel}
        </span>
      </div>
      <div className="flow-node-title" style={{ fontSize: '0.85rem' }}>{data.label}</div>
      <div className="flow-node-sub">ID: {data.id}</div>
      <Handle type="source" position={Position.Right} style={{ background: borderColor }} />
    </div>
  );
};

export const AttackGraphView: React.FC<AttackGraphViewProps> = ({ investigationId }) => {
  const [graphMode, setGraphMode] = useState<'CANDIDATE' | 'REFINED'>('REFINED');
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedItem, setSelectedItem] = useState<{ type: 'node' | 'edge'; data: any } | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const nodeTypes = useMemo(() => ({ customNode: CustomNode }), []);

  const loadGraph = async (mode: 'CANDIDATE' | 'REFINED') => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const graphData: FlowGraphResponse = mode === 'CANDIDATE' 
        ? await fetchCandidateGraph(investigationId)
        : await fetchRefinedGraph(investigationId);
      
      setNodes(graphData.nodes || []);
      setEdges(graphData.edges || []);
      setSelectedItem(null);
    } catch (err: any) {
      if (mode === 'REFINED') {
        // Fallback to candidate if refined not yet generated
        try {
          const cand = await fetchCandidateGraph(investigationId);
          setNodes(cand.nodes || []);
          setEdges(cand.edges || []);
          setGraphMode('CANDIDATE');
        } catch {
          setErrorMsg('No attack graph generated yet. Upload host audit logs or run a scenario.');
        }
      } else {
        setErrorMsg('Failed to load candidate graph. Ingest host provenance first.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (investigationId) {
      loadGraph(graphMode);
    }
  }, [investigationId, graphMode]);

  const onNodeClick = (_: any, node: Node) => {
    setSelectedItem({ type: 'node', data: node.data });
  };

  const onEdgeClick = (_: any, edge: Edge) => {
    setSelectedItem({ type: 'edge', data: edge.data });
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedItem ? '1fr 360px' : '1fr', gap: '1.25rem' }}>
      <div>
        {/* Graph Header Toolbar */}
        <div className="card" style={{ padding: '0.75rem 1.25rem', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ display: 'flex', background: 'var(--bg-secondary)', borderRadius: '6px', padding: '3px', border: '1px solid var(--border)' }}>
                <button
                  onClick={() => setGraphMode('CANDIDATE')}
                  style={{
                    padding: '0.35rem 0.85rem',
                    borderRadius: '4px',
                    border: 'none',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: graphMode === 'CANDIDATE' ? '#0284c7' : 'transparent',
                    color: graphMode === 'CANDIDATE' ? '#fff' : 'var(--text-muted)'
                  }}
                >
                  Candidate Graph (Hypotheses)
                </button>
                <button
                  onClick={() => setGraphMode('REFINED')}
                  style={{
                    padding: '0.35rem 0.85rem',
                    borderRadius: '4px',
                    border: 'none',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    background: graphMode === 'REFINED' ? '#059669' : 'transparent',
                    color: graphMode === 'REFINED' ? '#fff' : 'var(--text-muted)'
                  }}
                >
                  Refined Graph (Arbitrated)
                </button>
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                {nodes.length} Nodes &bull; {edges.length} Edges
              </div>

              <button
                className="btn btn-secondary"
                style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                onClick={() => loadGraph(graphMode)}
                title="Reload current graph state"
              >
                <RefreshCw size={12} className={loading ? 'spin' : ''} /> Refresh Graph
              </button>
            </div>

            {/* Invariant Legend */}
            <div style={{ display: 'flex', gap: '0.85rem', fontSize: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: '16px', height: '3px', background: 'var(--supported)', display: 'inline-block' }}></span>
                <span>Supported (Retained)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: '16px', height: '3px', background: 'var(--contradicted)', display: 'inline-block', borderBottom: '2px dashed #ef4444' }}></span>
                <span>Contradicted (Falsified)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: '16px', height: '3px', background: 'var(--unresolved)', display: 'inline-block', borderBottom: '2px dotted #f59e0b' }}></span>
                <span>Unresolved (Preserved)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Canvas */}
        <div className="graph-canvas-wrapper">
          {errorMsg ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
              <ShieldAlert size={36} color="var(--unresolved)" style={{ marginBottom: '0.5rem' }} />
              <p>{errorMsg}</p>
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              onEdgeClick={onEdgeClick}
              fitView
            >
              <Background color="#1e293b" gap={16} />
              <Controls />
              <MiniMap 
                nodeColor={(n: any) => {
                  if (n.data?.nodeType === 'PROCESS') return '#0284c7';
                  if (n.data?.nodeType === 'FILE') return '#f59e0b';
                  return '#10b981';
                }}
                style={{ background: '#0f172a' }}
              />
            </ReactFlow>
          )}
        </div>
      </div>

      {/* Inspector Drawer */}
      {selectedItem && (
        <div className="card" style={{ height: 'fit-content' }}>
          <div className="card-header">
            <div className="card-title">
              <Info size={16} color="var(--cyan-primary)" />
              {selectedItem.type === 'edge' ? 'Edge Verdict Inspector' : 'Node Inspector'}
            </div>
            <button 
              className="btn btn-secondary" 
              style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
              onClick={() => setSelectedItem(null)}
            >
              ✕
            </button>
          </div>

          {selectedItem.type === 'edge' ? (
            <div>
              <div style={{ marginBottom: '0.85rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Relation</span>
                <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff' }}>
                  {selectedItem.data.relation}
                </span>
              </div>

              {selectedItem.data.verdict && (
                <div style={{ marginBottom: '0.85rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Arbitration Verdict</span>
                  <span className={`badge badge-${selectedItem.data.verdict.toLowerCase()}`}>
                    {selectedItem.data.verdict === 'SUPPORTED' && <CheckCircle2 size={12} />}
                    {selectedItem.data.verdict === 'CONTRADICTED' && <XCircle size={12} />}
                    {selectedItem.data.verdict === 'UNRESOLVED' && <HelpCircle size={12} />}
                    {selectedItem.data.verdict}
                  </span>
                </div>
              )}

              {selectedItem.data.appliedRule && (
                <div style={{ marginBottom: '0.85rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Applied Invariant Rule</span>
                  <code style={{ fontSize: '0.78rem', color: 'var(--cyan-primary)', background: '#0a101f', padding: '2px 6px', borderRadius: '4px' }}>
                    {selectedItem.data.appliedRule}
                  </code>
                </div>
              )}

              {selectedItem.data.reasoning && (
                <div style={{ marginBottom: '0.85rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Verdict Reasoning</span>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.4, background: 'var(--bg-secondary)', padding: '0.6rem', borderRadius: '4px' }}>
                    {selectedItem.data.reasoning}
                  </p>
                </div>
              )}

              {selectedItem.data.properties?.observability_status && (
                <div style={{ marginBottom: '0.85rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Sensor Observability</span>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                    Status: <strong>{selectedItem.data.properties.observability_status}</strong>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {selectedItem.data.properties.observability_reasoning}
                  </div>
                </div>
              )}

              {selectedItem.data.properties?.epistemic_notes && (
                <div style={{ marginBottom: '0.85rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Epistemic Notes</span>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                    {selectedItem.data.properties.epistemic_notes}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: '0.85rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Label</span>
                <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff' }}>
                  {selectedItem.data.label}
                </span>
              </div>
              <div style={{ marginBottom: '0.85rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Node Type</span>
                <span className="badge badge-neutral">{selectedItem.data.nodeType}</span>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Properties</span>
                <pre style={{ fontSize: '0.75rem', background: '#0a101f', padding: '0.5rem', borderRadius: '4px', overflowX: 'auto' }}>
                  {JSON.stringify(selectedItem.data.properties || {}, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
