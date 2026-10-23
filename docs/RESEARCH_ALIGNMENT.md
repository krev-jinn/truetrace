# TrueTrace: Research Alignment & Theoretical Foundation

**Project Name:** TrueTrace  
**Excel-Safe Title:** TrueTrace: A Network-Grounded Framework for Attack Trace Verification  
**Technical Research Title:** Falsification-Driven Attack Reconstruction via Observability-Aware Network Invariant Arbitration  
**Author:** Pranayaa C  
**Guide:** Dr. Aaseegha M D  
**Primary Reference:** TrueTrace First-Review Presentation & Literature Review  

---

## 1. Executive Summary & Research Gap

### 1.1 The Core Problem
Modern digital forensics and incident response rely heavily on host-level audit logs (e.g., Linux auditd, Windows Event Logs/Sysmon, DARPA TC CDM records) to reconstruct cyberattacks and construct provenance causal graphs. However:
1. **OS-Level Over-Approximation:** Host audit logs report system call invocations at the OS boundary. A successful `connect()` or `write()` system call only indicates that an operation was requested or that bytes were accepted into the local kernel socket buffer. It does **not** prove that packets crossed physical network interfaces, reached the remote endpoint, or were processed by the remote application.
2. **Intermediate Failures:** Firewalls, middleboxes, stateful packet filters, TCP resets (`RST`), routing failures, or target application crashes may discard or terminate the connection immediately after the host system call returns.
3. **Forensic Vulnerability:** If a forensic reconstruction tool blindly converts host-level socket events into causal edges in an attack graph, the resulting narrative is over-approximated, potentially misleading investigators into attributing successful data exfiltration or remote command execution where none occurred.

### 1.2 Literature Review Summary & Gap Analysis

As established in the TrueTrace research review:

| Research Domain | Representative Works | Key Contributions | Forensic Limitation / Research Gap |
| :--- | :--- | :--- | :--- |
| **Host Provenance & Capture** | BEEP, ProTracer, RAIN, Kairos | Fine-grained capture of process, file, and system-call causality. | Evidence is strictly host-observed; over-approximates cross-host communication. |
| **Provenance Reduction & Abstraction** | LogGC, NodeMerge, WATSON, MPI | Reduces provenance graph volume via causality-preserving heuristics. | Optimization focuses on scalability; abstracts away network packet details needed for ground-truth verification. |
| **Attack Reconstruction** | SLEUTH, HOLMES, POIROT, ATLAS, NodLink | Correlates multi-stage attack steps to identify attack subgraphs. | Network telemetry is used merely for *correlation/enrichment*, never to *falsify* or contradict an invalid host causal claim. |
| **Network Verification & Observability** | Anteater, Batfish, VeriFlow, Vaseghipanah et al. (MDPI) | Verifies network invariant invariants, forwarding rules, and observability limits. | Validates network state/policies, but does not arbitrate host provenance attack graphs against packet captures. |

**Consolidated Research Gap:**  
> *"Existing research captures and reconstructs host provenance, while network research verifies network behaviour. However, there is no unified mechanism in the reviewed literature that uses network/transport evidence to arbitrate individual host-derived causal claims in an observability-aware manner."*

---

## 2. Core Methodological Contributions

TrueTrace addresses this gap through five foundational principles:

```
[ Host Audit Logs ] ---> [ Candidate Attack Graph ] (Hypotheses)
                                |
[ Network Packet Capture ] ---> [ Observability Check ] ---> [ Evidence Arbitration ] ---> [ Refined Attack Graph ]
                                (Sensor Topology & Loss)   - SUPPORTED               - Retained
                                                           - CONTRADICTED            - Falsified / Marked
                                                           - UNRESOLVED              - Preserved w/ Uncertainty
```

### Principle 1: System Calls as Hypotheses, Not Established Ground Truth
Network-dependent host audit records (e.g. `connect()`, `send()`, `write()`, `recv()`) are ingested as candidate hypotheses rather than verified causal facts.

### Principle 2: Observability-Aware Arbitration
Network evidence is collected independently (via packet captures, hardware taps, SPAN ports, firewall drop logs). Before any judgment is rendered, the system evaluates **sensor observability**:
- Was a sensor physically or topologically positioned to monitor this traffic flow (CIDR / subnet match)?
- Was the sensor active and capturing during the specific timestamp interval?
- Did the sensor record buffer overruns, ring drops, or frame corruptions?

