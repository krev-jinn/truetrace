"""
TrueTrace Host Audit Log & Provenance Parser
Extracts host provenance records (processes, files, sockets) and synthesizes candidate network claims.
Supports Linux auditd, Sysmon JSON, DARPA TC CDM JSON/JSONL, and generic forensic event logs.
"""

import json
import os
import datetime
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from ..models import HostEvent, HostEventType, NetworkClaim, ClaimType


def parse_timestamp(val: Any) -> Tuple[float, str]:
    """Normalizes epoch or ISO8601 timestamps into (unix_float, iso_utc_string)."""
    if isinstance(val, (int, float)):
        # DARPA TC sometimes provides nanoseconds or microseconds
        ts_float = float(val)
        if ts_float > 1e16:  # nanoseconds
            ts_float /= 1e9
        elif ts_float > 1e13:  # microseconds
            ts_float /= 1e6
        elif ts_float > 1e11:  # milliseconds
            ts_float /= 1e3
        dt = datetime.datetime.fromtimestamp(ts_float, tz=datetime.timezone.utc)
        return ts_float, dt.isoformat()
    elif isinstance(val, str):
        # Try parse ISO format
        cleaned = val.replace("Z", "+00:00")
        try:
            dt = datetime.datetime.fromisoformat(cleaned)
            return dt.timestamp(), dt.isoformat()
        except Exception:
            # Fallback float in string
            try:
                f = float(val)
                return parse_timestamp(f)
            except Exception:
                now = datetime.datetime.now(datetime.timezone.utc)
                return now.timestamp(), now.isoformat()
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.timestamp(), now.isoformat()


