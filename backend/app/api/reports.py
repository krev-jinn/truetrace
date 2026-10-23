"""
TrueTrace Forensic Report Export API
Generates reproducible, inspectable forensic reports in JSON and Markdown formats.
Includes evidence provenance, cryptographic hashes, sensor coverage, applied rules, and verdict rationales.
"""

from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any
import json
import datetime

from ..database import get_db_connection

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def build_investigation_report_data(inv_id: str) -> Dict[str, Any]:
    conn = get_db_connection()
    inv_row = conn.execute("SELECT * FROM investigations WHERE id = ?", (inv_id,)).fetchone()
    if not inv_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Investigation not found")

    evidence_rows = conn.execute("SELECT * FROM evidence_files WHERE investigation_id = ?", (inv_id,)).fetchall()
    sensor_rows = conn.execute("SELECT * FROM sensors WHERE investigation_id = ?", (inv_id,)).fetchall()
    claim_rows = conn.execute("SELECT * FROM network_claims WHERE investigation_id = ?", (inv_id,)).fetchall()
    arb_rows = conn.execute("SELECT * FROM arbitration_results WHERE investigation_id = ?", (inv_id,)).fetchall()
    
    cand_graph_row = conn.execute("SELECT graph_data FROM attack_graphs WHERE investigation_id = ? AND graph_type = 'CANDIDATE'", (inv_id,)).fetchone()
    refined_graph_row = conn.execute("SELECT graph_data FROM attack_graphs WHERE investigation_id = ? AND graph_type = 'REFINED'", (inv_id,)).fetchone()

    conn.close()

    evidence_list = []
    for r in evidence_rows:
        evidence_list.append({
            "id": r["id"],
            "file_name": r["file_name"],
            "file_path": r["file_path"],
            "evidence_type": r["evidence_type"],
            "file_size_bytes": r["file_size_bytes"],
            "sha256_hash": r["sha256_hash"],
            "recorded_at": r["recorded_at"],
            "ingested_at": r["ingested_at"],
            "description": r["description"]
        })

    sensors_list = []
    for r in sensor_rows:
        sensors_list.append({
            "id": r["id"],
            "sensor_name": r["sensor_name"],
            "interface": r["interface"],
            "monitored_cidrs": json.loads(r["monitored_cidrs"]) if r["monitored_cidrs"] else [],
            "packet_loss_detected": bool(r["packet_loss_detected"]),
            "status": r["status"]
        })

    claims_list = []
    for r in claim_rows:
        claims_list.append({
            "id": r["id"],
            "source_event_id": r["source_event_id"],
            "claim_type": r["claim_type"],
            "flow": f"{r['src_ip']}:{r['src_port'] or '*'} -> {r['dst_ip']}:{r['dst_port']}",
            "protocol": r["protocol"],
            "timestamp": r["timestamp_iso"],
            "tolerance_seconds": r["tolerance_seconds"],
            "claimed_bytes": r["claimed_bytes"],
            "description": r["description"]
        })

    arb_list = []
    verdict_counts = {"SUPPORTED": 0, "CONTRADICTED": 0, "UNRESOLVED": 0}
    for r in arb_rows:
        verdict = r["verdict"]
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        arb_list.append({
            "id": r["id"],
            "claim_id": r["claim_id"],
            "verdict": verdict,
            "applied_rule": r["applied_rule"],
            "reasoning": r["reasoning"],
            "observability_status": r["observability_status"],
            "observability_reasoning": r["observability_reasoning"],
            "matching_packet_count": len(json.loads(r["matching_packet_ids"])) if r["matching_packet_ids"] else 0,
            "conflicting_packet_count": len(json.loads(r["conflicting_packet_ids"])) if r["conflicting_packet_ids"] else 0,
            "matching_evidence_summaries": json.loads(r["matching_evidence_summaries"]) if r["matching_evidence_summaries"] else [],
            "timestamp_delta": r["timestamp_delta"],
            "sensor_id": r["sensor_id"],
            "epistemic_notes": r["epistemic_notes"]
        })

    return {
        "report_generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "investigation": {
            "id": inv_row["id"],
            "name": inv_row["name"],
            "description": inv_row["description"],
            "created_at": inv_row["created_at"],
            "status": inv_row["status"]
        },
        "verdict_summary": verdict_counts,
        "evidence_files": evidence_list,
        "sensors": sensors_list,
        "claims": claims_list,
        "arbitration_results": arb_list,
        "candidate_graph": json.loads(cand_graph_row[0]) if cand_graph_row else None,
        "refined_graph": json.loads(refined_graph_row[0]) if refined_graph_row else None
    }


@router.get("/{inv_id}/json")
def get_report_json(inv_id: str):
    return build_investigation_report_data(inv_id)


@router.get("/{inv_id}/markdown")
def get_report_markdown(inv_id: str):
    data = build_investigation_report_data(inv_id)
    inv = data["investigation"]
    summary = data["verdict_summary"]

    lines = [
        f"# TrueTrace Forensic Investigation Report: {inv['name']}",
        f"**Investigation ID:** `{inv['id']}`  ",
        f"**Generated At:** {data['report_generated_at']}  ",
        f"**Status:** {inv['status']}  ",
        "",
        "## 1. Executive Summary & Verdict Distribution",
        f"- **Supported Hypotheses:** {summary.get('SUPPORTED', 0)}",
        f"- **Contradicted Hypotheses:** {summary.get('CONTRADICTED', 0)}",
        f"- **Unresolved (Visibility / Incomplete):** {summary.get('UNRESOLVED', 0)}",
        "",
        "## 2. Evidence Provenance & Cryptographic Digests",
        "| Evidence File | Type | Size (Bytes) | SHA-256 Digest |",
        "| :--- | :--- | :--- | :--- |"
    ]

    for ev in data["evidence_files"]:
        lines.append(f"| `{ev['file_name']}` | {ev['evidence_type']} | {ev['file_size_bytes']} | `{ev['sha256_hash']}` |")

    lines.extend([
        "",
        "## 3. Sensor Topology & Observability Baseline",
        "| Sensor ID | Name | Monitored CIDRs | Packet Loss Flag | Status |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ])

    for s in data["sensors"]:
        cidrs = ", ".join(s["monitored_cidrs"]) or "All"
        lines.append(f"| `{s['id']}` | {s['sensor_name']} | `{cidrs}` | {s['packet_loss_detected']} | {s['status']} |")

    lines.extend([
        "",
        "## 4. Network Claim Arbitration & Invariant Verdicts",
        "| Claim ID | Verdict | Applied Rule | Flow & Description | Reasoning |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ])

    claim_map = {c["id"]: c for c in data["claims"]}
    for arb in data["arbitration_results"]:
        c = claim_map.get(arb["claim_id"], {})
        flow_desc = f"{c.get('flow', '')} ({c.get('description', '')})"
        lines.append(f"| `{arb['claim_id']}` | **{arb['verdict']}** | `{arb['applied_rule']}` | {flow_desc} | {arb['reasoning']} |")

    lines.extend([
        "",
        "## 5. Epistemic Verification Integrity Note",
        "> **Methodological Guarantee:** Under the TrueTrace framework, absence of network telemetry is never interpreted as proof of non-occurrence unless complete sensor observability and lossless packet capture are mathematically and topologically verified. Contradicted claims indicate genuine packet-level falsification (e.g. TCP RST, closed port, or explicit filter drop).",
        "",
        "---",
        "*Report automatically generated by TrueTrace: A Network-Grounded Framework for Attack Trace Verification.*"
    ])

    content = "\n".join(lines)
    return Response(content=content, media_type="text/markdown")
