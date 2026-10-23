# TrueTrace Invariant Verification Engine: Specification & Formal Rules

## 1. Architectural Overview

The TrueTrace Verification Engine is an independent, deterministic inference system designed to resolve the fundamental forensic limitation of host-level provenance: **host audit logs record requests to the OS kernel, not physical transmission across the network**.

```
+-------------------------------------------------------------------------+
|                          TrueTrace Engine Pipeline                      |
+-------------------------------------------------------------------------+
                                      |
 1. Input Ingestion                   | Host Events & Network Packets
                                      v
 2. Claim Synthesis                  | Hypotheses (TCP Handshake, Data Exfil)
                                      v
 3. Observability Matrix Check        | Topologic CIDR & Temporal Bounds Check
                                      | [Is flow observable by any active sensor?]
                                      v
 4. Directional 5-Tuple Correlation   | [Match Forward & Reverse wire frames within tc ± Δt]
                                      v
 5. Formal Invariant Arbitration      | Evaluate Preconditions & Invariant Rules
                                      v
 6. Epistemic Verdict Assignment     | SUPPORTED | CONTRADICTED | UNRESOLVED
                                      v
 7. Graph Refinement                  | Annotate/Refine Causal Attack Graph
```

---

## 2. Epistemic Foundation & Preconditions

### 2.1 The Golden Invariant: Absence of Evidence $\neq$ Evidence of Absence
> **Axiom 1:** *A failure to find a matching packet in a network trace must NEVER automatically yield a `CONTRADICTED` verdict unless the communication flow has been proven to be 100% topologically and temporally observable by a lossless sensor.*

If a sensor did not monitor the subnet of the destination IP, or if the sensor was offline during the timestamp window, the ground truth is epistemically unknown. Falsifying a host claim based on an unmonitored link is scientifically invalid.

### 2.2 System Call Semantics vs. Network Reality
> **Axiom 2:** *A successful return code from an OS system call (`connect()`, `write()`, `send()`) only proves that data entered the kernel socket buffer. It does not prove that packets traversed the wire, that remote middleboxes permitted transit, or that the remote application received or processed the bytes.*

---

## 3. Sensor Observability Assessment

Given a candidate claim $C$ with flow $(s_{ip}, s_{port}, d_{ip}, d_{port}, proto)$ and timestamp $t_c$, and a set of registered sensors $\mathcal{S} = \{S_1, S_2, \dots, S_k\}$:

Each sensor $S_i$ is characterized by:
- $\text{CIDR}(S_i)$: Set of monitored IP subnets (e.g. `["192.168.1.0/24"]`).
- $[T_{start}(S_i), T_{end}(S_i)]$: Active packet capture interval.
- $\text{Loss}(S_i) \in \{\text{True}, \text{False}\}$: Hardware buffer ring drops or interface packet loss indicator.

### Observability Logic:
1. **Topological Match:** $S_i$ covers flow $C$ if:
   $$s_{ip} \in \text{CIDR}(S_i) \quad \lor \quad d_{ip} \in \text{CIDR}(S_i)$$
2. **Temporal Match:** $t_c \in [T_{start}(S_i), T_{end}(S_i)]$.
3. **Classification:**
   - If no sensor satisfies both (1) and (2) $\rightarrow$ **`UNOBSERVABLE`**.
   - If a covering sensor exists but $\text{Loss}(S_i) = \text{True}$ $\rightarrow$ **`DEGRADED_VISIBILITY`**.
   - If a covering sensor exists with $\text{Loss}(S_i) = \text{False}$ $\rightarrow$ **`FULLY_OBSERVABLE`**.

---

## 4. Directional 5-Tuple Flow Matching

For claim $C$, packets are correlated within a symmetric temporal tolerance window $\Delta t$ (default $\Delta t = 3.0$ seconds):
$$|t_{packet} - t_c| \le \Delta t$$

Directional flows:
- **Forward (Client $\rightarrow$ Server):** Packet matches $(s_{ip}, s_{port}, d_{ip}, d_{port})$. If host log did not record client ephemeral port, $s_{port}$ is treated as a wildcard.
- **Reverse (Server $\rightarrow$ Client):** Packet matches $(d_{ip}, d_{port}, s_{ip}, s_{port})$.

---

## 5. Formal Invariant Rules & Verdict Catalog

### Category A: Observability Preconditions
- **`INV-OBS-01: Insufficient Evidence (Zero Packets Captured)`**
  - **Precondition:** Zero packets matched within tolerance window $\Delta t$.
  - **Verdict:** **`UNRESOLVED`**.
  - **Rationale:** No packets observed; without active conflicting packets or inline block logs, non-occurrence cannot be asserted.
