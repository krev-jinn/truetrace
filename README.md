# TrueTrace: A Network-Grounded Framework for Attack Trace Verification

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passed-brightgreen.svg)](#running-the-automated-test-suite)
[![License](https://img.shields.io/badge/License-Academic%20Research-purple.svg)]()

> **Technical Research Title:** *Falsification-Driven Attack Reconstruction via Observability-Aware Network Invariant Arbitration*  
> **Author:** Pranayaa C  
> **Guided By:** Dr. Aaseegha M D  
> **Primary Source:** TrueTrace Presentation & Literature Review

---

## 1. Research Motivation & Core Contribution

Modern digital forensics relies on host-level audit logs (auditd, Sysmon, DARPA TC CDM) to reconstruct attack narratives into causal provenance graphs. However, **these logs show what the OS reports, not what occurred across the network**:
- An OS `write()` or `send()` return value only means bytes were accepted into the local kernel socket buffer.
- Intermediate firewalls, drops, routing timeouts, or TCP resets (`RST`) may prevent the communication from completing.
- Conventional provenance engines (SLEUTH, HOLMES, ATLAS) treat network evidence merely as an additional correlation source rather than evidence capable of **falsifying** a host-derived claim.

**TrueTrace addresses this gap:**
1. Ingests host-reported network operations as **hypotheses** rather than established facts.
2. Cross-checks hypotheses against independently captured network evidence (PCAP/PCAPNG).
3. Evaluates **sensor observability** (topological CIDR coverage, capture time boundaries, and hardware loss flags).
4. Strictly enforces the epistemic invariant: **Absence of evidence is NOT evidence of absence** unless complete observability is proven.
5. Classifies claims into three explicit verdicts:
   - **`SUPPORTED`**: Independent packet evidence confirms the transport invariant (e.g. 3-way handshake or acknowledged payload).
   - **`CONTRADICTED`**: Reliable evidence conflicts with the claim (e.g. TCP `RST/ACK` connection refusal on a closed port or premature socket reset).
   - **`UNRESOLVED`**: Evidence is incomplete, ambiguous, or the communication was outside sensor coverage.
6. Refines the candidate attack graph **without silently deleting unresolved claims**.

---

## 2. Architecture & Workflow

```
+-----------------------------------------------------------------------------------+
|                              TrueTrace Architecture                               |
+-----------------------------------------------------------------------------------+

 [ Host Audit Logs ]                      [ Network Packet Captures (PCAP) ]
         |                                                 |
         v (JSON / Sysmon / TC CDM)                        v (Classic PCAP & PCAPNG)
 +-----------------------------+                  +--------------------------------+
 |     Host Event Parser       |                  |     Forensic PCAP Parser       |
 +-----------------------------+                  +--------------------------------+
         |                                                 |
         |--> Candidate Claims                             |--> L3/L4 Wire Telemetry
         |--> Process / File Graph Nodes                   |    (TCP flags, seq/ack, bytes)
         v                                                 v
 +---------------------------------------------------------------------------------+
 |                     Observability-Aware Verification Engine                     |
 |  1. Topologic CIDR & Temporal Bounds Check                                      |
 |  2. Hardware Packet Loss / Ring Buffer Assessment                               |
 |  3. Epistemic Preconditions (Absence != Non-occurrence)                         |
 |  4. Directional 5-Tuple Correlation (tc ± Δt)                                   |
 |  5. Transport Invariant Rules (INV-TCP-01, INV-TCP-02, INV-DATA-01, etc.)       |
 +---------------------------------------------------------------------------------+
         |
         v Three-Valued Arbitration Verdicts
 +---------------------------------------------------------------------------------+
 |                    Uncertainty-Preserving Attack Graph                          |
 |  • Candidate Graph: Initial reconstructed narrative (Hypotheses)                |
 |  • Refined Graph: Retains Supported, marks Contradicted, preserves Unresolved   |
 +---------------------------------------------------------------------------------+
         |
         v
 +---------------------------------------------------------------------------------+
 |              Interactive Digital Forensics Workbench (React + Vite)             |
 |  [Overview] [Attack Graph] [Claim Inspector] [Evidence Explorer] [Sensors]      |
 |  [Scenario Runner] [Report & Export] [Investigation Manager]                    |
 +---------------------------------------------------------------------------------+
```

---

## 3. Quick Start (Windows Native)

### 3.1 Prerequisites
- Python 3.12+ or 3.14 (Verified working on Python 3.14.3 Windows)
- Node.js 18+ (Verified working on Node v24.14.1)

### 3.2 Backend Setup & Startup
Open PowerShell in the project directory:

```powershell
# 1. Navigate to truetrace project
cd C:\Users\HP\.gemini\antigravity\scratch\truetrace

# 2. Install backend dependencies
python -m pip install -r requirements.txt

# 3. Run automated tests to verify engine
python -m pytest tests -v

# 4. Start the backend API server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend API documentation is now live at: `http://127.0.0.1:8000/docs`

### 3.3 Frontend Setup & Startup
In a second terminal window:

```powershell
# 1. Navigate to frontend
cd C:\Users\HP\.gemini\antigravity\scratch\truetrace\frontend

# 2. Install dependencies (if not already cached)
npm install

# 3. Start Vite development server
npm run dev
```
Open your browser to: **`http://localhost:5173`**

---

## 4. Running the Automated Test Suite

TrueTrace includes 18 unit, integration, and evaluation tests:

```powershell
cd C:\Users\HP\.gemini\antigravity\scratch\truetrace
python -m pytest tests -v
```

**Results:**
- `test_parsers.py`: Validates PCAP, PCAPNG, and Host audit log parsers, SHA-256 hashes, and malformed JSON recovery.
- `test_engine.py`: Tests CIDR matching, sensor observability windows, packet loss flags, and invariant arbitration rules.
- `test_graph.py`: Validates candidate graph generation and refined graph transformation preserving unresolved claims.
- `test_evaluation_metrics.py`: Evaluates precision, recall, and confusion matrix across standard forensic test vectors (100% rule adherence).
- `test_api_endpoints.py`: Tests the full REST API lifecycle, scenarios, and report generation.

---

## 5. Controlled Scenarios & Benchmark Cases

The TrueTrace workbench includes 5 one-click reproducible scenarios:

1. **Case 1 — Fully Supported Exfiltration (APT34):**
   - Host log: `exfil_agent` reads `/etc/shadow` and connects to `198.51.100.4:443`.
   - Network evidence: Complete 3-way TCP handshake (SYN, SYN-ACK, ACK) and 1024 acknowledged payload bytes.
   - Verdict: **`SUPPORTED`** (`INV-TCP-01`, `INV-DATA-01`).
2. **Case 2 — Contradicted Connection Refusal (Closed Port):**
   - Host log: `powershell.exe` claims connection to `192.168.1.150:445`.
   - Network evidence: SYN packet followed immediately by TCP `RST/ACK` from closed port.
   - Verdict: **`CONTRADICTED`** (`INV-TCP-02`).
3. **Case 3 — Unresolved Sensor Visibility Gap (Edge Blindspot):**
   - Host log: Edge VPN connection to `172.16.50.2:8443`.
   - Network evidence: Sensor only monitored `192.168.1.0/24`. Zero packets seen for target.
   - Verdict: **`UNRESOLVED`** (`INV-OBS-01`). Absence of packets does not prove non-occurrence!
4. **Case 4 — Contradicted Data Transfer (write() Buffered, Wire Reset):**
   - Host log: `nc.exe` reports `write(8192 bytes)` succeeded.
   - Network evidence: Handshake established, but remote host sent `RST` before any payload segments entered the wire.
   - Verdict: **`CONTRADICTED`** (`INV-DATA-02`). Proves `write()` return code $\ne$ network delivery.
5. **Live Controlled TCP Socket Experiment:**
   - Starts a real Python socket server/client on localhost (`127.0.0.1`), executes actual OS socket calls, captures transport telemetry, and verifies via arbitration.

---

## 6. Docker Deployment (Optional)

A multi-container Docker Compose configuration is provided:

```bash
docker compose up --build
```
- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:3000`

---

## 7. Forensic Documentation & Specifications

Detailed research alignment and architectural documents are located in `docs/`:
- [`docs/RESEARCH_ALIGNMENT.md`](docs/RESEARCH_ALIGNMENT.md): Detailed mapping of the first-review presentation to implementation components.
- [`docs/VERIFICATION_ENGINE.md`](docs/VERIFICATION_ENGINE.md): Formal rules, invariants, assumptions, and edge cases.
- [`docs/EVALUATION.md`](docs/EVALUATION.md): Evaluation methodology, confusion matrix, and performance metrics.
- [`docs/TECHNICAL_CONTRIBUTION.md`](docs/TECHNICAL_CONTRIBUTION.md): Invention disclosure, mathematical formulation, and technical effects.
- [`docs/PRIOR_ART_TODO.md`](docs/PRIOR_ART_TODO.md): Patent search queries, classification codes, and literature comparison.

---

## 8. Acceptance Criteria Verification

- [x] Frontend starts and communicates with backend API.
- [x] Investigations can be created and persist in SQLite.
- [x] Evidence files parsed and traceable to source with SHA-256 digests.
- [x] Verification engine works independently of UI components.
- [x] All three verdicts (`SUPPORTED`, `CONTRADICTED`, `UNRESOLVED`) produced by formal rules.
- [x] Missing evidence does not automatically cause `CONTRADICTED` (observability check enforced).
- [x] At least three scenario tests exercise the actual engine.
- [x] Candidate and refined attack graphs generated from actual investigation data.
- [x] Attack graphs visually distinguish verdicts without relying on color alone.
- [x] Graph selections navigate to claims, rules, and source packets.
- [x] Refined graph preserves unresolved claims without silent deletion.
- [x] Inspectable reports generated in Markdown and JSON.
- [x] Full automated test suite passes (18/18 tests passing).
