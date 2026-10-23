"""
TrueTrace Scenarios Runner API
Loads reproducible benchmark datasets and executes live local experiments end-to-end.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import os
import json
import uuid
import datetime
from pathlib import Path

from ..database import get_db_connection
from ..scenarios.fixtures import create_scenario_fixtures
from ..scenarios.controlled_experiments import run_live_tcp_test
from ..parsers.pcap_parser import parse_pcap_file
from ..parsers.host_log_parser import parse_host_log_file
from ..engine.graph_builder import AttackGraphBuilder
from ..engine.arbitration import arbitrate_claim
from ..models import (
    SensorConfig, NetworkClaim, NetworkPacket, ClaimType,
    EvidenceType, AttackGraph, Verdict
)

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])

BASE_EVIDENCE_DIR = os.environ.get(
    "TRUETRACE_EVIDENCE_DIR",
    str(Path(__file__).parent.parent.parent.parent / "evidence")
)


@router.get("")
def list_available_scenarios():
    return [
        {
            "id": "scenario_1_supported",
            "title": "Case 1: Fully Supported Exfiltration",
            "type": "BENCHMARK_FIXTURE",
            "expected_verdict": "SUPPORTED",
            "description": "APT34 staged exfiltration: bash spawns exfil_agent, reads /etc/shadow, connects to 198.51.100.4:443. Full TCP handshake & acknowledged payload confirmed on wire."
        },
        {
            "id": "scenario_2_contradicted",
            "title": "Case 2: Contradicted Lateral Movement (RST / Refusal)",
            "type": "BENCHMARK_FIXTURE",
            "expected_verdict": "CONTRADICTED",
            "description": "Host log claims powershell.exe established connection to 192.168.1.150:445, but independent PCAP captures TCP RST/ACK refusal from closed port."
        },
        {
            "id": "scenario_3_unresolved",
            "title": "Case 3: Unresolved (Sensor Visibility Gap)",
            "type": "BENCHMARK_FIXTURE",
            "expected_verdict": "UNRESOLVED",
            "description": "Mandiant M-Trends edge device blindspot: host connects to 172.16.50.2:8443. Sensor only monitored 192.168.1.0/24. Engine enforces: absence of evidence != evidence of absence."
        },
        {
            "id": "scenario_4_write_buffered_reset",
            "title": "Case 4: Contradicted Data Transfer (write() Buffered, Wire Reset)",
            "type": "BENCHMARK_FIXTURE",
            "expected_verdict": "CONTRADICTED",
            "description": "Demonstrates core research thesis: host write() return value != network transport delivery. Socket torn down by RST before payload reached wire."
        },
        {
            "id": "live_tcp_supported",
            "title": "Live Controlled TCP Experiment (Supported)",
            "type": "LIVE_SOCKET_EXECUTION",
            "expected_verdict": "SUPPORTED",
            "description": "Executes real Python socket server/client on localhost, sends real bytes, captures transport telemetry, and verifies via arbitration."
        },
        {
            "id": "live_tcp_contradicted",
            "title": "Live Controlled TCP Experiment (Contradicted / Refusal)",
            "type": "LIVE_SOCKET_EXECUTION",
            "expected_verdict": "CONTRADICTED",
            "description": "Attempts real socket connection to closed localhost port, captures OS refusal (WinError 10061) and wire RST, deriving falsification."
        }
    ]


@router.post("/run")
def execute_scenario(payload: Dict[str, str]):
    scenario_id = payload.get("scenario_id")
    if not scenario_id:
        raise HTTPException(status_code=400, detail="Missing scenario_id")

    conn = get_db_connection()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    inv_id = f"inv-{scenario_id[:12]}-{uuid.uuid4().hex[:4]}"

    # Setup files and metadata
    if scenario_id.startswith("live_tcp_"):
        mode = scenario_id.replace("live_tcp_", "")
        exp_meta = run_live_tcp_test(BASE_EVIDENCE_DIR, mode=mode)
        inv_name = f"Live Experiment: {mode.title()}"
        inv_desc = f"Real socket experiment executed on local host in mode '{mode}'."
        host_file = exp_meta["host_file"]
        pcap_file = exp_meta["pcap_file"]
        host_sha = exp_meta["host_sha256"]
        pcap_sha = exp_meta["pcap_sha256"]
        sensor_dict = exp_meta["sensor_config"]
    else:
        fixtures_meta = create_scenario_fixtures(BASE_EVIDENCE_DIR)
        if scenario_id not in fixtures_meta:
            raise HTTPException(status_code=404, detail="Scenario not found")
        scen_info = fixtures_meta[scenario_id]
        inv_name = scen_info["title"]
        inv_desc = scen_info["description"]
        host_file = scen_info["host_file"]
        pcap_file = scen_info["pcap_file"]
        host_sha = scen_info["host_sha256"]
        pcap_sha = scen_info["pcap_sha256"]
        sensor_dict = scen_info["sensor"]

    # 1. Insert Investigation
    with conn:
        conn.execute(
            "INSERT INTO investigations (id, name, description, created_at, status, stats) VALUES (?, ?, ?, ?, ?, ?)",
            (inv_id, inv_name, inv_desc, now_iso, "ACTIVE", json.dumps({}))
        )

    # 2. Insert Sensor
    sensor_id = f"sensor-{uuid.uuid4().hex[:6]}"
    with conn:
        conn.execute(
            """INSERT INTO sensors (id, investigation_id, sensor_name, interface, monitored_cidrs, capture_start, capture_end, packet_loss_detected, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                sensor_id,
                inv_id,
                sensor_dict["sensor_name"],
                "eth0",
                json.dumps(sensor_dict["monitored_cidrs"]),
                None,
                None,
                1 if sensor_dict.get("packet_loss_detected", False) else 0,
                sensor_dict.get("status", "ACTIVE"),
                f"Configured for {inv_name}"
            )
        )

    # 3. Ingest Host Evidence
    ev_host_id = f"ev-host-{uuid.uuid4().hex[:6]}"
    with conn:
        conn.execute(
            """INSERT INTO evidence_files 
               (id, investigation_id, file_name, file_path, evidence_type, file_size_bytes, sha256_hash, recorded_at, ingested_at, description, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ev_host_id, inv_id, Path(host_file).name, host_file, EvidenceType.HOST_AUDIT_LOG.value, os.path.getsize(host_file), host_sha, now_iso, now_iso, "Scenario Host Audit Log", json.dumps({}))
        )
    events, claims = parse_host_log_file(host_file, inv_id, ev_host_id)
    with conn:
        for e in events:
            conn.execute(
                """INSERT INTO host_events
                   (id, investigation_id, evidence_id, timestamp, timestamp_iso, event_type, process_id, process_name, parent_process_id, file_path, src_ip, src_port, dst_ip, dst_port, protocol, bytes_count, return_code, raw_record)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (e.id, e.investigation_id, e.evidence_id, e.timestamp, e.timestamp_iso, e.event_type.value, e.process_id, e.process_name, e.parent_process_id, e.file_path, e.src_ip, e.src_port, e.dst_ip, e.dst_port, e.protocol, e.bytes_count, e.return_code, json.dumps(e.raw_record))
            )
        for c in claims:
            conn.execute(
                """INSERT INTO network_claims
                   (id, investigation_id, source_event_id, claim_type, src_ip, src_port, dst_ip, dst_port, protocol, timestamp, timestamp_iso, tolerance_seconds, claimed_bytes, candidate_edge_id, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (c.id, c.investigation_id, c.source_event_id, c.claim_type.value, c.src_ip, c.src_port, c.dst_ip, c.dst_port, c.protocol, c.timestamp, c.timestamp_iso, c.tolerance_seconds, c.claimed_bytes, c.candidate_edge_id, c.description)
            )

    # 4. Ingest PCAP Evidence
    ev_pcap_id = f"ev-pcap-{uuid.uuid4().hex[:6]}"
    with conn:
        conn.execute(
            """INSERT INTO evidence_files 
               (id, investigation_id, file_name, file_path, evidence_type, file_size_bytes, sha256_hash, recorded_at, ingested_at, description, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ev_pcap_id, inv_id, Path(pcap_file).name, pcap_file, EvidenceType.PCAP_CAPTURE.value, os.path.getsize(pcap_file), pcap_sha, now_iso, now_iso, "Scenario Network Packet Capture", json.dumps({}))
        )
    pkts = parse_pcap_file(pcap_file, inv_id, ev_pcap_id, sensor_id=sensor_dict["sensor_name"])
    with conn:
        for p in pkts:
            conn.execute(
                """INSERT INTO network_packets
                   (id, investigation_id, evidence_id, timestamp, timestamp_iso, src_ip, src_port, dst_ip, dst_port, protocol, tcp_flags, seq_num, ack_num, payload_len, sensor_id, summary)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p.id, p.investigation_id, p.evidence_id, p.timestamp, p.timestamp_iso, p.src_ip, p.src_port, p.dst_ip, p.dst_port, p.protocol, json.dumps(p.tcp_flags), p.seq_num, p.ack_num, p.payload_len, p.sensor_id, p.summary)
            )

    # 5. Build Candidate Attack Graph
    builder = AttackGraphBuilder(inv_id)
    cand_graph = builder.build_candidate_graph(events, claims)
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO attack_graphs (investigation_id, graph_type, graph_data, created_at)
               VALUES (?, ?, ?, ?)""",
            (inv_id, "CANDIDATE", cand_graph.model_dump_json(), now_iso)
        )

    # 6. Execute Arbitration Engine
    sensors_list = [
        SensorConfig(
            id=sensor_id,
            investigation_id=inv_id,
            sensor_name=sensor_dict["sensor_name"],
            interface="eth0",
            monitored_cidrs=sensor_dict["monitored_cidrs"],
            packet_loss_detected=sensor_dict.get("packet_loss_detected", False),
            status=sensor_dict.get("status", "ACTIVE")
        )
    ]
    arbitration_results = []
    with conn:
        for claim in claims:
            res = arbitrate_claim(claim, pkts, sensors_list)
            arbitration_results.append(res)
            conn.execute(
                """INSERT INTO arbitration_results
                   (id, claim_id, investigation_id, verdict, applied_rule, reasoning, observability_status, observability_reasoning, matching_packet_ids, conflicting_packet_ids, matching_evidence_summaries, timestamp_delta, sensor_id, epistemic_notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    res.id,
                    res.claim_id,
                    res.investigation_id,
                    res.verdict.value,
                    res.applied_rule,
                    res.reasoning,
                    res.observability_status.value,
                    res.observability_reasoning,
                    json.dumps(res.matching_packet_ids),
                    json.dumps(res.conflicting_packet_ids),
                    json.dumps(res.matching_evidence_summaries),
                    res.timestamp_delta,
                    res.sensor_id,
                    res.epistemic_notes
                )
            )

    # 7. Build Refined Attack Graph
    refined_graph = builder.build_refined_graph(cand_graph, arbitration_results)
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO attack_graphs (investigation_id, graph_type, graph_data, created_at)
               VALUES (?, ?, ?, ?)""",
            (inv_id, "REFINED", refined_graph.model_dump_json(), now_iso)
        )

    summary = {
        "supported": sum(1 for r in arbitration_results if r.verdict == Verdict.SUPPORTED),
        "contradicted": sum(1 for r in arbitration_results if r.verdict == Verdict.CONTRADICTED),
        "unresolved": sum(1 for r in arbitration_results if r.verdict == Verdict.UNRESOLVED)
    }

    conn.close()

    return {
        "status": "success",
        "investigation_id": inv_id,
        "investigation_name": inv_name,
        "summary": summary,
        "results": [r.model_dump() for r in arbitration_results],
        "candidate_graph_nodes": len(cand_graph.nodes),
        "candidate_graph_edges": len(cand_graph.edges),
        "refined_graph_edges": len(refined_graph.edges)
    }
