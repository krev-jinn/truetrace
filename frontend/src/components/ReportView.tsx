import React, { useState, useEffect } from 'react';
import { 
  FileText, Download, Copy, Check, RefreshCw 
} from 'lucide-react';
import { fetchReportMarkdown, fetchReportJson } from '../api';

interface ReportViewProps {
  investigationId: string;
}

export const ReportView: React.FC<ReportViewProps> = ({ investigationId }) => {
  const [markdown, setMarkdown] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const loadReport = () => {
    if (investigationId) {
      setLoading(true);
      fetchReportMarkdown(investigationId)
        .then(setMarkdown)
        .catch((err) => setMarkdown(`Error generating report: ${err.message}`))
        .finally(() => setLoading(false));
    }
  };

  useEffect(() => {
    loadReport();
  }, [investigationId]);

  const handleCopy = () => {
    navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMd = () => {
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `truetrace_report_${investigationId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJson = async () => {
    try {
      const data = await fetchReportJson(investigationId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `truetrace_investigation_${investigationId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(`Export error: ${err.message}`);
    }
  };

  return (
    <div>
      {/* Action Toolbar */}
      <div className="card" style={{ padding: '0.75rem 1.25rem', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={18} color="var(--cyan-primary)" />
            <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff' }}>
              Forensic Report Preview
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-secondary" onClick={loadReport} disabled={loading}>
              <RefreshCw size={14} /> Refresh
            </button>
            <button className="btn btn-secondary" onClick={handleCopy}>
              {copied ? <Check size={14} color="var(--supported)" /> : <Copy size={14} />}
              {copied ? 'Copied' : 'Copy Markdown'}
            </button>
            <button className="btn btn-secondary" onClick={handleDownloadMd}>
              <Download size={14} /> Download .MD
            </button>
            <button className="btn btn-primary" onClick={handleDownloadJson}>
              <Download size={14} /> Export Full JSON
            </button>
          </div>
        </div>
      </div>

      {/* Markdown Content */}
      <div className="card" style={{ background: '#090d16', padding: '1.5rem', maxHeight: '680px', overflowY: 'auto' }}>
        <pre style={{ 
          fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
          fontSize: '0.82rem', 
          color: '#cbd5e1', 
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word'
        }}>
          {markdown || (loading ? 'Synthesizing report...' : 'No report data available.')}
        </pre>
      </div>
    </div>
  );
};
