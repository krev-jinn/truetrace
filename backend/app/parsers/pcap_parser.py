"""
TrueTrace PCAP & PCAPNG Forensic Packet Parser
Robust parser extracting L3/L4 transport semantics, TCP handshake/data invariants, and flags.
Supports classic Libpcap format, PCAPNG, with Scapy/DPKT engine fallback.
"""

import struct
import hashlib
import os
import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path
from ..models import NetworkPacket


def compute_file_sha256(filepath: str) -> str:
    """Computes cryptographic SHA-256 digest of an evidence file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class PurePcapReader:
    """
    Lightweight, high-performance pure-Python reader for classic PCAP format.
    Zero external C-library dependency, works across all operating systems.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath

    def parse(self, investigation_id: str, evidence_id: str, sensor_id: str = "sensor-tap-01") -> List[NetworkPacket]:
        packets: List[NetworkPacket] = []
        with open(self.filepath, "rb") as f:
            header = f.read(24)
            if len(header) < 24:
                raise ValueError("PCAP file is too short to contain a valid global header.")

            magic = header[0:4]
            # Standard PCAP magic numbers
            if magic in (b'\xa1\xb2\xc3\xd4', b'\xa1\xb2\x3c\x4d'):
                endianness = ">"  # big-endian
                is_nanosec = (magic == b'\xa1\xb2\x3c\x4d')
            elif magic in (b'\xd4\xc3\xb2\xa1', b'\x4d\x3c\xb2\xa1'):
                endianness = "<"  # little-endian
                is_nanosec = (magic == b'\x4d\x3c\xb2\xa1')
            else:
                raise ValueError(f"Unrecognized PCAP magic header: {magic.hex()}")

            # Unpack global header: magic(4), v_maj(2), v_min(2), thiszone(4), sigfigs(4), snaplen(4), network(4)
            _, _, _, _, _, _, link_type = struct.unpack(f"{endianness}IHHiIII", header)
            
            # link_type 1 is Ethernet, 101 is Raw IP, 113 is Linux Cooked (SLL)
            packet_idx = 0
            while True:
                p_hdr = f.read(16)
                if len(p_hdr) < 16:
                    break
                ts_sec, ts_usec, incl_len, orig_len = struct.unpack(f"{endianness}IIII", p_hdr)
                raw_data = f.read(incl_len)
                if len(raw_data) < incl_len:
                    break

                ts = float(ts_sec) + (float(ts_usec) / (1e9 if is_nanosec else 1e6))
                iso_ts = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()

                parsed_pkt = self._decode_frame(raw_data, link_type, ts, iso_ts, investigation_id, evidence_id, sensor_id, packet_idx)
                if parsed_pkt:
                    packets.append(parsed_pkt)
                    packet_idx += 1

        return packets

    def _decode_frame(self, data: bytes, link_type: int, ts: float, iso_ts: str,
                      investigation_id: str, evidence_id: str, sensor_id: str, idx: int) -> Optional[NetworkPacket]:
        offset = 0
        eth_type = None

        if link_type == 1:  # Ethernet
            if len(data) < 14:
                return None
            eth_type = struct.unpack(">H", data[12:14])[0]
            offset = 14
            # Handle 802.1Q VLAN tag
            if eth_type == 0x8100:
                eth_type = struct.unpack(">H", data[16:18])[0]
                offset = 18
        elif link_type == 113:  # Linux cooked SLL
            if len(data) < 16:
                return None
            eth_type = struct.unpack(">H", data[14:16])[0]
            offset = 16
        elif link_type in (101, 12):  # Raw IPv4 / IPv6
            eth_type = 0x0800
            offset = 0
        else:
            # Default try IPv4 if starting with 0x45
            if len(data) >= 20 and (data[0] >> 4) == 4:
                eth_type = 0x0800
                offset = 0
            else:
                return None

        # We focus on IPv4
        if eth_type != 0x0800 or len(data) < offset + 20:
            return None

        ip_hdr = data[offset:offset + 20]
        v_ihl, tos, total_len, identification, flags_frag, ttl, proto, checksum, s_ip, d_ip = struct.unpack(">BBHHHBBH4s4s", ip_hdr)
        ihl = (v_ihl & 0x0F) * 4
        src_ip = ".".join(map(str, s_ip))
        dst_ip = ".".join(map(str, d_ip))

        l4_offset = offset + ihl
        if proto == 6:  # TCP
            if len(data) < l4_offset + 20:
                return None
            tcp_hdr = data[l4_offset:l4_offset + 20]
            sport, dport, seq, ack, data_offset_flags, win, chk, urp = struct.unpack(">HHIIHHHH", tcp_hdr)
            data_offset = ((data_offset_flags >> 12) & 0x0F) * 4
            flags_byte = data_offset_flags & 0x00FF

            flags = []
            if flags_byte & 0x02: flags.append("SYN")
            if flags_byte & 0x10: flags.append("ACK")
            if flags_byte & 0x04: flags.append("RST")
            if flags_byte & 0x01: flags.append("FIN")
            if flags_byte & 0x08: flags.append("PSH")
            if flags_byte & 0x20: flags.append("URG")

            payload_len = max(0, total_len - ihl - data_offset)
            flag_str = "+".join(flags) if flags else "NONE"
            summary = f"TCP {src_ip}:{sport} -> {dst_ip}:{dport} [{flag_str}] seq={seq} ack={ack} len={payload_len}"

            return NetworkPacket(
                id=f"pkt-{evidence_id}-{idx:05d}",
                investigation_id=investigation_id,
                evidence_id=evidence_id,
                timestamp=ts,
                timestamp_iso=iso_ts,
                src_ip=src_ip,
                src_port=sport,
                dst_ip=dst_ip,
                dst_port=dport,
                protocol="TCP",
                tcp_flags=flags,
                seq_num=seq,
                ack_num=ack,
                payload_len=payload_len,
                sensor_id=sensor_id,
                summary=summary
            )
        elif proto == 17:  # UDP
            if len(data) < l4_offset + 8:
                return None
            sport, dport, ulen, chk = struct.unpack(">HHHH", data[l4_offset:l4_offset + 8])
            payload_len = max(0, ulen - 8)
            summary = f"UDP {src_ip}:{sport} -> {dst_ip}:{dport} len={payload_len}"

            return NetworkPacket(
                id=f"pkt-{evidence_id}-{idx:05d}",
                investigation_id=investigation_id,
                evidence_id=evidence_id,
                timestamp=ts,
                timestamp_iso=iso_ts,
                src_ip=src_ip,
                src_port=sport,
                dst_ip=dst_ip,
                dst_port=dport,
                protocol="UDP",
                tcp_flags=[],
                seq_num=None,
                ack_num=None,
                payload_len=payload_len,
                sensor_id=sensor_id,
                summary=summary
            )
        return None


