"""
TrueTrace Evidence Ingestion & Explorer API
Uploads, parses, and provides forensic access to original evidence, cryptographic hashes, and parsed events.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Any, Optional
import os
import uuid
import datetime
import json
import shutil
from pathlib import Path

from ..models import EvidenceFile, EvidenceType, HostEvent, NetworkPacket
from ..database import get_db_connection
from ..parsers.pcap_parser import parse_pcap_file, compute_file_sha256
from ..parsers.host_log_parser import parse_host_log_file
from ..engine.graph_builder import AttackGraphBuilder

router = APIRouter(prefix="/api/evidence", tags=["Evidence"])

EVIDENCE_DIR = os.environ.get(
    "TRUETRACE_EVIDENCE_DIR",
    str(Path(__file__).parent.parent.parent.parent / "evidence")
)
os.makedirs(EVIDENCE_DIR, exist_ok=True)


@router.get("/{inv_id}", response_model=List[EvidenceFile])
def list_evidence_files(inv_id: str):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM evidence_files WHERE investigation_id = ? ORDER BY ingested_at DESC", (inv_id,)).fetchall()
    results = []
    for r in rows:
        results.append(EvidenceFile(
            id=r["id"],
            investigation_id=r["investigation_id"],
            file_name=r["file_name"],
            file_path=r["file_path"],
            evidence_type=EvidenceType(r["evidence_type"]),
            file_size_bytes=r["file_size_bytes"],
            sha256_hash=r["sha256_hash"],
            recorded_at=r["recorded_at"],
            ingested_at=r["ingested_at"],
            description=r["description"] or "",
            metadata=json.loads(r["metadata"]) if r["metadata"] else {}
        ))
    conn.close()
    return results


@router.post("/upload")
async def upload_evidence(
    investigation_id: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...)
):
    safe_filename = Path(file.filename).name
    evidence_id = f"ev-{uuid.uuid4().hex[:8]}"
    save_path = os.path.join(EVIDENCE_DIR, f"{evidence_id}_{safe_filename}")

    # Write file to disk
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    sha256 = compute_file_sha256(save_path)
    file_size = os.path.getsize(save_path)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Determine type
    lower_name = safe_filename.lower()
    is_pcap = lower_name.endswith(".pcap") or lower_name.endswith(".pcapng") or lower_name.endswith(".cap")
    ev_type = EvidenceType.PCAP_CAPTURE if is_pcap else EvidenceType.HOST_AUDIT_LOG

    conn = get_db_connection()
    with conn:
        conn.execute(
            """INSERT INTO evidence_files 
               (id, investigation_id, file_name, file_path, evidence_type, file_size_bytes, sha256_hash, recorded_at, ingested_at, description, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (evidence_id, investigation_id, safe_filename, save_path, ev_type.value, file_size, sha256, now_iso, now_iso, description, json.dumps({}))
        )

    # Parse evidence
    parsed_events_count = 0
    parsed_packets_count = 0
    parsed_claims_count = 0

    if ev_type == EvidenceType.PCAP_CAPTURE:
        pkts = parse_pcap_file(save_path, investigation_id, evidence_id)
        with conn:
            for p in pkts:
                conn.execute(
                    """INSERT OR REPLACE INTO network_packets
                       (id, investigation_id, evidence_id, timestamp, timestamp_iso, src_ip, src_port, dst_ip, dst_port, protocol, tcp_flags, seq_num, ack_num, payload_len, sensor_id, summary)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (p.id, p.investigation_id, p.evidence_id, p.timestamp, p.timestamp_iso, p.src_ip, p.src_port, p.dst_ip, p.dst_port, p.protocol, json.dumps(p.tcp_flags), p.seq_num, p.ack_num, p.payload_len, p.sensor_id, p.summary)
                )
        parsed_packets_count = len(pkts)

    elif ev_type == EvidenceType.HOST_AUDIT_LOG:
        events, claims = parse_host_log_file(save_path, investigation_id, evidence_id)
        with conn:
            for e in events:
                conn.execute(
                    """INSERT OR REPLACE INTO host_events
                       (id, investigation_id, evidence_id, timestamp, timestamp_iso, event_type, process_id, process_name, parent_process_id, file_path, src_ip, src_port, dst_ip, dst_port, protocol, bytes_count, return_code, raw_record)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (e.id, e.investigation_id, e.evidence_id, e.timestamp, e.timestamp_iso, e.event_type.value, e.process_id, e.process_name, e.parent_process_id, e.file_path, e.src_ip, e.src_port, e.dst_ip, e.dst_port, e.protocol, e.bytes_count, e.return_code, json.dumps(e.raw_record))
                )
            for c in claims:
                conn.execute(
                    """INSERT OR REPLACE INTO network_claims
                       (id, investigation_id, source_event_id, claim_type, src_ip, src_port, dst_ip, dst_port, protocol, timestamp, timestamp_iso, tolerance_seconds, claimed_bytes, candidate_edge_id, description)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (c.id, c.investigation_id, c.source_event_id, c.claim_type.value, c.src_ip, c.src_port, c.dst_ip, c.dst_port, c.protocol, c.timestamp, c.timestamp_iso, c.tolerance_seconds, c.claimed_bytes, c.candidate_edge_id, c.description)
                )
        parsed_events_count = len(events)
        parsed_claims_count = len(claims)

        # Update candidate attack graph
        builder = AttackGraphBuilder(investigation_id)
        cand_graph = builder.build_candidate_graph(events, claims)
        with conn:
            conn.execute(
                """INSERT OR REPLACE INTO attack_graphs (investigation_id, graph_type, graph_data, created_at)
                   VALUES (?, ?, ?, ?)""",
                (investigation_id, "CANDIDATE", cand_graph.model_dump_json(), now_iso)
            )

    conn.close()

    return {
        "status": "success",
        "evidence_id": evidence_id,
        "file_name": safe_filename,
        "sha256": sha256,
        "file_size": file_size,
        "evidence_type": ev_type.value,
        "parsed_events": parsed_events_count,
        "parsed_claims": parsed_claims_count,
        "parsed_packets": parsed_packets_count
    }


@router.get("/host-events/{inv_id}")
def get_host_events(inv_id: str, limit: int = 100):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM host_events WHERE investigation_id = ? ORDER BY timestamp ASC LIMIT ?", (inv_id, limit)).fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


@router.get("/packets/{inv_id}")
def get_network_packets(inv_id: str, limit: int = 200):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM network_packets WHERE investigation_id = ? ORDER BY timestamp ASC LIMIT ?", (inv_id, limit)).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        d["tcp_flags"] = json.loads(d["tcp_flags"]) if d["tcp_flags"] else []
        results.append(d)
    conn.close()
    return results
