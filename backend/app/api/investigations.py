"""
TrueTrace Investigations API
Endpoints for creating, listing, inspecting, and deleting forensic investigations.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import uuid
import datetime
import json

from ..models import Investigation, InvestigationCreate
from ..database import get_db_connection

router = APIRouter(prefix="/api/investigations", tags=["Investigations"])


@router.get("", response_model=List[Investigation])
def list_investigations():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM investigations ORDER BY created_at DESC").fetchall()
    results = []
    for r in rows:
        results.append(Investigation(
            id=r["id"],
            name=r["name"],
            description=r["description"],
            created_at=r["created_at"],
            status=r["status"],
            stats=json.loads(r["stats"]) if r["stats"] else {}
        ))
    conn.close()
    return results


@router.post("", response_model=Investigation)
def create_investigation(payload: InvestigationCreate):
    conn = get_db_connection()
    inv_id = f"inv-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    initial_stats = {
        "evidence_files": 0,
        "host_events": 0,
        "network_packets": 0,
        "claims": 0,
        "supported": 0,
        "contradicted": 0,
        "unresolved": 0
    }
    with conn:
        conn.execute(
            "INSERT INTO investigations (id, name, description, created_at, status, stats) VALUES (?, ?, ?, ?, ?, ?)",
            (inv_id, payload.name, payload.description, now_iso, "ACTIVE", json.dumps(initial_stats))
        )
        # Register a default sensor configuration for this investigation
        conn.execute(
            """INSERT INTO sensors (id, investigation_id, sensor_name, interface, monitored_cidrs, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                f"sensor-{inv_id}-01",
                inv_id,
                "Gateway-SPAN-01",
                "eth0",
                json.dumps(["192.168.1.0/24", "198.51.100.0/24", "127.0.0.0/8"]),
                "ACTIVE",
                "Default network tap monitoring gateway traffic"
            )
        )
    conn.close()
    return Investigation(
        id=inv_id,
        name=payload.name,
        description=payload.description,
        created_at=now_iso,
        status="ACTIVE",
        stats=initial_stats
    )


@router.get("/{inv_id}", response_model=Investigation)
def get_investigation(inv_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM investigations WHERE id = ?", (inv_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # Calculate live stats
    ev_count = conn.execute("SELECT COUNT(*) FROM evidence_files WHERE investigation_id = ?", (inv_id,)).fetchone()[0]
    he_count = conn.execute("SELECT COUNT(*) FROM host_events WHERE investigation_id = ?", (inv_id,)).fetchone()[0]
    np_count = conn.execute("SELECT COUNT(*) FROM network_packets WHERE investigation_id = ?", (inv_id,)).fetchone()[0]
    cl_count = conn.execute("SELECT COUNT(*) FROM network_claims WHERE investigation_id = ?", (inv_id,)).fetchone()[0]
    
    sup_count = conn.execute("SELECT COUNT(*) FROM arbitration_results WHERE investigation_id = ? AND verdict = 'SUPPORTED'", (inv_id,)).fetchone()[0]
    con_count = conn.execute("SELECT COUNT(*) FROM arbitration_results WHERE investigation_id = ? AND verdict = 'CONTRADICTED'", (inv_id,)).fetchone()[0]
    unr_count = conn.execute("SELECT COUNT(*) FROM arbitration_results WHERE investigation_id = ? AND verdict = 'UNRESOLVED'", (inv_id,)).fetchone()[0]

    stats = {
        "evidence_files": ev_count,
        "host_events": he_count,
        "network_packets": np_count,
        "claims": cl_count,
        "supported": sup_count,
        "contradicted": con_count,
        "unresolved": unr_count
    }

    inv = Investigation(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        created_at=row["created_at"],
        status=row["status"],
        stats=stats
    )
    conn.close()
    return inv


@router.delete("/{inv_id}")
def delete_investigation(inv_id: str):
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM investigations WHERE id = ?", (inv_id,))
    conn.close()
    return {"status": "deleted", "id": inv_id}