def parse_pcap_file(filepath: str, investigation_id: str, evidence_id: str, sensor_id: str = "sensor-tap-01") -> List[NetworkPacket]:
    """
    Main parser entry point for PCAP files.
    Tries the high-performance pure-Python parser first; falls back to Scapy/DPKT if format is PCAPNG or specialized.
    """
    try:
        reader = PurePcapReader(filepath)
        return reader.parse(investigation_id, evidence_id, sensor_id)
    except Exception as e:
        # Fallback to Scapy for PCAPNG or unusual headers
        try:
            from scapy.all import rdpcap, IP, TCP, UDP
            scapy_pkts = rdpcap(filepath)
            parsed: List[NetworkPacket] = []
            for idx, p in enumerate(scapy_pkts):
                if IP in p:
                    ip = p[IP]
                    ts = float(p.time)
                    iso_ts = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()
                    src_ip = ip.src
                    dst_ip = ip.dst
                    if TCP in p:
                        tcp = p[TCP]
                        flags = []
                        f = tcp.flags
                        if 'S' in f: flags.append("SYN")
                        if 'A' in f: flags.append("ACK")
                        if 'R' in f: flags.append("RST")
                        if 'F' in f: flags.append("FIN")
                        if 'P' in f: flags.append("PSH")
                        payload_len = len(tcp.payload) if tcp.payload else 0
                        summary = f"TCP {src_ip}:{tcp.sport} -> {dst_ip}:{tcp.dport} [{'+'.join(flags)}] len={payload_len}"
                        parsed.append(NetworkPacket(
                            id=f"pkt-{evidence_id}-{idx:05d}",
                            investigation_id=investigation_id,
                            evidence_id=evidence_id,
                            timestamp=ts,
                            timestamp_iso=iso_ts,
                            src_ip=src_ip,
                            src_port=tcp.sport,
                            dst_ip=dst_ip,
                            dst_port=tcp.dport,
                            protocol="TCP",
                            tcp_flags=flags,
                            seq_num=tcp.seq,
                            ack_num=tcp.ack,
                            payload_len=payload_len,
                            sensor_id=sensor_id,
                            summary=summary
                        ))
            return parsed
        except Exception as scapy_err:
            raise ValueError(f"Failed to parse PCAP evidence file: {e} | Scapy fallback error: {scapy_err}")
