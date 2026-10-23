export type Verdict = 'SUPPORTED' | 'CONTRADICTED' | 'UNRESOLVED';

export type ClaimType = 'TCP_HANDSHAKE' | 'DATA_TRANSFER' | 'COMMAND_AND_CONTROL' | 'CONNECTION_PROBE' | 'GENERIC_NETWORK';

export type HostEventType = 'PROCESS_SPAWN' | 'FILE_READ' | 'FILE_WRITE' | 'SOCKET_CONNECT' | 'SOCKET_SEND' | 'SOCKET_RECV' | 'SOCKET_CLOSE' | 'FIREWALL_DROP';

export type ObservabilityStatus = 'FULLY_OBSERVABLE' | 'DEGRADED_VISIBILITY' | 'UNOBSERVABLE';

export type EvidenceType = 'HOST_AUDIT_LOG' | 'PCAP_CAPTURE' | 'FIREWALL_LOG' | 'CONTROLLED_EXPERIMENT';

export interface Investigation {
  id: string;
  name: string;
  description: string;
  created_at: string;
  status: string;
  stats: {
    evidence_files?: number;
    host_events?: number;
    network_packets?: number;
    claims?: number;
    supported?: number;
    contradicted?: number;
    unresolved?: number;
  };
}

export interface EvidenceFile {
  id: string;
  investigation_id: string;
  file_name: string;
  file_path: string;
  evidence_type: EvidenceType;
  file_size_bytes: number;
  sha256_hash: string;
  recorded_at: string;
  ingested_at: string;
  description: string;
  metadata: Record<string, any>;
}

export interface SensorConfig {
  id: string;
  investigation_id: string;
  sensor_name: string;
  interface: string;
  monitored_cidrs: string[];
  capture_start?: string | null;
  capture_end?: string | null;
  packet_loss_detected: boolean;
  status: string;
  notes: string;
}

export interface HostEvent {
  id: string;
  investigation_id: string;
  evidence_id: string;
  timestamp: number;
  timestamp_iso: string;
  event_type: HostEventType;
  process_id?: number | null;
  process_name?: string | null;
  parent_process_id?: number | null;
  file_path?: string | null;
  src_ip?: string | null;
  src_port?: number | null;
  dst_ip?: string | null;
  dst_port?: number | null;
  protocol?: string | null;
  bytes_count?: number;
  return_code?: number;
  raw_record: Record<string, any>;
}

export interface NetworkPacket {
  id: string;
  investigation_id: string;
  evidence_id: string;
  timestamp: number;
  timestamp_iso: string;
  src_ip: string;
  src_port: number;
  dst_ip: string;
  dst_port: number;
  protocol: string;
  tcp_flags: string[];
  seq_num?: number | null;
  ack_num?: number | null;
  payload_len: number;
  sensor_id?: string;
  summary: string;
}

export interface NetworkClaim {
  id: string;
  investigation_id: string;
  source_event_id: string;
  claim_type: ClaimType;
  src_ip: string;
  src_port?: number | null;
  dst_ip: string;
  dst_port: number;
  protocol: string;
  timestamp: number;
  timestamp_iso: string;
  tolerance_seconds: number;
  claimed_bytes?: number | null;
  candidate_edge_id?: string | null;
  description: string;
}

export interface ArbitrationResult {
  id: string;
  claim_id: string;
  investigation_id: string;
  verdict: Verdict;
  applied_rule: string;
  reasoning: string;
  observability_status: ObservabilityStatus;
  observability_reasoning: string;
  matching_packet_ids: string[];
  conflicting_packet_ids: string[];
  matching_evidence_summaries: string[];
  timestamp_delta?: number | null;
  sensor_id?: string | null;
  epistemic_notes: string;
}

export interface GraphNodeData {
  id: string;
  label: string;
  nodeType: string;
  properties: Record<string, any>;
}

export interface GraphEdgeData {
  id: string;
  relation: string;
  isNetworkDependent: boolean;
  claimId?: string;
  verdict?: string;
  appliedRule?: string;
  reasoning?: string;
  properties: Record<string, any>;
}

export interface FlowGraphResponse {
  graphType: 'CANDIDATE' | 'REFINED';
  investigationId: string;
  nodes: any[];
  edges: any[];
  metadata: Record<string, any>;
}

export interface ScenarioMeta {
  id: string;
  title: string;
  type: string;
  expected_verdict: string;
  description: string;
}
