"""
Unit Tests for TrueTrace Evidence Parsers (PCAP & Host Logs)
"""

import os
import json
import pytest
from scapy.all import Ether, IP, TCP, wrpcap

from backend.app.parsers.pcap_parser import parse_pcap_file, compute_file_sha256
from backend.app.parsers.host_log_parser import parse_host_log_file, parse_timestamp
from backend.app.models import HostEventType, ClaimType


def test_pcap_parser(tmp_path):
    pcap_path = str(tmp_path / "test_traffic.pcap")
    pkts = [
        Ether()/IP(src="192.168.1.10", dst="192.168.1.50")/TCP(sport=4444, dport=80, flags="S", seq=100),
        Ether()/IP(src="192.168.1.50", dst="192.168.1.10")/TCP(sport=80, dport=4444, flags="SA", seq=500, ack=101),
        Ether()/IP(src="192.168.1.10", dst="192.168.1.50")/TCP(sport=4444, dport=80, flags="A", seq=101, ack=501),
        Ether()/IP(src="192.168.1.10", dst="192.168.1.50")/TCP(sport=4444, dport=80, flags="PA", seq=101, ack=501)/b"GET /index.html HTTP/1.1\r\n\r\n"
    ]
    for idx, p in enumerate(pkts):
        p.time = 1700000000.0 + (idx * 0.01)
    wrpcap(pcap_path, pkts)

    # Compute SHA-256
    sha = compute_file_sha256(pcap_path)
    assert len(sha) == 64

    # Parse packets
    parsed = parse_pcap_file(pcap_path, "inv-test", "ev-pcap-1")
    assert len(parsed) == 4
    
    # Check flags and 5-tuple
    assert parsed[0].src_ip == "192.168.1.10"
    assert parsed[0].dst_port == 80
    assert "SYN" in parsed[0].tcp_flags
    assert "ACK" not in parsed[0].tcp_flags

    assert "SYN" in parsed[1].tcp_flags and "ACK" in parsed[1].tcp_flags
    assert "ACK" in parsed[2].tcp_flags and "SYN" not in parsed[2].tcp_flags
    assert parsed[3].payload_len > 0


def test_host_log_parser(tmp_path):
    log_path = str(tmp_path / "audit_events.json")
    records = [
        {
            "event_type": "PROCESS_SPAWN",
            "timestamp": 1700000000.0,
            "process_id": 501,
            "process_name": "mimikatz.exe",
            "parent_process_id": 400
        },
        {
            "event_type": "FILE_READ",
            "timestamp": 1700000001.0,
            "process_id": 501,
            "file_path": "C:\\Windows\\System32\\config\\SAM"
        },
        {
            "event_type": "SOCKET_CONNECT",
            "timestamp": 1700000002.0,
            "process_id": 501,
            "process_name": "mimikatz.exe",
            "src_ip": "192.168.1.10",
            "src_port": 49155,
            "dst_ip": "198.51.100.23",
            "dst_port": 443,
            "protocol": "TCP"
        },
        {
            "event_type": "SOCKET_SEND",
            "timestamp": 1700000003.0,
            "process_id": 501,
            "process_name": "mimikatz.exe",
            "src_ip": "192.168.1.10",
            "src_port": 49155,
            "dst_ip": "198.51.100.23",
            "dst_port": 443,
            "bytes_count": 2048
        }
    ]
    with open(log_path, "w") as f:
        json.dump(records, f)

    events, claims = parse_host_log_file(log_path, "inv-test", "ev-host-1")
    assert len(events) == 4
    assert len(claims) == 2  # 1 connect + 1 send

    assert claims[0].claim_type == ClaimType.TCP_HANDSHAKE
    assert claims[0].dst_ip == "198.51.100.23"
    assert claims[0].dst_port == 443

    assert claims[1].claim_type == ClaimType.DATA_TRANSFER
    assert claims[1].claimed_bytes == 2048


def test_malformed_host_log_handling(tmp_path):
    bad_log = str(tmp_path / "corrupt.jsonl")
    with open(bad_log, "w") as f:
        f.write('{"event_type": "PROCESS_SPAWN", "process_id": 100}\n')
        f.write('CORRUPTED LINE NOT JSON\n')
        f.write('{"event_type": "SOCKET_CONNECT", "process_id": 100, "dst_ip": "10.0.0.1", "dst_port": 80}\n')

    events, claims = parse_host_log_file(bad_log, "inv-test", "ev-corrupt")
    assert len(events) == 2
    assert len(claims) == 1
