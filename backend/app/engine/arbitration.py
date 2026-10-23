"""
TrueTrace Falsification-Driven Invariant Arbitration Engine
Applies explicit formal transport invariants to arbitrate candidate host claims against network ground truth.
Produces three-valued verdicts: SUPPORTED, CONTRADICTED, UNRESOLVED.
"""

from typing import List, Optional
import uuid
from ..models import (
    NetworkClaim, NetworkPacket, SensorConfig, ArbitrationResult,
    Verdict, ObservabilityStatus, ClaimType
)
from .matching import match_flow_packets, MatchedFlow
from .observability import assess_sensor_observability


def arbitrate_claim(
    claim: NetworkClaim,
    packets: List[NetworkPacket],
    sensors: List[SensorConfig]
) -> ArbitrationResult:
    """
    Evaluates a candidate network-dependent claim against independent packet evidence and sensor coverage.
    """
    obs_status, sensor_id, obs_reasoning = assess_sensor_observability(claim, sensors)
    matched_flow: MatchedFlow = match_flow_packets(claim, packets)

    matched_pkt_ids = [p.id for p in matched_flow.all_matched_packets]
    matched_summaries = [p.summary for p in matched_flow.all_matched_packets]
    conflicting_pkt_ids = [p.id for p in matched_flow.all_matched_packets if "RST" in p.tcp_flags]

    ts_delta = None
    if matched_flow.all_matched_packets:
        first_pkt = matched_flow.all_matched_packets[0]
        ts_delta = round(first_pkt.timestamp - claim.timestamp, 4)

    # -------------------------------------------------------------------------
    # Preconditions: Sensor Observability Check
    # -------------------------------------------------------------------------
    if obs_status == ObservabilityStatus.UNOBSERVABLE:
        # If no packets observed AND flow was unobservable -> UNRESOLVED
        if not matched_flow.all_matched_packets:
            return ArbitrationResult(
                id=f"arb-{uuid.uuid4().hex[:8]}",
                claim_id=claim.id,
                investigation_id=claim.investigation_id,
                verdict=Verdict.UNRESOLVED,
                applied_rule="INV-OBS-02: Sensor Visibility Gap (Unobservable Flow)",
                reasoning=(
                    "Target communication was outside registered sensor topology or active capture window. "
                    "Under TrueTrace formal invariants, absence of network evidence cannot refute a host claim "
                    "unless observability is rigorously established."
                ),
                observability_status=obs_status,
                observability_reasoning=obs_reasoning,
                matching_packet_ids=[],
                conflicting_packet_ids=[],
                matching_evidence_summaries=[],
                timestamp_delta=None,
                sensor_id=None,
                epistemic_notes="Preserved hypothesis with explicit visibility gap warning. Do not discard candidate edge."
            )

    if obs_status == ObservabilityStatus.DEGRADED_VISIBILITY:
        if not matched_flow.all_matched_packets:
            return ArbitrationResult(
                id=f"arb-{uuid.uuid4().hex[:8]}",
                claim_id=claim.id,
                investigation_id=claim.investigation_id,
                verdict=Verdict.UNRESOLVED,
                applied_rule="INV-OBS-03: Degraded Sensor Telemetry (Packet Loss Flagged)",
                reasoning=(
                    "The monitoring sensor flagged hardware packet loss / buffer ring overflow during this capture window. "
                    "Missing packets may be artifacts of sensor loss rather than true non-occurrence."
                ),
                observability_status=obs_status,
                observability_reasoning=obs_reasoning,
                matching_packet_ids=[],
                conflicting_packet_ids=[],
                matching_evidence_summaries=[],
                timestamp_delta=None,
                sensor_id=sensor_id,
                epistemic_notes="Degraded sensor confidence. Verdict held in abeyance pending re-capture."
            )

    # -------------------------------------------------------------------------
    # TCP Handshake Claims
    # -------------------------------------------------------------------------
    if claim.claim_type == ClaimType.TCP_HANDSHAKE:
        # Check for explicit Connection Refusal / RST
        if matched_flow.has_rst:
            return ArbitrationResult(
                id=f"arb-{uuid.uuid4().hex[:8]}",
                claim_id=claim.id,
                investigation_id=claim.investigation_id,
                verdict=Verdict.CONTRADICTED,
                applied_rule="INV-TCP-02: Active Connection Refusal / RST Invariant",
                reasoning=(
                    f"Host audit log claimed connection to {claim.dst_ip}:{claim.dst_port} succeeded, "
                    f"but independent network capture recorded a TCP RST/ACK refusal from {claim.dst_ip}. "
                    f"The remote port was closed or blocked; no valid TCP session was established."
                ),
                observability_status=obs_status,
                observability_reasoning=obs_reasoning,
                matching_packet_ids=matched_pkt_ids,
                conflicting_packet_ids=conflicting_pkt_ids,
                matching_evidence_summaries=matched_summaries,
                timestamp_delta=ts_delta,
                sensor_id=sensor_id,
                epistemic_notes="Falsification confirmed: host OS socket request returned or buffered, but network rejected."
            )

        # Check for full 3-way handshake completion: SYN -> SYN-ACK -> ACK
        if matched_flow.has_syn and matched_flow.has_syn_ack and matched_flow.has_ack:
            return ArbitrationResult(
                id=f"arb-{uuid.uuid4().hex[:8]}",
                claim_id=claim.id,
                investigation_id=claim.investigation_id,
                verdict=Verdict.SUPPORTED,
                applied_rule="INV-TCP-01: Full Three-Way Handshake Invariant",
                reasoning=(
                    f"Full TCP 3-way handshake (SYN, SYN+ACK, ACK) verified across client and server. "
                    f"Independent network evidence conclusively confirms connection establishment to {claim.dst_ip}:{claim.dst_port}."
                ),
                observability_status=obs_status,
                observability_reasoning=obs_reasoning,
                matching_packet_ids=matched_pkt_ids,
                conflicting_packet_ids=[],
                matching_evidence_summaries=matched_summaries,
                timestamp_delta=ts_delta,
                sensor_id=sensor_id,
                epistemic_notes="Corroborated by bidirectional wire telemetry."
            )

        # Check for zero packets observed
        if not matched_flow.all_matched_packets:
            return ArbitrationResult(
                id=f"arb-{uuid.uuid4().hex[:8]}",
                claim_id=claim.id,
                investigation_id=claim.investigation_id,
                verdict=Verdict.UNRESOLVED,
                applied_rule="INV-OBS-01: Insufficient Evidence (Zero Packets Captured)",
                reasoning=(
                    f"No network packets observed for flow to {claim.dst_ip}:{claim.dst_port} within the temporal correlation window. "
                    f"Under TrueTrace epistemic principles, absence of packet telemetry cannot be treated as positive proof of non-occurrence."
                ),
                observability_status=obs_status,
                observability_reasoning=obs_reasoning,
                matching_packet_ids=[],
                conflicting_packet_ids=[],
                matching_evidence_summaries=[],
                timestamp_delta=None,
                sensor_id=sensor_id,
                epistemic_notes="Preserve uncertainty: do not prune candidate edge without positive contradictory evidence."
            )

        # Partial handshake (e.g. SYN sent, no SYN-ACK returned, but target didn't RST)
        return ArbitrationResult(
            id=f"arb-{uuid.uuid4().hex[:8]}",
            claim_id=claim.id,
            investigation_id=claim.investigation_id,
            verdict=Verdict.UNRESOLVED,
            applied_rule="INV-TCP-03: Incomplete Handshake Telemetry",
            reasoning=(
                f"Partial TCP telemetry observed for {claim.dst_ip}:{claim.dst_port}. "
                f"SYN observed: {matched_flow.has_syn}, SYN-ACK observed: {matched_flow.has_syn_ack}, "
                f"Handshake ACK observed: {matched_flow.has_ack}. Inconclusive proof of completed session."
            ),
            observability_status=obs_status,
            observability_reasoning=obs_reasoning,
            matching_packet_ids=matched_pkt_ids,
            conflicting_packet_ids=[],
            matching_evidence_summaries=matched_summaries,
            timestamp_delta=ts_delta,
            sensor_id=sensor_id,
            epistemic_notes="Handshake incomplete. Retain edge as unresolved."
        )

    # -------------------------------------------------------------------------
    # Data Transfer / Exfiltration Claims
    # -------------------------------------------------------------------------
    elif claim.claim_type == ClaimType.DATA_TRANSFER:
        # Check if session was reset before data could flow
        if matched_flow.has_rst and matched_flow.total_payload_bytes == 0:
            return ArbitrationResult(
                id=f"arb-{uuid.uuid4().hex[:8]}",
                claim_id=claim.id,
                investigation_id=claim.investigation_id,
                verdict=Verdict.CONTRADICTED,
                applied_rule="INV-DATA-02: Premature Termination Prior to Payload",
                reasoning=(
                    f"Host write() system call reported transmitting {claim.claimed_bytes or 'data'} bytes, "
                    f"but network capture recorded a TCP RST tearing down the socket before any data segments traversed the wire. "
                    f"Data remained isolated in the local kernel socket buffer."
                ),
                observability_status=obs_status,
                observability_reasoning=obs_reasoning,
                matching_packet_ids=matched_pkt_ids,
                conflicting_packet_ids=conflicting_pkt_ids,
                matching_evidence_summaries=matched_summaries,
                timestamp_delta=ts_delta,
                sensor_id=sensor_id,
                epistemic_notes="Crucial forensic insight: local write() != remote delivery."
            )

        # Check if data packets were observed AND acknowledged
        if matched_flow.total_payload_bytes > 0:
            # We have wire payload!
            # Did server acknowledge?
            server_acks = [p for p in matched_flow.server_to_client_packets if "ACK" in p.tcp_flags]
            if server_acks:
                return ArbitrationResult(
                    id=f"arb-{uuid.uuid4().hex[:8]}",
                    claim_id=claim.id,
                    investigation_id=claim.investigation_id,
                    verdict=Verdict.SUPPORTED,
                    applied_rule="INV-DATA-01: Acknowledged Transport Payload Invariant",
                    reasoning=(
                        f"Independent packet evidence confirmed delivery of {matched_flow.total_payload_bytes} payload bytes "
                        f"to {claim.dst_ip}:{claim.dst_port}, with TCP transport-layer acknowledgements returned by the receiver."
                    ),
                    observability_status=obs_status,
                    observability_reasoning=obs_reasoning,
                    matching_packet_ids=matched_pkt_ids,
                    conflicting_packet_ids=[],
                    matching_evidence_summaries=matched_summaries,
                    timestamp_delta=ts_delta,
                    sensor_id=sensor_id,
                    epistemic_notes="End-to-end transport delivery corroborated."
                )
            else:
                return ArbitrationResult(
                    id=f"arb-{uuid.uuid4().hex[:8]}",
                    claim_id=claim.id,
                    investigation_id=claim.investigation_id,
                    verdict=Verdict.UNRESOLVED,
                    applied_rule="INV-DATA-04: Unacknowledged Transport Segments",
                    reasoning=(
                        f"Outbound payload bytes ({matched_flow.total_payload_bytes} bytes) were seen on the wire, "
                        f"but no return TCP ACKs from {claim.dst_ip} were captured. Packet may have been dropped downstream."
                    ),
                    observability_status=obs_status,
                    observability_reasoning=obs_reasoning,
                    matching_packet_ids=matched_pkt_ids,
                    conflicting_packet_ids=[],
                    matching_evidence_summaries=matched_summaries,
                    timestamp_delta=ts_delta,
                    sensor_id=sensor_id,
                    epistemic_notes="Wire transmission observed, but reception unconfirmed."
                )

        if obs_status == ObservabilityStatus.FULLY_OBSERVABLE and matched_flow.total_payload_bytes == 0:
            return ArbitrationResult(
                id=f"arb-{uuid.uuid4().hex[:8]}",
                claim_id=claim.id,
                investigation_id=claim.investigation_id,
                verdict=Verdict.CONTRADICTED,
                applied_rule="INV-DATA-03: Zero Payload Transport Observed Under Full Observability",
                reasoning=(
                    f"Under full sensor visibility, zero payload bytes were observed for {claim.dst_ip}:{claim.dst_port}. "
                    f"The claimed exfiltration of {claim.claimed_bytes or 'data'} bytes did not occur across the network."
                ),
                observability_status=obs_status,
                observability_reasoning=obs_reasoning,
                matching_packet_ids=matched_pkt_ids,
                conflicting_packet_ids=[],
                matching_evidence_summaries=matched_summaries,
                timestamp_delta=ts_delta,
                sensor_id=sensor_id,
                epistemic_notes="Host-reported write() was discarded or buffered without wire transmission."
            )

    # -------------------------------------------------------------------------
    # Fallback Generic Network Claims
    # -------------------------------------------------------------------------
    if matched_flow.all_matched_packets:
        return ArbitrationResult(
            id=f"arb-{uuid.uuid4().hex[:8]}",
            claim_id=claim.id,
            investigation_id=claim.investigation_id,
            verdict=Verdict.SUPPORTED,
            applied_rule="INV-GEN-01: Correlated Flow Packets Observed",
            reasoning=f"Correlated packets ({len(matched_flow.all_matched_packets)}) observed within correlation tolerance.",
            observability_status=obs_status,
            observability_reasoning=obs_reasoning,
            matching_packet_ids=matched_pkt_ids,
            conflicting_packet_ids=[],
            matching_evidence_summaries=matched_summaries,
            timestamp_delta=ts_delta,
            sensor_id=sensor_id,
            epistemic_notes="General network correlation confirmed."
        )

    return ArbitrationResult(
        id=f"arb-{uuid.uuid4().hex[:8]}",
        claim_id=claim.id,
        investigation_id=claim.investigation_id,
        verdict=Verdict.UNRESOLVED,
        applied_rule="INV-GEN-02: Insufficient Corroborating Telemetry",
        reasoning=f"No matching network evidence observed for {claim.dst_ip}:{claim.dst_port} within time window.",
        observability_status=obs_status,
        observability_reasoning=obs_reasoning,
        matching_packet_ids=[],
        conflicting_packet_ids=[],
        matching_evidence_summaries=[],
        timestamp_delta=None,
        sensor_id=sensor_id,
        epistemic_notes="Preserve uncertainty."
    )
