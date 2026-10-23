# TrueTrace Prior Art Investigation & Search Guide

## 1. Core Novelty Hypothesis to Search

The candidate novel mechanism in TrueTrace is:
> *A computerized system that evaluates host-derived provenance causal attack claims as hypotheses against independent packet captures by executing an observability-aware arbitration check (verifying subnet CIDR topology, capture time boundaries, and hardware loss flags) and applying transport-layer invariants (e.g. handshake completion, connection refusal RST, acknowledged payload bytes) to assign three-valued verdicts (`SUPPORTED`, `CONTRADICTED`, `UNRESOLVED`) and refine a candidate attack graph without deleting unresolved claims.*

---

## 2. Relevant Patent Classification Codes (IPC / CPC)

- **G06F 21/55:** Detecting local intrusions or malicious activities on computers.
- **G06F 21/56:** Malware detection and attack graph modeling.
- **H04L 9/40:** Network security; cryptographic mechanisms; intrusion detection and incident reconstruction.
- **H04L 41/06:** Network fault management, invariant checking, packet trace arbitration.
- **H04L 43/028:** Network monitoring; packet capture filtering and flow extraction.

---

## 3. Prior-Art Queries (Google Patents, USPTO, EPO, IEEE Xplore)

### Query Set 1: Provenance Graph & Network Arbitration
```
("provenance graph" OR "attack graph" OR "causal graph") 
AND ("packet capture" OR "PCAP" OR "network flow" OR "transport layer") 
AND ("arbitrat*" OR "falsif*" OR "contradict*" OR "inconsistent")
```

### Query Set 2: Observability & Invariant Verification
```
("sensor observability" OR "visibility gap" OR "sensor coverage") 
AND ("network invariant" OR "transport invariant" OR "TCP handshake") 
AND ("audit log" OR "provenance" OR "Sysmon" OR "auditd")
```

### Query Set 3: Three-Valued Epistemic Verdicts in Digital Forensics
```
("three-valued" OR "ternary logic" OR "supported" OR "contradicted" OR "unresolved") 
AND ("attack reconstruction" OR "digital forensics" OR "incident response") 
AND ("absence of evidence" OR "negative evidence")
```

---

## 4. Prior-Art Systems Comparison Points

| Prior System | Literature Source | Comparison Point for TrueTrace Patent Claims |
| :--- | :--- | :--- |
| **SLEUTH** | USENIX Security 2016 | Uses tag-based causality tracking on host audit logs; treats network as external tags, never falsifies a host claim via packet evidence. |
| **HOLMES** | IEEE S&P 2019 | Maps provenance graphs to high-level attack steps (MITRE ATT&CK); lacks network transport invariant arbitration. |
| **Anteater / Batfish** | ACM SIGCOMM / NSDI | Verifies static network invariants and forwarding policies from router configurations; does not arbitrate dynamic host execution provenance. |
| **LogGC / WATSON** | USENIX ATC / ACM CCS | Prunes host provenance graphs based on frequency/information flow; does not incorporate independent network ground truth. |
| **ProTracer / RAIN** | NDSS 2016 / IEEE S&P 2017 | Bintrace kernel module for system call attribution; strictly host-resident. |

---

## 5. Concrete Action Items for Patent Counsel

1. **Verify Claim Scope:** Ensure claims emphasize the *observability-aware arbitration mechanism* (checking sensor topology before rendering negative verdicts) rather than generic log correlation.
2. **Review Defensive Publications:** Determine whether any DARPA TC participant published packet-host arbitration techniques between 2016 and 2026.
3. **Examine Edge Cases:** File dependent claims covering:
   - Dynamic ephemeral port wildcard matching.
   - Sensor packet drop ring buffer compensation (`DEGRADED_VISIBILITY`).
   - Uncertainty-preserving attack graph visualization.
