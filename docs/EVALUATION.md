# TrueTrace Research Evaluation & Scientific Verification

## 1. Evaluation Methodology

The TrueTrace verification framework is evaluated against a structured test corpus and reproducible controlled scenarios designed to address the research questions:
- **RQ1:** Can network and transport ground truth detect and falsify over-approximated host provenance claims?
- **RQ2:** Does the observability check prevent fallacious negative inferences (i.e. treating absence of packets as non-occurrence)?
- **RQ3:** Does graph refinement preserve uncertainty without silently dropping unresolved narrative branches?

The evaluation harnesses three tiers of empirical verification:
1. **Automated Unit & Integration Test Suite (`tests/`):** 18 deterministic pytest suites covering parsers, observability checks, arbitration rules, graph construction, live TCP sockets, and REST endpoints.
2. **Standard Labelled Benchmark Corpus (`test_evaluation_metrics.py`):** 8 diverse forensic test vectors with ground-truth labels.
3. **Reproducible Controlled Scenarios (`scenarios/`):** Full end-to-end attack scenarios including APT34 exfiltration, lateral movement port refusal, Mandiant edge device blindspots, and live Windows socket executions.

---

## 2. Empirical Results & Confusion Matrix

### 2.1 Labelled Benchmark Corpus Evaluation

Across the 8 labelled test vectors in `test_evaluation_metrics.py`:

| Test Vector ID | Description | Ground-Truth Label | Engine Verdict | Applied Rule | Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TV-01** | Full Handshake Established | `SUPPORTED` | `SUPPORTED` | `INV-TCP-01` | **MATCH** |
| **TV-02** | Connection Refusal via RST | `CONTRADICTED` | `CONTRADICTED` | `INV-TCP-02` | **MATCH** |
| **TV-03** | Sensor Blindspot (Unobservable) | `UNRESOLVED` | `UNRESOLVED` | `INV-OBS-01` | **MATCH** |
| **TV-04** | Lossy Buffer Ring Degradation | `UNRESOLVED` | `UNRESOLVED` | `INV-OBS-03` | **MATCH** |
| **TV-05** | Out-of-Window Packet Drift | `UNRESOLVED` | `UNRESOLVED` | `INV-OBS-01` | **MATCH** |
| **TV-06** | Data Payload Acknowledged | `SUPPORTED` | `SUPPORTED` | `INV-DATA-01` | **MATCH** |
| **TV-07** | `write()` Buffered, Socket Reset | `CONTRADICTED` | `CONTRADICTED` | `INV-DATA-02` | **MATCH** |
| **TV-08** | Incomplete Handshake (SYN Only) | `UNRESOLVED` | `UNRESOLVED` | `INV-TCP-03` | **MATCH** |

### 2.2 Confusion Matrix

| Actual \ Predicted | `SUPPORTED` | `CONTRADICTED` | `UNRESOLVED` | Total Actual |
| :--- | :---: | :---: | :---: | :---: |
| **`SUPPORTED`** | **2** | 0 | 0 | 2 |
| **`CONTRADICTED`** | 0 | **2** | 0 | 2 |
| **`UNRESOLVED`** | 0 | 0 | **4** | 4 |
| **Total Predicted** | 2 | 2 | 4 | 8 |

### 2.3 Statistical Performance Metrics
- **Overall Accuracy:** $1.00$ ($100\%$)
- **Per-Class Precision:**
  - `SUPPORTED`: $\frac{2}{2} = 1.00$ ($100\%$)
  - `CONTRADICTED`: $\frac{2}{2} = 1.00$ ($100\%$)
  - `UNRESOLVED`: $\frac{4}{4} = 1.00$ ($100\%$)
- **Per-Class Recall:**
  - `SUPPORTED`: $\frac{2}{2} = 1.00$ ($100\%$)
  - `CONTRADICTED`: $\frac{2}{2} = 1.00$ ($100\%$)
  - `UNRESOLVED`: $\frac{4}{4} = 1.00$ ($100\%$)
- **F1 Score:** $1.00$ across all three verdict classes.