def parse_host_log_file(filepath: str, investigation_id: str, evidence_id: str) -> Tuple[List[HostEvent], List[NetworkClaim]]:
    """
    Parses a host log file (JSON or JSONL) into structured HostEvent objects and candidate NetworkClaims.
    """
    raw_lines: List[Dict[str, Any]] = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read().strip()
        if content.startswith("[") and content.endswith("]"):
            raw_lines = json.loads(content)
        else:
            for line in content.splitlines():
                line = line.strip()
                if line:
                    try:
                        raw_lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    events: List[HostEvent] = []
    claims: List[NetworkClaim] = []

    for idx, rec in enumerate(raw_lines):
        evt_id = f"hevt-{evidence_id}-{idx:04d}"
        
        # Determine event type
        evt_type_raw = str(rec.get("event_type") or rec.get("type") or rec.get("action") or "").upper()
        
        # Mapping to HostEventType
        if any(k in evt_type_raw for k in ["SPAWN", "EXEC", "FORK", "PROCESS"]):
            evt_type = HostEventType.PROCESS_SPAWN
        elif any(k in evt_type_raw for k in ["CONNECT", "SOCK_CONN", "NETWORK_CONN"]):
            evt_type = HostEventType.SOCKET_CONNECT
        elif any(k in evt_type_raw for k in ["SEND", "WRITE_SOCK", "SOCK_WRITE", "OUTBOUND"]):
            evt_type = HostEventType.SOCKET_SEND
        elif any(k in evt_type_raw for k in ["RECV", "READ_SOCK", "INBOUND"]):
            evt_type = HostEventType.SOCKET_RECV
        elif any(k in evt_type_raw for k in ["FILE_READ", "READ"]):
            evt_type = HostEventType.FILE_READ
        elif any(k in evt_type_raw for k in ["FILE_WRITE", "WRITE"]):
            evt_type = HostEventType.FILE_WRITE
        elif any(k in evt_type_raw for k in ["CLOSE", "DISCONNECT"]):
            evt_type = HostEventType.SOCKET_CLOSE
        elif any(k in evt_type_raw for k in ["FIREWALL", "DROP", "BLOCK"]):
            evt_type = HostEventType.FIREWALL_DROP
        else:
            evt_type = HostEventType.PROCESS_SPAWN

        ts_val, ts_iso = parse_timestamp(rec.get("timestamp") or rec.get("time") or rec.get("@timestamp") or 0)
        
        proc_id = rec.get("process_id") or rec.get("pid")
        proc_name = rec.get("process_name") or rec.get("exe") or rec.get("image") or rec.get("comm")
        ppid = rec.get("parent_process_id") or rec.get("ppid")
        file_path = rec.get("file_path") or rec.get("path") or rec.get("target_file")
        
        src_ip = rec.get("src_ip") or rec.get("source_ip") or rec.get("s_ip")
        src_port = rec.get("src_port") or rec.get("source_port") or rec.get("s_port")
        dst_ip = rec.get("dst_ip") or rec.get("destination_ip") or rec.get("d_ip")
        dst_port = rec.get("dst_port") or rec.get("destination_port") or rec.get("d_port")
        proto = (rec.get("protocol") or rec.get("proto") or "TCP").upper()
        bytes_count = rec.get("bytes_count") or rec.get("bytes") or rec.get("length") or 0
        ret_code = rec.get("return_code") or rec.get("ret") or 0

        event = HostEvent(
            id=evt_id,
            investigation_id=investigation_id,
            evidence_id=evidence_id,
            timestamp=ts_val,
            timestamp_iso=ts_iso,
            event_type=evt_type,
            process_id=int(proc_id) if proc_id is not None else None,
            process_name=proc_name,
            parent_process_id=int(ppid) if ppid is not None else None,
            file_path=file_path,
            src_ip=src_ip,
            src_port=int(src_port) if src_port is not None else None,
            dst_ip=dst_ip,
            dst_port=int(dst_port) if dst_port is not None else None,
            protocol=proto,
            bytes_count=int(bytes_count) if bytes_count else 0,
            return_code=int(ret_code) if ret_code is not None else 0,
            raw_record=rec
        )
        events.append(event)

        # Synthesize Network Claim if the event has network implications
        if evt_type == HostEventType.SOCKET_CONNECT and dst_ip and dst_port:
            claim_id = f"claim-{investigation_id}-{len(claims)+1:03d}"
            desc = f"Process '{proc_name or 'unknown'}' (PID {proc_id}) claims to have established a TCP connection to {dst_ip}:{dst_port}"
            claims.append(NetworkClaim(
                id=claim_id,
                investigation_id=investigation_id,
                source_event_id=evt_id,
                claim_type=ClaimType.TCP_HANDSHAKE,
                src_ip=src_ip or "0.0.0.0",
                src_port=int(src_port) if src_port else None,
                dst_ip=dst_ip,
                dst_port=int(dst_port),
                protocol=proto,
                timestamp=ts_val,
                timestamp_iso=ts_iso,
                tolerance_seconds=rec.get("tolerance_seconds", 3.0),
                claimed_bytes=None,
                description=desc
            ))
        elif evt_type == HostEventType.SOCKET_SEND and dst_ip and dst_port:
            claim_id = f"claim-{investigation_id}-{len(claims)+1:03d}"
            desc = f"Process '{proc_name or 'unknown'}' (PID {proc_id}) claims to have transmitted {bytes_count} bytes to {dst_ip}:{dst_port}"
            claims.append(NetworkClaim(
                id=claim_id,
                investigation_id=investigation_id,
                source_event_id=evt_id,
                claim_type=ClaimType.DATA_TRANSFER,
                src_ip=src_ip or "0.0.0.0",
                src_port=int(src_port) if src_port else None,
                dst_ip=dst_ip,
                dst_port=int(dst_port),
                protocol=proto,
                timestamp=ts_val,
                timestamp_iso=ts_iso,
                tolerance_seconds=rec.get("tolerance_seconds", 3.0),
                claimed_bytes=int(bytes_count) if bytes_count else None,
                description=desc
            ))

    return events, claims
