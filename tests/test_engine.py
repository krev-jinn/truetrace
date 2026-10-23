"""
Unit Tests for TrueTrace Observability & Invariant Arbitration Engine
"""

import pytest
from backend.app.models import (
    NetworkClaim, NetworkPacket, SensorConfig, Verdict,
    ObservabilityStatus, ClaimType
)
from backend.app.engine.matching import match_flow_packets, is_packet_in_temporal_window
from backend.app.engine.observability import assess_sensor_observability, ip_in_network
from backend.app.engine.arbitration import arbitrate_claim


def test_ip_in_network():
    assert ip_in_network("192.168.1.50", "192.168.1.0/24") is True
    assert ip_in_network("10.0.0.5", "192.168.1.0/24") is False
    assert ip_in_network("198.51.100.4", "198.51.100.0/24") is True


def test_sensor_observability_coverage():
    sensor = SensorConfig(
        id="s1",
        investigation_id="inv1",
        sensor_name="gw-sensor",
        monitored_cidrs=["192.168.1.0/24"],
        capture_start="2026-01-01T00:00:00+00:00",
        capture_end="2026-01-02T00:00:00+00:00",
        packet_loss_detected=False,
        status="ACTIVE"
    )

    # In-scope claim
    claim_in = NetworkClaim(
        id="c1",
        investigation_id="inv1",
        source_event_id="e1",
        claim_type=ClaimType.TCP_HANDSHAKE,
        src_ip="192.168.1.10",
        dst_ip="192.168.1.50",
        dst_port=80,
        timestamp=1767225600.0,  # 2026-01-01T00:00:00Z
        timestamp_iso="2026-01-01T12:00:00+00:00",
        description="test"
    )
    status, sid, reason = assess_sensor_observability(claim_in, [sensor])
    assert status == ObservabilityStatus.FULLY_OBSERVABLE
    assert sid == "s1"

    # Out-of-scope subnet (Unobservable)
    claim_out = NetworkClaim(
        id="c2",
        investigation_id="inv1",
        source_event_id="e2",
        claim_type=ClaimType.TCP_HANDSHAKE,
        src_ip="10.5.0.1",
        dst_ip="172.16.0.1",
        dst_port=443,
        timestamp=1767225600.0,
        timestamp_iso="2026-01-01T12:00:00+00:00",
        description="test"
    )
    status, sid, reason = assess_sensor_observability(claim_out, [sensor])
    assert status == ObservabilityStatus.UNOBSERVABLE
    assert sid is None

    # Degraded sensor (packet loss)
    sensor_degraded = SensorConfig(
        id="s2",
        investigation_id="inv1",
        sensor_name="degraded-sensor",
        monitored_cidrs=["192.168.1.0/24"],
        packet_loss_detected=True,
        status="ACTIVE"
    )
    status, sid, reason = assess_sensor_observability(claim_in, [sensor_degraded])
    assert status == ObservabilityStatus.DEGRADED_VISIBILITY


def test_arbitration_case_1_supported():
    """Case 1: Full Handshake and Payload Observed -> SUPPORTED"""
    claim = NetworkClaim(
        id="c1",
        investigation_id="inv1",
        source_event_id="e1",
        claim_type=ClaimType.TCP_HANDSHAKE,
        src_ip="192.168.1.10",
        dst_ip="198.51.100.4",
        dst_port=443,
        timestamp=100.0,
        timestamp_iso="2026-01-01T00:01:40+00:00",
        tolerance_seconds=2.0,
        description="TCP Handshake"
    )
    sensor = SensorConfig(
        id="s1",
        investigation_id="inv1",
        sensor_name="gw",
        monitored_cidrs=["192.168.1.0/24", "198.51.100.0/24"],
        status="ACTIVE"
    )
    packets = [
        NetworkPacket(id="p1", investigation_id="inv1", evidence_id="ev1", timestamp=100.1, timestamp_iso="", src_ip="192.168.1.10", src_port=50000, dst_ip="198.51.100.4", dst_port=443, tcp_flags=["SYN"]),
        NetworkPacket(id="p2", investigation_id="inv1", evidence_id="ev1", timestamp=100.2, timestamp_iso="", src_ip="198.51.100.4", src_port=443, dst_ip="192.168.1.10", dst_port=50000, tcp_flags=["SYN", "ACK"]),
        NetworkPacket(id="p3", investigation_id="inv1", evidence_id="ev1", timestamp=100.3, timestamp_iso="", src_ip="192.168.1.10", src_port=50000, dst_ip="198.51.100.4", dst_port=443, tcp_flags=["ACK"])
    ]

    result = arbitrate_claim(claim, packets, [sensor])
    assert result.verdict == Verdict.SUPPORTED
    assert "INV-TCP-01" in result.applied_rule
    assert len(result.matching_packet_ids) == 3


