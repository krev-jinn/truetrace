"""
TrueTrace Benchmark Scenarios & Forensics Fixtures
Generates verifiable, reproducible datasets representing DARPA TC CDM provenance and real-world attack patterns.
"""

import os
import json
import time
import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path

from ..models import (
    HostEvent, HostEventType, NetworkPacket, NetworkClaim,
    SensorConfig, ClaimType
)
from ..parsers.pcap_parser import compute_file_sha256


def create_scenario_fixtures(base_evidence_dir: str) -> Dict[str, Any]:
    """
    Creates reproducible evidence files on disk (host JSON logs and PCAP files)
    for the core evaluation scenarios.
    """
    os.makedirs(base_evidence_dir, exist_ok=True)
    scenarios_meta = {}

    t0 = 1718000000.0  # Stable baseline timestamp
    t0_iso = datetime.datetime.fromtimestamp(t0, tz=datetime.timezone.utc).isoformat()

    # =========================================================================
    # SCENARIO 1: SUPPORTED — Full Handshake & Acknowledged Data Exfiltration
    # Process 'exfil_agent' connects to 198.51.100.4:443 and exfiltrates 1024 bytes.
    # =========================================================================
    s1_dir = os.path.join(base_evidence_dir, "scenario_1_supported")
    os.makedirs(s1_dir, exist_ok=True)

    s1_host_events = [
        {
            "event_type": "PROCESS_SPAWN",
            "timestamp": t0,
            "process_id": 1010,
            "process_name": "bash",
            "parent_process_id": 1000
        },
        {
            "event_type": "FILE_READ",
            "timestamp": t0 + 0.1,
            "process_id": 1010,
            "process_name": "bash",
            "file_path": "/etc/shadow"
        },
        {
            "event_type": "PROCESS_SPAWN",
            "timestamp": t0 + 0.2,
            "process_id": 1025,
            "process_name": "exfil_agent",
            "parent_process_id": 1010
        },
        {
            "event_type": "SOCKET_CONNECT",
            "timestamp": t0 + 0.5,
            "process_id": 1025,
            "process_name": "exfil_agent",
            "src_ip": "192.168.1.105",
            "src_port": 49152,
            "dst_ip": "198.51.100.4",
            "dst_port": 443,
            "protocol": "TCP",
            "return_code": 0
        },
        {
            "event_type": "SOCKET_SEND",
            "timestamp": t0 + 0.7,
            "process_id": 1025,
            "process_name": "exfil_agent",
            "src_ip": "192.168.1.105",
            "src_port": 49152,
            "dst_ip": "198.51.100.4",
            "dst_port": 443,
            "protocol": "TCP",
            "bytes_count": 1024,
            "return_code": 1024
        }
    ]
    s1_host_path = os.path.join(s1_dir, "host_events.json")
    with open(s1_host_path, "w") as f:
        json.dump(s1_host_events, f, indent=2)

    # Generate synthetic PCAP for Scenario 1
    from scapy.all import Ether, IP, TCP, wrpcap
    s1_pkts = [
        # SYN
        Ether()/IP(src="192.168.1.105", dst="198.51.100.4")/TCP(sport=49152, dport=443, flags="S", seq=1000),
        # SYN+ACK
        Ether()/IP(src="198.51.100.4", dst="192.168.1.105")/TCP(sport=443, dport=49152, flags="SA", seq=5000, ack=1001),
        # Handshake ACK
        Ether()/IP(src="192.168.1.105", dst="198.51.100.4")/TCP(sport=49152, dport=443, flags="A", seq=1001, ack=5001),
        # Data segment (PSH+ACK, 1024 bytes)
        Ether()/IP(src="192.168.1.105", dst="198.51.100.4")/TCP(sport=49152, dport=443, flags="PA", seq=1001, ack=5001)/("A"*1024),
        # Server ACK
        Ether()/IP(src="198.51.100.4", dst="192.168.1.105")/TCP(sport=443, dport=49152, flags="A", seq=5001, ack=2025)
    ]
    # Set packet timestamps relative to t0
    for idx, p in enumerate(s1_pkts):
        p.time = t0 + 0.5 + (idx * 0.05)
    s1_pcap_path = os.path.join(s1_dir, "capture.pcap")
    wrpcap(s1_pcap_path, s1_pkts)

    scenarios_meta["scenario_1_supported"] = {
        "title": "Case 1: Fully Supported Exfiltration",
        "description": "Mimikatz/bash exfiltration where independent PCAP confirms 3-way handshake and acknowledged payload.",
        "host_file": s1_host_path,
        "pcap_file": s1_pcap_path,
        "host_sha256": compute_file_sha256(s1_host_path),
        "pcap_sha256": compute_file_sha256(s1_pcap_path),
        "sensor": {
            "sensor_name": "gateway-tap-01",
            "monitored_cidrs": ["192.168.1.0/24", "198.51.100.0/24"],
            "packet_loss_detected": False,
            "status": "ACTIVE"
        }
    }

    # =========================================================================
    # SCENARIO 2: CONTRADICTED — Connection Refusal / RST (Closed Port)
    # Host log claims powershell connected to 192.168.1.150:445, but PCAP shows RST.
    # =========================================================================
    s2_dir = os.path.join(base_evidence_dir, "scenario_2_contradicted")
    os.makedirs(s2_dir, exist_ok=True)

    s2_host_events = [
        {
            "event_type": "PROCESS_SPAWN",
            "timestamp": t0 + 10.0,
            "process_id": 2040,
            "process_name": "powershell.exe",
            "parent_process_id": 900
        },
        {
            "event_type": "SOCKET_CONNECT",
            "timestamp": t0 + 10.2,
            "process_id": 2040,
            "process_name": "powershell.exe",
            "src_ip": "192.168.1.105",
            "src_port": 50110,
            "dst_ip": "192.168.1.150",
            "dst_port": 445,
            "protocol": "TCP",
            "return_code": 0  # Host log erroneously recorded success or buffered state
        }
    ]
    s2_host_path = os.path.join(s2_dir, "host_events.json")
    with open(s2_host_path, "w") as f:
        json.dump(s2_host_events, f, indent=2)

    # Synthetic PCAP for Scenario 2: SYN -> RST/ACK (Connection Refused)
    s2_pkts = [
        Ether()/IP(src="192.168.1.105", dst="192.168.1.150")/TCP(sport=50110, dport=445, flags="S", seq=3000),
        Ether()/IP(src="192.168.1.150", dst="192.168.1.105")/TCP(sport=445, dport=50110, flags="RA", seq=0, ack=3001)
    ]
    for idx, p in enumerate(s2_pkts):
        p.time = t0 + 10.2 + (idx * 0.02)
    s2_pcap_path = os.path.join(s2_dir, "capture.pcap")
    wrpcap(s2_pcap_path, s2_pkts)

    scenarios_meta["scenario_2_contradicted"] = {
        "title": "Case 2: Contradicted Connection (RST / Port Refusal)",
        "description": "Host log claims lateral movement to 192.168.1.150:445, but independent PCAP proves remote port was closed via TCP RST/ACK.",
        "host_file": s2_host_path,
        "pcap_file": s2_pcap_path,
        "host_sha256": compute_file_sha256(s2_host_path),
        "pcap_sha256": compute_file_sha256(s2_pcap_path),
        "sensor": {
            "sensor_name": "switch-span-02",
            "monitored_cidrs": ["192.168.1.0/24"],
            "packet_loss_detected": False,
            "status": "ACTIVE"
        }
    }

    # =========================================================================
    # SCENARIO 3: UNRESOLVED — Sensor Visibility Gap (Edge Blindspot)
    # Host log claims connection to 172.16.50.2:8443, but sensor only monitors 192.168.1.0/24.
    # Engine must return UNRESOLVED (not Contradicted) because absence of evidence != evidence of absence.
    # =========================================================================
    s3_dir = os.path.join(base_evidence_dir, "scenario_3_unresolved")
    os.makedirs(s3_dir, exist_ok=True)

    s3_host_events = [
        {
            "event_type": "PROCESS_SPAWN",
            "timestamp": t0 + 20.0,
            "process_id": 3100,
            "process_name": "vpn_agent",
            "parent_process_id": 800
        },
        {
            "event_type": "SOCKET_CONNECT",
            "timestamp": t0 + 20.3,
            "process_id": 3100,
            "process_name": "vpn_agent",
            "src_ip": "10.0.0.5",
            "src_port": 52000,
            "dst_ip": "172.16.50.2",
            "dst_port": 8443,
            "protocol": "TCP",
            "return_code": 0
        }
    ]
    s3_host_path = os.path.join(s3_dir, "host_events.json")
    with open(s3_host_path, "w") as f:
        json.dump(s3_host_events, f, indent=2)

    # Empty PCAP or capture containing only unrelated packets
    s3_pkts = [
        Ether()/IP(src="192.168.1.1", dst="192.168.1.2")/TCP(sport=80, dport=8080, flags="A", seq=1, ack=1)
    ]
    s3_pkts[0].time = t0 + 20.0
    s3_pcap_path = os.path.join(s3_dir, "capture.pcap")
    wrpcap(s3_pcap_path, s3_pkts)

    scenarios_meta["scenario_3_unresolved"] = {
        "title": "Case 3: Unresolved (Sensor Visibility Gap)",
        "description": "Host claims edge VPN connection to 172.16.50.2:8443. Sensor only monitored 192.168.1.0/24. Engine correctly returns UNRESOLVED rather than falsification.",
        "host_file": s3_host_path,
        "pcap_file": s3_pcap_path,
        "host_sha256": compute_file_sha256(s3_host_path),
        "pcap_sha256": compute_file_sha256(s3_pcap_path),
        "sensor": {
            "sensor_name": "corp-lan-sensor",
            "monitored_cidrs": ["192.168.1.0/24"],  # Does NOT cover 172.16.50.0/24
            "packet_loss_detected": False,
            "status": "ACTIVE"
        }
    }

    # =========================================================================
    # SCENARIO 4: CONTRADICTED DATA TRANSFER — Write() Buffered But Reset Prior to Wire
    # Host log reports write(8192 bytes), but network capture shows RST immediately after handshake.
    # =========================================================================
    s4_dir = os.path.join(base_evidence_dir, "scenario_4_write_buffered_reset")
    os.makedirs(s4_dir, exist_ok=True)

    s4_host_events = [
        {
            "event_type": "PROCESS_SPAWN",
            "timestamp": t0 + 30.0,
            "process_id": 4010,
            "process_name": "nc.exe",
            "parent_process_id": 1000
        },
        {
            "event_type": "SOCKET_CONNECT",
            "timestamp": t0 + 30.1,
            "process_id": 4010,
            "process_name": "nc.exe",
            "src_ip": "192.168.1.105",
            "src_port": 53000,
            "dst_ip": "203.0.113.88",
            "dst_port": 9001,
            "protocol": "TCP",
            "return_code": 0
        },
        {
            "event_type": "SOCKET_SEND",
            "timestamp": t0 + 30.3,
            "process_id": 4010,
            "process_name": "nc.exe",
            "src_ip": "192.168.1.105",
            "src_port": 53000,
            "dst_ip": "203.0.113.88",
            "dst_port": 9001,
            "protocol": "TCP",
            "bytes_count": 8192,
            "return_code": 8192  # Kernel accepted into socket buffer
        }
    ]
    s4_host_path = os.path.join(s4_dir, "host_events.json")
    with open(s4_host_path, "w") as f:
        json.dump(s4_host_events, f, indent=2)

    # PCAP: Handshake completes, but server sends RST before client can send payload
    s4_pkts = [
        Ether()/IP(src="192.168.1.105", dst="203.0.113.88")/TCP(sport=53000, dport=9001, flags="S", seq=7000),
        Ether()/IP(src="203.0.113.88", dst="192.168.1.105")/TCP(sport=9001, dport=53000, flags="SA", seq=8000, ack=7001),
        Ether()/IP(src="192.168.1.105", dst="203.0.113.88")/TCP(sport=53000, dport=9001, flags="A", seq=7001, ack=8001),
        # Immediate RST before data
        Ether()/IP(src="203.0.113.88", dst="192.168.1.105")/TCP(sport=9001, dport=53000, flags="R", seq=8001, ack=7001)
    ]
    for idx, p in enumerate(s4_pkts):
        p.time = t0 + 30.1 + (idx * 0.05)
    s4_pcap_path = os.path.join(s4_dir, "capture.pcap")
    wrpcap(s4_pcap_path, s4_pkts)

    scenarios_meta["scenario_4_write_buffered_reset"] = {
        "title": "Case 4: Contradicted Exfiltration (write() Buffered, Wire Reset)",
        "description": "Demonstrates core research thesis: host write() return value != network transport delivery. Socket torn down by RST.",
        "host_file": s4_host_path,
        "pcap_file": s4_pcap_path,
        "host_sha256": compute_file_sha256(s4_host_path),
        "pcap_sha256": compute_file_sha256(s4_pcap_path),
        "sensor": {
            "sensor_name": "dmz-tap-01",
            "monitored_cidrs": ["192.168.1.0/24", "203.0.113.0/24"],
            "packet_loss_detected": False,
            "status": "ACTIVE"
        }
    }

    return scenarios_meta