### Principle 3: Epistemic Invariant: Absence of Evidence $\neq$ Evidence of Absence
> **Crucial Invariant:** *Absence of network evidence must never be treated as proof of absence unless full observability is rigorously established.*  
If a packet is missing but the sensor did not monitor that subnet or was disabled at that timestamp, the verdict is strictly **`UNRESOLVED`**, preserving the investigator's uncertainty.

### Principle 4: Three-Valued Arbitration Logic
1. **`SUPPORTED`**: Independent network observations confirm the specific transport invariant (e.g. 3-way TCP handshake completed with SYN, SYN-ACK, ACK, and matching sequence/acknowledgement progression).
2. **`CONTRADICTED`**: Independent, reliable evidence directly refutes the claim (e.g. host recorded a connection attempt, but network sensor recorded a `RST/ACK` connection refusal from a closed port or an upstream firewall drop).
3. **`UNRESOLVED`**: Evidence is incomplete, ambiguous, outside sensor coverage, or timestamp tolerances are exceeded.

### Principle 5: Uncertainty-Preserving Graph Refinement
The attack graph is refined without destructive deletion:
- `SUPPORTED` edges are confirmed and weighted as validated narrative milestones.
- `CONTRADICTED` edges are visually marked with falsification evidence, pruning false branches.
- `UNRESOLVED` edges are preserved with explicit uncertainty indicators, prompting forensic examiners to investigate visibility gaps.

---

## 3. Claim-to-Implementation Traceability Matrix

| Research Claim / Requirement | Implementation Component | Required Evidence & Input | Verification Status |
| :--- | :--- | :--- | :--- |
| **C1: Host System Call Ingestion** | `backend/app/parsers/host_log_parser.py` | JSON / Sysmon / Auditd / DARPA TC CDM logs | **Implemented & Tested** |
| **C2: Candidate Attack Graph Construction** | `backend/app/engine/graph_builder.py` | Parsed process, file, and socket host events | **Implemented & Tested** |
| **C3: Network Evidence Ingestion** | `backend/app/parsers/pcap_parser.py` | Raw PCAP / PCAPNG packet captures | **Implemented & Tested** |
| **C4: Sensor Observability Matrix** | `backend/app/engine/observability.py` | Sensor CIDR topology, capture time-window, drop status | **Implemented & Tested** |
| **C5: Transport Invariant Arbitration** | `backend/app/engine/arbitration.py` | 5-tuple flow matching, TCP handshake & data invariants | **Implemented & Tested** |
| **C6: Three-Valued Verdict Generation** | `backend/app/engine/arbitration.py` | Preconditioned rule execution with explicit reasoning | **Implemented & Tested** |
| **C7: Uncertainty-Preserving Graph Refinement** | `backend/app/engine/graph_builder.py` | NetworkX candidate graph + arbitration result mapping | **Implemented & Tested** |
| **C8: Controlled Scenarios (Cases 1, 2, 3)** | `backend/app/scenarios/` | Real TCP experiment & reproducible forensic fixtures | **Implemented & Tested** |
| **C9: Forensics Investigation Interface** | `frontend/` (React, Vite, @xyflow/react) | 8 dedicated workbench views with evidence drill-down | **Implemented & Tested** |
| **C10: Cryptographic Provenance & Export** | `backend/app/api/reports.py` | SHA-256 digests, reproducible JSON/Markdown reports | **Implemented & Tested** |

---

## 4. Benchmark Datasets & Real-World Alignment

1. **DARPA Transparent Computing (TC):** DARPA TC datasets (THEIA, CADETS, TRACE, FiveDirections) standardise Common Data Model (CDM) host provenance. TrueTrace ingest formats mirror TC CDM process and network events.
2. **MAWI DITL Traffic:** Used in literature to validate packet transport behavior. TrueTrace PCAP parsers handle standard pcap/pcapng packet records.
3. **Mandiant M-Trends 2026 Reference:** Target edge devices (VPNs, firewalls, network appliances) frequently lack host endpoint agents. TrueTrace directly models edge sensor coverage and visibility boundaries.