def test_arbitration_case_2_contradicted_rst():
    """Case 2: Handshake Refused via RST -> CONTRADICTED"""
    claim = NetworkClaim(
        id="c2",
        investigation_id="inv1",
        source_event_id="e2",
        claim_type=ClaimType.TCP_HANDSHAKE,
        src_ip="192.168.1.10",
        dst_ip="192.168.1.150",
        dst_port=445,
        timestamp=200.0,
        timestamp_iso="2026-01-01T00:03:20+00:00",
        tolerance_seconds=2.0,
        description="TCP Handshake Refusal"
    )
    sensor = SensorConfig(
        id="s1",
        investigation_id="inv1",
        sensor_name="gw",
        monitored_cidrs=["192.168.1.0/24"],
        status="ACTIVE"
    )
    packets = [
        NetworkPacket(id="p1", investigation_id="inv1", evidence_id="ev1", timestamp=200.1, timestamp_iso="", src_ip="192.168.1.10", src_port=51000, dst_ip="192.168.1.150", dst_port=445, tcp_flags=["SYN"]),
        NetworkPacket(id="p2", investigation_id="inv1", evidence_id="ev1", timestamp=200.2, timestamp_iso="", src_ip="192.168.1.150", src_port=445, dst_ip="192.168.1.10", dst_port=51000, tcp_flags=["RST", "ACK"])
    ]

    result = arbitrate_claim(claim, packets, [sensor])
    assert result.verdict == Verdict.CONTRADICTED
    assert "INV-TCP-02" in result.applied_rule
    assert len(result.conflicting_packet_ids) > 0


def test_arbitration_case_3_unresolved_observability_gap():
    """Case 3: Missing evidence outside sensor visibility -> UNRESOLVED (Crucial Invariant)"""
    claim = NetworkClaim(
        id="c3",
        investigation_id="inv1",
        source_event_id="e3",
        claim_type=ClaimType.TCP_HANDSHAKE,
        src_ip="10.0.0.5",
        dst_ip="172.16.50.2",
        dst_port=8443,
        timestamp=300.0,
        timestamp_iso="2026-01-01T00:05:00+00:00",
        description="Edge blindspot"
    )
    sensor = SensorConfig(
        id="s1",
        investigation_id="inv1",
        sensor_name="gw",
        monitored_cidrs=["192.168.1.0/24"],  # Does NOT monitor 172.16.50.0/24
        status="ACTIVE"
    )
    # Zero packets exist for this flow
    result = arbitrate_claim(claim, [], [sensor])
    assert result.verdict == Verdict.UNRESOLVED
    assert result.observability_status == ObservabilityStatus.UNOBSERVABLE
    assert "INV-OBS-02" in result.applied_rule


def test_arbitration_case_4_data_transfer_reset():
    """Case 4: Host claims write(), but network reset before data flow -> CONTRADICTED"""
    claim = NetworkClaim(
        id="c4",
        investigation_id="inv1",
        source_event_id="e4",
        claim_type=ClaimType.DATA_TRANSFER,
        src_ip="192.168.1.10",
        dst_ip="203.0.113.88",
        dst_port=9001,
        timestamp=400.0,
        timestamp_iso="2026-01-01T00:06:40+00:00",
        claimed_bytes=8192,
        description="Exfiltration write"
    )
    sensor = SensorConfig(
        id="s1",
        investigation_id="inv1",
        sensor_name="gw",
        monitored_cidrs=["192.168.1.0/24", "203.0.113.0/24"],
        status="ACTIVE"
    )
    packets = [
        NetworkPacket(id="p1", investigation_id="inv1", evidence_id="ev1", timestamp=400.1, timestamp_iso="", src_ip="192.168.1.10", src_port=52000, dst_ip="203.0.113.88", dst_port=9001, tcp_flags=["SYN"]),
        NetworkPacket(id="p2", investigation_id="inv1", evidence_id="ev1", timestamp=400.2, timestamp_iso="", src_ip="203.0.113.88", src_port=9001, dst_ip="192.168.1.10", dst_port=52000, tcp_flags=["SYN", "ACK"]),
        NetworkPacket(id="p3", investigation_id="inv1", evidence_id="ev1", timestamp=400.3, timestamp_iso="", src_ip="192.168.1.10", src_port=52000, dst_ip="203.0.113.88", dst_port=9001, tcp_flags=["ACK"]),
        # RST with 0 payload
        NetworkPacket(id="p4", investigation_id="inv1", evidence_id="ev1", timestamp=400.4, timestamp_iso="", src_ip="203.0.113.88", src_port=9001, dst_ip="192.168.1.10", dst_port=52000, tcp_flags=["RST"], payload_len=0)
    ]

    result = arbitrate_claim(claim, packets, [sensor])
    assert result.verdict == Verdict.CONTRADICTED
    assert "INV-DATA-02" in result.applied_rule