> **Scientific Disclosure:** While metrics on this 8-vector benchmark achieve 100% precision and recall, this reflects mathematical fidelity to the defined invariant rules. In real-world enterprise captures, asymmetric routing, NAT translation, and TLS encapsulation introduce ambiguities evaluated under `UNRESOLVED`.

---

## 3. Automated Test Execution Record

Execution of the full automated test suite on Windows 11 with Python 3.14.3:

```powershell
python -m pytest tests -v
```

**Test Output:**
```
tests/test_api_endpoints.py::test_health_check PASSED                    [  5%]
tests/test_api_endpoints.py::test_investigation_lifecycle PASSED         [ 11%]
tests/test_api_endpoints.py::test_scenario_execution_case_1_supported PASSED [ 16%]
tests/test_api_endpoints.py::test_scenario_execution_case_2_contradicted PASSED [ 22%]
tests/test_api_endpoints.py::test_scenario_execution_case_3_unresolved PASSED [ 27%]
tests/test_api_endpoints.py::test_live_tcp_experiment PASSED             [ 33%]
tests/test_engine.py::test_ip_in_network PASSED                          [ 38%]
tests/test_engine.py::test_sensor_observability_coverage PASSED          [ 44%]
tests/test_engine.py::test_arbitration_case_1_supported PASSED           [ 50%]
tests/test_engine.py::test_arbitration_case_2_contradicted_rst PASSED    [ 55%]
tests/test_engine.py::test_arbitration_case_3_unresolved_observability_gap PASSED [ 61%]
tests/test_engine.py::test_arbitration_case_4_data_transfer_reset PASSED [ 66%]
tests/test_evaluation_metrics.py::test_evaluation_corpus_accuracy_and_metrics PASSED [ 72%]
tests/test_graph.py::test_candidate_graph_construction PASSED            [ 77%]
tests/test_graph.py::test_refined_graph_preserves_unresolved_and_marks_contradicted PASSED [ 83%]
tests/test_parsers.py::test_pcap_parser PASSED                           [ 88%]
tests/test_parsers.py::test_host_log_parser PASSED                       [ 94%]
tests/test_parsers.py::test_malformed_host_log_handling PASSED           [100%]

======================== 18 passed, 1 warning in 3.48s ========================
```

---

## 4. Controlled Scenarios Evaluation

| Scenario | Mode | Ingested Evidence | Outcome & Graph Refinement |
| :--- | :--- | :--- | :--- |
| **Case 1: Supported** | DARPA TC Style | Host JSON + 5-packet PCAP | Edge marked **SUPPORTED**; 3-way handshake verified; payload acknowledged. |
| **Case 2: Contradicted** | Port Refusal | Host JSON + 2-packet PCAP | Edge marked **CONTRADICTED**; RST refusal recorded; attack branch pruned. |
| **Case 3: Unresolved** | Edge Blindspot | Host JSON + unmonitored PCAP | Edge preserved as **UNRESOLVED**; sensor visibility gap clearly explained. |
| **Case 4: Buffered Reset** | Data Transfer | Host JSON + reset PCAP | Edge marked **CONTRADICTED**; proves local `write()` $\ne$ wire delivery. |
| **Live TCP Experiment** | Real OS Socket | Loopback socket client/server | Full live execution on Windows; genuine OS socket metrics verified. |

---

## 5. Limitations & Future Work

1. **IPv6 Support:** Current flow matching logic prioritizes IPv4 5-tuples. Extension to IPv6 / dual-stack flows is planned for v1.1.
2. **Encrypted Transport (TLS):** While TCP handshake and data volume invariants are verified regardless of payload encryption, application-level semantic claims (e.g. specific HTTP endpoints) within TLS tunnels require JA3/JA4 fingerprinting or session key injection.
3. **NAT / Middlebox Rewriting:** Dynamic NAT rewrites ephemeral source ports. In TrueTrace, wildcard port matching mitigates client-side NAT, but multi-tier enterprise NAT traversal requires stateful topology mapping.
