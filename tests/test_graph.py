"""
Unit Tests for Candidate and Refined Attack Graph Construction
"""

import pytest
from backend.app.models import (
    HostEvent, HostEventType, NetworkClaim, ArbitrationResult,
    Verdict, ObservabilityStatus, ClaimType
)
from backend.app.engine.graph_builder import AttackGraphBuilder


def test_candidate_graph_construction():
    events = [
        HostEvent(id="e1", investigation_id="inv1", evidence_id="ev1", timestamp=10.0, timestamp_iso="2026-01-01T00:00:10Z", event_type=HostEventType.PROCESS_SPAWN, process_id=101, process_name="powershell.exe", parent_process_id=100),
        HostEvent(id="e2", investigation_id="inv1", evidence_id="ev1", timestamp=11.0, timestamp_iso="2026-01-01T00:00:11Z", event_type=HostEventType.FILE_READ, process_id=101, file_path="C:\\passwords.txt"),
        HostEvent(id="e3", investigation_id="inv1", evidence_id="ev1", timestamp=12.0, timestamp_iso="2026-01-01T00:00:12Z", event_type=HostEventType.SOCKET_CONNECT, process_id=101, dst_ip="198.51.100.5", dst_port=443)
    ]
    claims = [
        NetworkClaim(id="c1", investigation_id="inv1", source_event_id="e3", claim_type=ClaimType.TCP_HANDSHAKE, src_ip="192.168.1.10", dst_ip="198.51.100.5", dst_port=443, timestamp=12.0, timestamp_iso="2026-01-01T00:00:12Z", description="Connection")
    ]

    builder = AttackGraphBuilder("inv1")
    cand = builder.build_candidate_graph(events, claims)

    assert len(cand.nodes) >= 3  # Parent process, Child process, File, Endpoint
    assert len(cand.edges) == 3   # SPAWNED, READ, CONNECTS_TO
    net_edges = [e for e in cand.edges if e.is_network_dependent]
    assert len(net_edges) == 1
    assert net_edges[0].verdict is None  # Unarbitrated in candidate phase


def test_refined_graph_preserves_unresolved_and_marks_contradicted():
    events = [
        HostEvent(id="e1", investigation_id="inv1", evidence_id="ev1", timestamp=10.0, timestamp_iso="2026-01-01T00:00:10Z", event_type=HostEventType.SOCKET_CONNECT, process_id=101, dst_ip="198.51.100.5", dst_port=443),
        HostEvent(id="e2", investigation_id="inv1", evidence_id="ev1", timestamp=20.0, timestamp_iso="2026-01-01T00:00:20Z", event_type=HostEventType.SOCKET_CONNECT, process_id=101, dst_ip="172.16.0.1", dst_port=80)
    ]
    claims = [
        NetworkClaim(id="c1", investigation_id="inv1", source_event_id="e1", claim_type=ClaimType.TCP_HANDSHAKE, src_ip="192.168.1.10", dst_ip="198.51.100.5", dst_port=443, timestamp=10.0, timestamp_iso="", description="C1"),
        NetworkClaim(id="c2", investigation_id="inv1", source_event_id="e2", claim_type=ClaimType.TCP_HANDSHAKE, src_ip="192.168.1.10", dst_ip="172.16.0.1", dst_port=80, timestamp=20.0, timestamp_iso="", description="C2")
    ]

    builder = AttackGraphBuilder("inv1")
    cand = builder.build_candidate_graph(events, claims)

    arbitration_results = [
        ArbitrationResult(
            id="a1",
            claim_id="c1",
            investigation_id="inv1",
            verdict=Verdict.CONTRADICTED,
            applied_rule="INV-TCP-02",
            reasoning="RST Refusal received",
            observability_status=ObservabilityStatus.FULLY_OBSERVABLE,
            observability_reasoning="Full visibility"
        ),
        ArbitrationResult(
            id="a2",
            claim_id="c2",
            investigation_id="inv1",
            verdict=Verdict.UNRESOLVED,
            applied_rule="INV-OBS-02",
            reasoning="Blindspot",
            observability_status=ObservabilityStatus.UNOBSERVABLE,
            observability_reasoning="Outside monitored CIDR"
        )
    ]

    refined = builder.build_refined_graph(cand, arbitration_results)

    # Both edges must be present in refined graph! No silent deletion!
    assert len(refined.edges) == 2
    edge_map = {e.claim_id: e for e in refined.edges}

    assert edge_map["c1"].verdict == Verdict.CONTRADICTED
    assert "INV-TCP-02" in edge_map["c1"].applied_rule

    assert edge_map["c2"].verdict == Verdict.UNRESOLVED
    assert "INV-OBS-02" in edge_map["c2"].applied_rule
    assert edge_map["c2"].properties.get("observability_status") == "UNOBSERVABLE"
