# TrueTrace Technical Contribution & Forensic Innovation Specification

## 1. Title of the Technical Invention
**System and Method for Observability-Aware Arbitration of Host-Derived Attack Graphs using Network Invariant Verification**

---

## 2. Technical Field
The present innovation relates to digital forensics, cyberattack reconstruction, computer network monitoring, and causal provenance graph refinement. More specifically, it pertains to systems that evaluate host-observed network system calls against independently captured network transport evidence to eliminate causal over-approximation while strictly preserving forensic uncertainty.

---

## 3. Background & Shortcomings of Conventional Systems

Conventional attack reconstruction systems (e.g., SLEUTH, HOLMES, POIROT, ATLAS, NodLink) rely heavily on host OS audit logging (e.g. Linux auditd, Windows Event Logs/Sysmon). These systems represent system execution as a directed acyclic graph (provenance graph) where edges denote causal dependencies.

### Fundamental Flaw of Prior Systems:
1. **OS Boundary Limitation:** Host-level audit records capture system call invocations at the operating system boundary. A process calling `connect()` or `write()` receives an OS return code indicating local execution. In conventional systems, this event is directly transformed into an edge asserting that communication occurred.
2. **Ignorance of Transport Falsification:** In real network topologies, firewalls, stateful filters, middleboxes, routing failures, or target closed ports (`RST`) frequently terminate or discard packets before completion. Conventional provenance engines possess no mechanism to falsify a host-derived claim using network packet evidence.
3. **The "Absence Fallacy":** Naive attempts to correlate network packets fall into the trap of treating missing packets as proof that an event did not happen. In real enterprise environments, network sensors have limited placement, unmonitored VLANs, capture buffers, or transient drops. Concluding non-occurrence from an unmonitored network link produces catastrophic false negatives.

---

## 4. The Concrete Technical Mechanism

TrueTrace introduces a formalized, multi-stage arbitration engine operating as follows:

```
[ Host Audit Logs ] 
        |
        v (Extraction)
[ Candidate Causal Graph ] + [ Candidate Hypotheses (Claims C) ]
                                    |
[ Sensor Topology & Taps ] ---------> [ Stage 1: Observability Check ]
                                    |   - Subnet CIDR containment
                                    |   - Capture time window
                                    |   - Hardware loss flag
                                    v
[ Network Packet Capture ] ---------> [ Stage 2: Directional 5-Tuple Match ]
                                    |   - Client -> Server forward
                                    |   - Server -> Client reverse
                                    |   - Temporal correlation window (tc ± Δt)
                                    v
                                [ Stage 3: Invariant Arbitration ]
                                    |   - INV-TCP-01 (Handshake Triad)
                                    |   - INV-TCP-02 (RST Refusal)
                                    |   - INV-DATA-01 (Acknowledged Payload)
                                    |   - INV-DATA-02 (Buffered Socket Reset)
                                    |   - INV-OBS-01/02/03 (Visibility Bounds)
                                    v
                                [ Epistemic Verdict ]
                                    |-- SUPPORTED
                                    |-- CONTRADICTED
                                    |-- UNRESOLVED
                                    v
                                [ Stage 4: Uncertainty-Preserving Graph Refinement ]
```

### 4.1 Mathematical Formulation of Arbitration Operator $\mathcal{A}$
Let $C = (s_{ip}, s_{port}, d_{ip}, d_{port}, proto, t_c, \tau, \mathcal{K})$ be a candidate network claim, where $\mathcal{K} \in \{\text{TCP\_HANDSHAKE}, \text{DATA\_TRANSFER}\}$.  
Let $\mathcal{P}$ be the set of independently captured network packets.  
Let $\mathcal{S}$ be the set of registered sensors.

The arbitration operator $\mathcal{A}(C, \mathcal{P}, \mathcal{S}) \rightarrow (\mathcal{V}, \mathcal{R}, \mathcal{M})$ produces:
1. Verdict $\mathcal{V} \in \{\text{SUPPORTED}, \text{CONTRADICTED}, \text{UNRESOLVED}\}$.
2. Applied Invariant Rule $\mathcal{R}$.
3. Evidence Provenance & Justification $\mathcal{M}$.

### 4.2 Non-Destructive Attack Graph Refinement
Unlike graph pruning systems that irreversibly excise edges, TrueTrace refines candidate attack graph $G = (V, E)$ into $G' = (V, E')$:
- **Supported edges:** Retained and weighted with packet-level corroboration.
- **Contradicted edges:** Marked with explicit falsification metadata, allowing investigators to identify failed attack branches (e.g., failed exploits, blocked exfiltration attempts).
- **Unresolved edges:** Preserved with explicit visibility gap indicators (e.g. "Sensor blindspot: Subnet 172.16.50.0/24 unmonitored"). The investigator is alerted to expand sensor coverage rather than assuming safety.

---

## 5. Technical Effects & Measurable Advantages

1. **Elimination of Causal Over-Approximation:** Prevents false attribution of data exfiltration and lateral movement caused by host socket buffering.
2. **Epistemic Rigor:** Mathematically enforces that missing evidence is never equated with evidence of non-occurrence.
3. **Reproducibility & Provenance Integrity:** Every decision is cryptographically traceable to raw evidence SHA-256 digests, frame timestamps, and explicit invariant rules.
4. **Interactive Digital Forensics Workbench:** Enables forensic analysts to visually inspect candidate vs. refined graphs, drill into packet captures, and explore sensor coverage in real time.
