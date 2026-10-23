"""
TrueTrace SQLite Database Layer
Thread-safe, self-initializing persistence for investigations, evidence, parsed events, claims, and graphs.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

DB_PATH = os.environ.get("TRUETRACE_DB_PATH", str(Path(__file__).parent.parent / "truetrace.db"))


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_db_connection()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            stats TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS evidence_files (
            id TEXT PRIMARY KEY,
            investigation_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            sha256_hash TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            ingested_at TEXT NOT NULL,
            description TEXT,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY(investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS sensors (
            id TEXT PRIMARY KEY,
            investigation_id TEXT NOT NULL,
            sensor_name TEXT NOT NULL,
            interface TEXT DEFAULT 'eth0',
            monitored_cidrs TEXT NOT NULL,
            capture_start TEXT,
            capture_end TEXT,
            packet_loss_detected INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ACTIVE',
            notes TEXT DEFAULT '',
            FOREIGN KEY(investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS host_events (
            id TEXT PRIMARY KEY,
            investigation_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            timestamp_iso TEXT NOT NULL,
            event_type TEXT NOT NULL,
            process_id INTEGER,
            process_name TEXT,
            parent_process_id INTEGER,
            file_path TEXT,
            src_ip TEXT,
            src_port INTEGER,
            dst_ip TEXT,
            dst_port INTEGER,
            protocol TEXT DEFAULT 'TCP',
            bytes_count INTEGER DEFAULT 0,
            return_code INTEGER DEFAULT 0,
            raw_record TEXT DEFAULT '{}',
            FOREIGN KEY(investigation_id) REFERENCES investigations(id) ON DELETE CASCADE,
            FOREIGN KEY(evidence_id) REFERENCES evidence_files(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS network_packets (
            id TEXT PRIMARY KEY,
            investigation_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            timestamp_iso TEXT NOT NULL,
            src_ip TEXT NOT NULL,
            src_port INTEGER NOT NULL,
            dst_ip TEXT NOT NULL,
            dst_port INTEGER NOT NULL,
            protocol TEXT DEFAULT 'TCP',
            tcp_flags TEXT NOT NULL,
            seq_num INTEGER,
            ack_num INTEGER,
            payload_len INTEGER DEFAULT 0,
            sensor_id TEXT DEFAULT 'default-sensor',
            summary TEXT,
            FOREIGN KEY(investigation_id) REFERENCES investigations(id) ON DELETE CASCADE,
            FOREIGN KEY(evidence_id) REFERENCES evidence_files(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS network_claims (
            id TEXT PRIMARY KEY,
            investigation_id TEXT NOT NULL,
            source_event_id TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            src_ip TEXT NOT NULL,
            src_port INTEGER,
            dst_ip TEXT NOT NULL,
            dst_port INTEGER NOT NULL,
            protocol TEXT DEFAULT 'TCP',
            timestamp REAL NOT NULL,
            timestamp_iso TEXT NOT NULL,
            tolerance_seconds REAL DEFAULT 3.0,
            claimed_bytes INTEGER,
            candidate_edge_id TEXT,
            description TEXT NOT NULL,
            FOREIGN KEY(investigation_id) REFERENCES investigations(id) ON DELETE CASCADE,
            FOREIGN KEY(source_event_id) REFERENCES host_events(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS arbitration_results (
            id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            investigation_id TEXT NOT NULL,
            verdict TEXT NOT NULL,
            applied_rule TEXT NOT NULL,
            reasoning TEXT NOT NULL,
            observability_status TEXT NOT NULL,
            observability_reasoning TEXT NOT NULL,
            matching_packet_ids TEXT DEFAULT '[]',
            conflicting_packet_ids TEXT DEFAULT '[]',
            matching_evidence_summaries TEXT DEFAULT '[]',
            timestamp_delta REAL,
            sensor_id TEXT,
            epistemic_notes TEXT DEFAULT '',
            FOREIGN KEY(investigation_id) REFERENCES investigations(id) ON DELETE CASCADE,
            FOREIGN KEY(claim_id) REFERENCES network_claims(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS attack_graphs (
            investigation_id TEXT NOT NULL,
            graph_type TEXT NOT NULL,
            graph_data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(investigation_id, graph_type),
            FOREIGN KEY(investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_host_inv ON host_events(investigation_id);
        CREATE INDEX IF NOT EXISTS idx_net_inv ON network_packets(investigation_id);
        CREATE INDEX IF NOT EXISTS idx_claims_inv ON network_claims(investigation_id);
        CREATE INDEX IF NOT EXISTS idx_arb_claim ON arbitration_results(claim_id);
        """)
    conn.close()


init_db()
