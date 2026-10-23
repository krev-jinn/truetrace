"""
TrueTrace Data Models & Type Definitions
Core schemas for forensic events, network claims, sensor observability, and arbitration results.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import datetime


class Verdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNRESOLVED = "UNRESOLVED"


class ClaimType(str, Enum):
    TCP_HANDSHAKE = "TCP_HANDSHAKE"
    DATA_TRANSFER = "DATA_TRANSFER"
    COMMAND_AND_CONTROL = "COMMAND_AND_CONTROL"
    CONNECTION_PROBE = "CONNECTION_PROBE"
    GENERIC_NETWORK = "GENERIC_NETWORK"


class HostEventType(str, Enum):
    PROCESS_SPAWN = "PROCESS_SPAWN"
    FILE_READ = "FILE_READ"
    FILE_WRITE = "FILE_WRITE"
    SOCKET_CONNECT = "SOCKET_CONNECT"
    SOCKET_SEND = "SOCKET_SEND"
    SOCKET_RECV = "SOCKET_RECV"
    SOCKET_CLOSE = "SOCKET_CLOSE"
    FIREWALL_DROP = "FIREWALL_DROP"


class ObservabilityStatus(str, Enum):
    FULLY_OBSERVABLE = "FULLY_OBSERVABLE"
    DEGRADED_VISIBILITY = "DEGRADED_VISIBILITY"
    UNOBSERVABLE = "UNOBSERVABLE"


class EvidenceType(str, Enum):
    HOST_AUDIT_LOG = "HOST_AUDIT_LOG"
    PCAP_CAPTURE = "PCAP_CAPTURE"
    FIREWALL_LOG = "FIREWALL_LOG"
    CONTROLLED_EXPERIMENT = "CONTROLLED_EXPERIMENT"


class NodeType(str, Enum):
    PROCESS = "PROCESS"
    FILE = "FILE"
    ENDPOINT = "ENDPOINT"
    SOCKET = "SOCKET"


# -------------------------------------------------------------------------
# Core Investigation & Evidence Schemas
# -------------------------------------------------------------------------

class InvestigationCreate(BaseModel):
    name: str = Field(..., description="Unique investigation name")
    description: str = Field("", description="Contextual case notes")


class Investigation(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    status: str = "ACTIVE"
    stats: Dict[str, Any] = Field(default_factory=dict)


class EvidenceFile(BaseModel):
    id: str
    investigation_id: str
    file_name: str
    file_path: str
    evidence_type: EvidenceType
    file_size_bytes: int
    sha256_hash: str
    recorded_at: str
    ingested_at: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SensorConfig(BaseModel):
    id: str
    investigation_id: str
    sensor_name: str
    interface: str = "eth0"
    monitored_cidrs: List[str] = Field(default_factory=list, description="List of CIDRs e.g. ['192.168.1.0/24']")
    capture_start: Optional[str] = None
    capture_end: Optional[str] = None
    packet_loss_detected: bool = False
    status: str = "ACTIVE"
    notes: str = ""


# -------------------------------------------------------------------------
# Parsed Records: Host Events & Network Packets
# -------------------------------------------------------------------------

class HostEvent(BaseModel):
    id: str
    investigation_id: str
    evidence_id: str
    timestamp: float  # Unix timestamp in seconds
    timestamp_iso: str
    event_type: HostEventType
    process_id: Optional[int] = None
    process_name: Optional[str] = None
    parent_process_id: Optional[int] = None
    file_path: Optional[str] = None
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_ip: Optional[str] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = "TCP"
    bytes_count: Optional[int] = 0
    return_code: Optional[int] = 0
    raw_record: Dict[str, Any] = Field(default_factory=dict)


class NetworkPacket(BaseModel):
    id: str
    investigation_id: str
    evidence_id: str
    timestamp: float  # Unix timestamp in seconds
    timestamp_iso: str
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: str = "TCP"
    tcp_flags: List[str] = Field(default_factory=list, description="['SYN', 'ACK', 'RST', 'FIN', 'PSH']")
    seq_num: Optional[int] = None
    ack_num: Optional[int] = None
    payload_len: int = 0
    sensor_id: Optional[str] = "default-sensor"
    summary: str = ""


# -------------------------------------------------------------------------
# Claims & Arbitration
# -------------------------------------------------------------------------

class NetworkClaim(BaseModel):
    id: str
    investigation_id: str
    source_event_id: str
    claim_type: ClaimType
    src_ip: str
    src_port: Optional[int] = None
    dst_ip: str
    dst_port: int
    protocol: str = "TCP"
    timestamp: float
    timestamp_iso: str
    tolerance_seconds: float = 3.0
    claimed_bytes: Optional[int] = None
    candidate_edge_id: Optional[str] = None
    description: str


class ArbitrationResult(BaseModel):
    id: str
    claim_id: str
    investigation_id: str
    verdict: Verdict
    applied_rule: str
    reasoning: str
    observability_status: ObservabilityStatus
    observability_reasoning: str
    matching_packet_ids: List[str] = Field(default_factory=list)
    conflicting_packet_ids: List[str] = Field(default_factory=list)
    matching_evidence_summaries: List[str] = Field(default_factory=list)
    timestamp_delta: Optional[float] = None
    sensor_id: Optional[str] = None
    epistemic_notes: str = ""


# -------------------------------------------------------------------------
# Attack Graph Representation
# -------------------------------------------------------------------------

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: NodeType
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str
    is_network_dependent: bool = False
    claim_id: Optional[str] = None
    verdict: Optional[Verdict] = None
    applied_rule: Optional[str] = None
    reasoning: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class AttackGraph(BaseModel):
    investigation_id: str
    graph_type: str  # "CANDIDATE" or "REFINED"
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = Field(default_factory=dict)