- **`INV-OBS-02: Sensor Visibility Gap (Unobservable Flow)`**
  - **Precondition:** Zero packets matched AND observability status is `UNOBSERVABLE`.
  - **Verdict:** **`UNRESOLVED`**.
  - **Rationale:** Flow falls outside registered sensor topology or time bounds.
- **`INV-OBS-03: Degraded Sensor Telemetry (Packet Loss Flagged)`**
  - **Precondition:** Zero packets matched AND sensor flagged buffer ring drops.
  - **Verdict:** **`UNRESOLVED`**.
  - **Rationale:** Packet drop by sensor hardware cannot be distinguished from non-occurrence.

---

### Category B: TCP Connection Establishment Invariants (`TCP_HANDSHAKE`)
- **`INV-TCP-01: Full Three-Way Handshake Invariant`**
  - **Precondition:** Client emitted `SYN`; Server emitted `SYN+ACK`; Client emitted handshake `ACK`.
  - **Verdict:** **`SUPPORTED`**.
  - **Rationale:** Both endpoints completed transport state synchronization. Connection was independently established.
- **`INV-TCP-02: Active Connection Refusal / RST Invariant`**
  - **Precondition:** Client emitted `SYN`; Server returned `RST` or `RST+ACK` (or ICMP Port Unreachable).
  - **Verdict:** **`CONTRADICTED`**.
  - **Rationale:** Remote port was closed or blocked. Host OS `connect()` returned or buffered, but the wire connection was rejected.
- **`INV-TCP-03: Incomplete Handshake Telemetry`**
  - **Precondition:** Client emitted `SYN`, but no `SYN+ACK` or `ACK` observed, and no `RST` observed.
  - **Verdict:** **`UNRESOLVED`**.
  - **Rationale:** Wire evidence is ambiguous or incomplete.

---

### Category C: Data Transfer & Exfiltration Invariants (`DATA_TRANSFER`)
- **`INV-DATA-01: Acknowledged Transport Payload Invariant`**
  - **Precondition:** Client data packets observed ($L_{payload} > 0$, `PSH+ACK`), AND Server returned TCP `ACK` acknowledging payload sequence space.
  - **Verdict:** **`SUPPORTED`**.
  - **Rationale:** Full transport delivery confirmed by bidirectional acknowledgements.
- **`INV-DATA-02: Premature Termination Prior to Payload`**
  - **Precondition:** Host logged `write(N bytes)`, but network capture reveals TCP `RST` tearing down socket before any data segments traversed wire.
  - **Verdict:** **`CONTRADICTED`**.
  - **Rationale:** Data remained trapped in local OS socket buffer; connection was aborted before transport transmission.
- **`INV-DATA-03: Zero Payload Transport Observed Under Full Observability`**
  - **Precondition:** Host logged `write(N bytes)`, full handshake observed, but connection closed with FIN/RST with 0 data payload bytes transferred.
  - **Verdict:** **`CONTRADICTED`**.
  - **Rationale:** No data segments traversed the monitored lossless link.
- **`INV-DATA-04: Unacknowledged Transport Segments`**
  - **Precondition:** Outbound payload seen on wire, but zero return ACKs captured from receiver.
  - **Verdict:** **`UNRESOLVED`**.
  - **Rationale:** Data left client NIC, but remote receipt cannot be confirmed.

---

## 6. Input / Output Concrete Examples

### Example 1: Contradicted Connection
**Input:**
- Host Event: `SOCKET_CONNECT to 192.168.1.150:445, ret=0, timestamp=1718000010.2`
- Candidate Claim: `claim-01: powershell.exe established TCP to 192.168.1.150:445`
- Network PCAP:
  - `t=1718000010.200: 192.168.1.105:50110 -> 192.168.1.150:445 [SYN]`
  - `t=1718000010.220: 192.168.1.150:445 -> 192.168.1.105:50110 [RST, ACK]`
- Sensor: `switch-span-02, Monitored: ["192.168.1.0/24"], Loss: False`

**Output:**
- **Verdict:** `CONTRADICTED`
- **Applied Rule:** `INV-TCP-02: Active Connection Refusal / RST Invariant`
- **Reasoning:** *"Host audit log claimed connection to 192.168.1.150:445 succeeded, but independent network capture recorded a TCP RST/ACK refusal from 192.168.1.150. The remote port was closed; no valid TCP session was established."*
- **Attack Graph Impact:** Edge marked dashed red with falsification badge. Narrative branch pruned from confirmed attack path.
