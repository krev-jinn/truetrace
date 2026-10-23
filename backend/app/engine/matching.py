"""
TrueTrace Flow Matching & Temporal Correlation
Matches network-dependent claims against independent network packet records using defensible 5-tuple criteria.
"""

from typing import List, Dict, Any, Optional, Tuple
from ..models import NetworkClaim, NetworkPacket


class MatchedFlow:
    """Encapsulates packets correlated with a candidate claim and their directional semantics."""
    def __init__(self, claim: NetworkClaim):
        self.claim = claim
        self.client_to_server_packets: List[NetworkPacket] = []
        self.server_to_client_packets: List[NetworkPacket] = []
        self.all_matched_packets: List[NetworkPacket] = []
        self.has_syn: bool = False
        self.has_syn_ack: bool = False
        self.has_ack: bool = False
        self.has_rst: bool = False
        self.has_fin: bool = False
        self.total_payload_bytes: int = 0
        self.conflicting_events: List[str] = []


def is_packet_in_temporal_window(pkt_ts: float, claim_ts: float, tolerance_seconds: float) -> bool:
    """Checks whether packet timestamp falls within [claim_ts - tolerance, claim_ts + tolerance]."""
    return abs(pkt_ts - claim_ts) <= tolerance_seconds


def match_flow_packets(claim: NetworkClaim, packets: List[NetworkPacket]) -> MatchedFlow:
    """
    Correlates packet stream with a candidate claim based on 5-tuple (or wildcard client port)
    and temporal correlation tolerance.
    """
    flow = MatchedFlow(claim)
    
    for pkt in packets:
        # Check temporal window first
        if not is_packet_in_temporal_window(pkt.timestamp, claim.timestamp, claim.tolerance_seconds):
            continue

        # Check protocol
        if pkt.protocol.upper() != claim.protocol.upper():
            continue

        # Direction 1: Client -> Server (Forward)
        forward_match = (
            pkt.dst_ip == claim.dst_ip and
            pkt.dst_port == claim.dst_port and
            (claim.src_ip == "0.0.0.0" or pkt.src_ip == claim.src_ip) and
            (claim.src_port is None or pkt.src_port == claim.src_port)
        )

        # Direction 2: Server -> Client (Reverse / Response)
        reverse_match = (
            pkt.src_ip == claim.dst_ip and
            pkt.src_port == claim.dst_port and
            (claim.src_ip == "0.0.0.0" or pkt.dst_ip == claim.src_ip) and
            (claim.src_port is None or pkt.dst_port == claim.src_port)
        )

        if forward_match:
            flow.client_to_server_packets.append(pkt)
            flow.all_matched_packets.append(pkt)
            flow.total_payload_bytes += pkt.payload_len

            if "SYN" in pkt.tcp_flags and "ACK" not in pkt.tcp_flags:
                flow.has_syn = True
            if "ACK" in pkt.tcp_flags and "SYN" not in pkt.tcp_flags:
                flow.has_ack = True
            if "RST" in pkt.tcp_flags:
                flow.has_rst = True
                flow.conflicting_events.append(f"Client emitted RST at {pkt.timestamp_iso}")
            if "FIN" in pkt.tcp_flags:
                flow.has_fin = True

        elif reverse_match:
            flow.server_to_client_packets.append(pkt)
            flow.all_matched_packets.append(pkt)

            if "SYN" in pkt.tcp_flags and "ACK" in pkt.tcp_flags:
                flow.has_syn_ack = True
            if "ACK" in pkt.tcp_flags:
                flow.has_ack = True
            if "RST" in pkt.tcp_flags:
                flow.has_rst = True
                flow.conflicting_events.append(f"Server emitted RST (Refusal/Reset) at {pkt.timestamp_iso}")
            if "FIN" in pkt.tcp_flags:
                flow.has_fin = True

    return flow
