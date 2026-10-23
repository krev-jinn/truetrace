import {
  Investigation, EvidenceFile, SensorConfig, HostEvent,
  NetworkPacket, NetworkClaim, ArbitrationResult, FlowGraphResponse, ScenarioMeta
} from './types';

const API_BASE = '/api';

export async function fetchInvestigations(): Promise<Investigation[]> {
  const res = await fetch(`${API_BASE}/investigations`);
  if (!res.ok) throw new Error('Failed to fetch investigations');
  return res.json();
}

export async function createInvestigation(name: string, description: string): Promise<Investigation> {
  const res = await fetch(`${API_BASE}/investigations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description })
  });
  if (!res.ok) throw new Error('Failed to create investigation');
  return res.json();
}

export async function fetchInvestigation(id: string): Promise<Investigation> {
  const res = await fetch(`${API_BASE}/investigations/${id}`);
  if (!res.ok) throw new Error('Failed to fetch investigation');
  return res.json();
}

export async function deleteInvestigation(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/investigations/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete investigation');
}

export async function fetchEvidenceFiles(invId: string): Promise<EvidenceFile[]> {
  const res = await fetch(`${API_BASE}/evidence/${invId}`);
  if (!res.ok) throw new Error('Failed to fetch evidence files');
  return res.json();
}

export async function uploadEvidenceFile(invId: string, file: File, description = ''): Promise<any> {
  const formData = new FormData();
  formData.append('investigation_id', invId);
  formData.append('description', description);
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/evidence/upload`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload evidence');
  return res.json();
}

export async function fetchHostEvents(invId: string): Promise<HostEvent[]> {
  const res = await fetch(`${API_BASE}/evidence/host-events/${invId}`);
  if (!res.ok) throw new Error('Failed to fetch host events');
  return res.json();
}

export async function fetchNetworkPackets(invId: string): Promise<NetworkPacket[]> {
  const res = await fetch(`${API_BASE}/evidence/packets/${invId}`);
  if (!res.ok) throw new Error('Failed to fetch network packets');
  return res.json();
}

export async function fetchSensors(invId: string): Promise<SensorConfig[]> {
  const res = await fetch(`${API_BASE}/sensors/${invId}`);
  if (!res.ok) throw new Error('Failed to fetch sensors');
  return res.json();
}

export async function updateSensor(sensorId: string, sensor: SensorConfig): Promise<SensorConfig> {
  const res = await fetch(`${API_BASE}/sensors/${sensorId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sensor)
  });
  if (!res.ok) throw new Error('Failed to update sensor');
  return res.json();
}

export async function fetchClaims(invId: string): Promise<NetworkClaim[]> {
  const res = await fetch(`${API_BASE}/arbitration/claims/${invId}`);
  if (!res.ok) throw new Error('Failed to fetch claims');
  return res.json();
}

export async function fetchArbitrationResults(invId: string): Promise<ArbitrationResult[]> {
  const res = await fetch(`${API_BASE}/arbitration/results/${invId}`);
  if (!res.ok) throw new Error('Failed to fetch arbitration results');
  return res.json();
}

export async function runArbitration(invId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/arbitration/run/${invId}`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run arbitration');
  return res.json();
}

export async function fetchCandidateGraph(invId: string): Promise<FlowGraphResponse> {
  const res = await fetch(`${API_BASE}/graphs/${invId}/candidate`);
  if (!res.ok) throw new Error('Failed to fetch candidate graph');
  return res.json();
}

export async function fetchRefinedGraph(invId: string): Promise<FlowGraphResponse> {
  const res = await fetch(`${API_BASE}/graphs/${invId}/refined`);
  if (!res.ok) throw new Error('Failed to fetch refined graph');
  return res.json();
}

export async function fetchScenarios(): Promise<ScenarioMeta[]> {
  const res = await fetch(`${API_BASE}/scenarios`);
  if (!res.ok) throw new Error('Failed to fetch scenarios');
  return res.json();
}

export async function runScenario(scenarioId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/scenarios/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario_id: scenarioId })
  });
  if (!res.ok) throw new Error('Failed to execute scenario');
  return res.json();
}

export async function fetchReportMarkdown(invId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/reports/${invId}/markdown`);
  if (!res.ok) throw new Error('Failed to fetch report markdown');
  return res.text();
}

export async function fetchReportJson(invId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/reports/${invId}/json`);
  if (!res.ok) throw new Error('Failed to fetch report json');
  return res.json();
}
