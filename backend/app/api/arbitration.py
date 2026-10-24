"""
TrueTrace Claim Arbitration API
Executes observability-aware arbitration on candidate claims and produces inspectable verdicts.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import json
import datetime

from ..models import (
    NetworkClaim, NetworkPacket, SensorConfig, ArbitrationResult,
    Verdict, ObservabilityStatus, ClaimType, AttackGraph
)
from ..database import get_db_connection
from ..engine.arbitration import arbitrate_claim
from ..engine.graph_builder import AttackGraphBuilder

router = APIRouter(prefix="/api/arbitration", tags=["Arbitration"])


@router.get("/claims/{inv_id}", response_model=List[NetworkClaim])
def list_claims(inv_id: str):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM network_claims WHERE investigation_id = ? ORDER BY timestamp ASC", (inv_id,)).fetchall()
    results = []
    for r in rows:
        results.append(NetworkClaim(
            id=r["id"],
            investigation_id=r["investigation_id"],
            source_event_id=r["source_event_id"],
            claim_type=ClaimType(r["claim_type"]),
            src_ip=r["src_ip"],
            src_port=r["src_port"],
            dst_ip=r["dst_ip"],
            dst_port=r["dst_port"],
            protocol=r["protocol"],
            timestamp=r["timestamp"],
            timestamp_iso=r["timestamp_iso"],
            tolerance_seconds=r["tolerance_seconds"],
            claimed_bytes=r["claimed_bytes"],
            candidate_edge_id=r["candidate_edge_id"],
            description=r["description"]
        ))
    conn.close()
    return results


@router.get("/results/{inv_id}", response_model=List[ArbitrationResult])
def list_results(inv_id: str):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM arbitration_results WHERE investigation_id = ?", (inv_id,)).fetchall()
    results = []
    for r in rows:
        results.append(ArbitrationResult(
            id=r["id"],
            claim_id=r["claim_id"],
            investigation_id=r["investigation_id"],
            verdict=Verdict(r["verdict"]),
            applied_rule=r["applied_rule"],
            reasoning=r["reasoning"],
            observability_status=ObservabilityStatus(r["observability_status"]),
            observability_reasoning=r["observability_reasoning"],
            matching_packet_ids=json.loads(r["matching_packet_ids"]) if r["matching_packet_ids"] else [],
            conflicting_packet_ids=json.loads(r["conflicting_packet_ids"]) if r["conflicting_packet_ids"] else [],
            matching_evidence_summaries=json.loads(r["matching_evidence_summaries"]) if r["matching_evidence_summaries"] else [],
            timestamp_delta=r["timestamp_delta"],
            sensor_id=r["sensor_id"],
            epistemic_notes=r["epistemic_notes"] or ""
        ))
    conn.close()
    return results


def execute_arbitration_logic(inv_id: str) -> Dict[str, Any]:
    conn = get_db_connection()

    # 1. Fetch claims
    claim_rows = conn.execute("SELECT * FROM network_claims WHERE investigation_id = ?", (inv_id,)).fetchall()
    if not claim_rows:
        conn.close()
        return {"status": "no_claims", "message": "No network claims found for this investigation."}

    claims: List[NetworkClaim] = []
    for r in claim_rows:
        claims.append(NetworkClaim(
            id=r["id"],
            investigation_id=r["investigation_id"],
            source_event_id=r["source_event_id"],
            claim_type=ClaimType(r["claim_type"]),
            src_ip=r["src_ip"],
            src_port=r["src_port"],
            dst_ip=r["dst_ip"],
            dst_port=r["dst_port"],
            protocol=r["protocol"],
            timestamp=r["timestamp"],
            timestamp_iso=r["timestamp_iso"],
            tolerance_seconds=r["tolerance_seconds"],
            claimed_bytes=r["claimed_bytes"],
            candidate_edge_id=r["candidate_edge_id"],
            description=r["description"]
        ))

    # 2. Fetch packets
    pkt_rows = conn.execute("SELECT * FROM network_packets WHERE investigation_id = ?", (inv_id,)).fetchall()
    packets: List[NetworkPacket] = []
    for r in pkt_rows:
        packets.append(NetworkPacket(
            id=r["id"],
            investigation_id=r["investigation_id"],
            evidence_id=r["evidence_id"],
            timestamp=r["timestamp"],
            timestamp_iso=r["timestamp_iso"],
            src_ip=r["src_ip"],
            src_port=r["src_port"],
            dst_ip=r["dst_ip"],
            dst_port=r["dst_port"],
            protocol=r["protocol"],
            tcp_flags=json.loads(r["tcp_flags"]) if r["tcp_flags"] else [],
            seq_num=r["seq_num"],
            ack_num=r["ack_num"],
            payload_len=r["payload_len"],
            sensor_id=r["sensor_id"],
            summary=r["summary"] or ""
        ))

    # 3. Fetch sensors
    sensor_rows = conn.execute("SELECT * FROM sensors WHERE investigation_id = ?", (inv_id,)).fetchall()
    sensors: List[SensorConfig] = []
    for r in sensor_rows:
        sensors.append(SensorConfig(
            id=r["id"],
            investigation_id=r["investigation_id"],
            sensor_name=r["sensor_name"],
            interface=r["interface"],
            monitored_cidrs=json.loads(r["monitored_cidrs"]) if r["monitored_cidrs"] else [],
            capture_start=r["capture_start"],
            capture_end=r["capture_end"],
            packet_loss_detected=bool(r["packet_loss_detected"]),
            status=r["status"],
            notes=r["notes"] or ""
        ))

    # 4. Arbitrate each claim
    arbitration_results: List[ArbitrationResult] = []
    with conn:
        conn.execute("DELETE FROM arbitration_results WHERE investigation_id = ?", (inv_id,))
        for claim in claims:
            res = arbitrate_claim(claim, packets, sensors)
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

    # 5. Build Refined Graph
    cand_row = conn.execute("SELECT graph_data FROM attack_graphs WHERE investigation_id = ? AND graph_type = 'CANDIDATE'", (inv_id,)).fetchone()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if cand_row:
        cand_dict = json.loads(cand_row[0])
        cand_graph = AttackGraph(**cand_dict)
        builder = AttackGraphBuilder(inv_id)
        refined_graph = builder.build_refined_graph(cand_graph, arbitration_results)
        with conn:
            conn.execute(
                """INSERT OR REPLACE INTO attack_graphs (investigation_id, graph_type, graph_data, created_at)
                   VALUES (?, ?, ?, ?)""",
                (inv_id, "REFINED", refined_graph.model_dump_json(), now_iso)
            )

    # Calculate summary counts
    summary = {
        "total_claims": len(arbitration_results),
        "supported": sum(1 for r in arbitration_results if r.verdict == Verdict.SUPPORTED),
        "contradicted": sum(1 for r in arbitration_results if r.verdict == Verdict.CONTRADICTED),
        "unresolved": sum(1 for r in arbitration_results if r.verdict == Verdict.UNRESOLVED)
    }

    conn.close()
    return {
        "status": "success",
        "investigation_id": inv_id,
        "summary": summary,
        "results": [r.model_dump() for r in arbitration_results]
    }


@router.post("/run/{inv_id}")
def run_arbitration(inv_id: str):
    return execute_arbitration_logic(inv_id)
