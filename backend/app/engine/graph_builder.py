"""
TrueTrace Attack Graph Engine (Candidate & Refined Attack Graphs)
Uses NetworkX to construct the candidate causal graph from host events and refines it via arbitration results.
Never silently deletes unresolved claims; preserves uncertainty and full provenance traceability.
"""

from typing import List, Dict, Any, Tuple, Optional
import networkx as nx
from ..models import (
    HostEvent, HostEventType, NetworkClaim, ArbitrationResult,
    GraphNode, GraphEdge, AttackGraph, NodeType, Verdict
)


class AttackGraphBuilder:
    """Builds and refines causal attack graphs using formal NetworkX graphs."""

    def __init__(self, investigation_id: str):
        self.investigation_id = investigation_id
        self.nx_graph = nx.DiGraph()

    def build_candidate_graph(
        self,
        events: List[HostEvent],
        claims: List[NetworkClaim]
    ) -> AttackGraph:
        """
        Builds the initial candidate attack narrative directly from host-level provenance events.
        """
        self.nx_graph.clear()
        nodes_dict: Dict[str, GraphNode] = {}
        edges_list: List[GraphEdge] = []

        # Map claims by source_event_id
        claim_map = {c.source_event_id: c for c in claims}

        for evt in events:
            # 1. Process Nodes
            if evt.process_id is not None:
                p_id = f"proc-{evt.process_id}"
                p_label = f"{evt.process_name or 'Process'} (PID {evt.process_id})"
                if p_id not in nodes_dict:
                    nodes_dict[p_id] = GraphNode(
                        id=p_id,
                        label=p_label,
                        node_type=NodeType.PROCESS,
                        properties={
                            "pid": evt.process_id,
                            "name": evt.process_name,
                            "timestamp": evt.timestamp_iso
                        }
                    )
                    self.nx_graph.add_node(p_id, label=p_label, type="PROCESS")

            # 2. Parent-Child Process Spawning
            if evt.event_type == HostEventType.PROCESS_SPAWN and evt.parent_process_id is not None:
                parent_id = f"proc-{evt.parent_process_id}"
                child_id = f"proc-{evt.process_id}"
                if parent_id not in nodes_dict:
                    nodes_dict[parent_id] = GraphNode(
                        id=parent_id,
                        label=f"Parent (PID {evt.parent_process_id})",
                        node_type=NodeType.PROCESS,
                        properties={"pid": evt.parent_process_id}
                    )
                    self.nx_graph.add_node(parent_id, label=f"PID {evt.parent_process_id}", type="PROCESS")

                edge_id = f"edge-{parent_id}-spawns-{child_id}"
                edge = GraphEdge(
                    id=edge_id,
                    source=parent_id,
                    target=child_id,
                    relation="SPAWNED",
                    is_network_dependent=False,
                    properties={"timestamp": evt.timestamp_iso}
                )
                edges_list.append(edge)
                self.nx_graph.add_edge(parent_id, child_id, id=edge_id, relation="SPAWNED")

            # 3. File Operations
            if evt.file_path and evt.event_type in (HostEventType.FILE_READ, HostEventType.FILE_WRITE):
                file_node_id = f"file-{abs(hash(evt.file_path)) % 100000}"
                if file_node_id not in nodes_dict:
                    nodes_dict[file_node_id] = GraphNode(
                        id=file_node_id,
                        label=evt.file_path.split("/")[-1].split("\\")[-1] or evt.file_path,
                        node_type=NodeType.FILE,
                        properties={"path": evt.file_path}
                    )
                    self.nx_graph.add_node(file_node_id, label=nodes_dict[file_node_id].label, type="FILE")

                proc_node_id = f"proc-{evt.process_id}" if evt.process_id else None
                if proc_node_id:
                    relation = "READ" if evt.event_type == HostEventType.FILE_READ else "WROTE"
                    edge_id = f"edge-{proc_node_id}-{relation.lower()}-{file_node_id}"
                    src = proc_node_id if relation == "WROTE" else file_node_id
                    dst = file_node_id if relation == "WROTE" else proc_node_id
                    edge = GraphEdge(
                        id=edge_id,
                        source=src,
                        target=dst,
                        relation=relation,
                        is_network_dependent=False,
                        properties={"timestamp": evt.timestamp_iso}
                    )
                    edges_list.append(edge)
                    self.nx_graph.add_edge(src, dst, id=edge_id, relation=relation)

            # 4. Network Connections / Exfiltration Claims
            if evt.id in claim_map:
                claim = claim_map[evt.id]
                ep_id = f"endpoint-{claim.dst_ip}:{claim.dst_port}"
                ep_label = f"{claim.dst_ip}:{claim.dst_port}"
                if ep_id not in nodes_dict:
                    nodes_dict[ep_id] = GraphNode(
                        id=ep_id,
                        label=ep_label,
                        node_type=NodeType.ENDPOINT,
                        properties={
                            "ip": claim.dst_ip,
                            "port": claim.dst_port,
                            "protocol": claim.protocol
                        }
                    )
                    self.nx_graph.add_node(ep_id, label=ep_label, type="ENDPOINT")

                proc_node_id = f"proc-{evt.process_id}" if evt.process_id else "proc-unknown"
                if proc_node_id not in nodes_dict:
                    nodes_dict[proc_node_id] = GraphNode(
                        id=proc_node_id,
                        label=f"Process (PID {evt.process_id or '?'})",
                        node_type=NodeType.PROCESS,
                        properties={"pid": evt.process_id}
                    )
                    self.nx_graph.add_node(proc_node_id, label=proc_node_id, type="PROCESS")

                relation = "EXFILTRATES_TO" if claim.claim_type.value == "DATA_TRANSFER" else "CONNECTS_TO"
                edge_id = f"edge-{proc_node_id}-{relation.lower()}-{ep_id}"
                claim.candidate_edge_id = edge_id

                edge = GraphEdge(
                    id=edge_id,
                    source=proc_node_id,
                    target=ep_id,
                    relation=relation,
                    is_network_dependent=True,
                    claim_id=claim.id,
                    verdict=None,  # Candidate state has no arbitration verdict yet
                    reasoning="Candidate hypothesis derived from host audit logs; awaiting network arbitration.",
                    properties={
                        "timestamp": claim.timestamp_iso,
                        "dst_ip": claim.dst_ip,
                        "dst_port": claim.dst_port,
                        "claimed_bytes": claim.claimed_bytes,
                        "claim_type": claim.claim_type.value
                    }
                )
                edges_list.append(edge)
                self.nx_graph.add_edge(proc_node_id, ep_id, id=edge_id, relation=relation)

        return AttackGraph(
            investigation_id=self.investigation_id,
            graph_type="CANDIDATE",
            nodes=list(nodes_dict.values()),
            edges=edges_list,
            metadata={
                "node_count": len(nodes_dict),
                "edge_count": len(edges_list),
                "network_dependent_edges": sum(1 for e in edges_list if e.is_network_dependent)
            }
        )

    def build_refined_graph(
        self,
        candidate_graph: AttackGraph,
        arbitration_results: List[ArbitrationResult]
    ) -> AttackGraph:
        """
        Refines the candidate graph by annotating each network-dependent edge with its arbitration verdict.
        Contradicted edges are marked with falsification evidence.
        Unresolved edges are preserved with explicit uncertainty tags (never deleted).
        """
        arb_map = {res.claim_id: res for res in arbitration_results}
        refined_edges: List[GraphEdge] = []

        verdict_counts = {
            "SUPPORTED": 0,
            "CONTRADICTED": 0,
            "UNRESOLVED": 0
        }

        for edge in candidate_graph.edges:
            if not edge.is_network_dependent or not edge.claim_id:
                # Retain non-network edges (process spawning, file read/write)
                refined_edges.append(edge)
                continue

            arb = arb_map.get(edge.claim_id)
            if arb:
                verdict_counts[arb.verdict.value] += 1
                refined_edge = GraphEdge(
                    id=edge.id,
                    source=edge.source,
                    target=edge.target,
                    relation=edge.relation,
                    is_network_dependent=True,
                    claim_id=edge.claim_id,
                    verdict=arb.verdict,
                    applied_rule=arb.applied_rule,
                    reasoning=arb.reasoning,
                    properties={
                        **edge.properties,
                        "verdict": arb.verdict.value,
                        "applied_rule": arb.applied_rule,
                        "observability_status": arb.observability_status.value,
                        "observability_reasoning": arb.observability_reasoning,
                        "epistemic_notes": arb.epistemic_notes,
                        "matching_packet_count": len(arb.matching_packet_ids),
                        "timestamp_delta": arb.timestamp_delta
                    }
                )
                refined_edges.append(refined_edge)
            else:
                # Claim not arbitrated yet: retain as UNRESOLVED
                refined_edge = GraphEdge(
                    id=edge.id,
                    source=edge.source,
                    target=edge.target,
                    relation=edge.relation,
                    is_network_dependent=True,
                    claim_id=edge.claim_id,
                    verdict=Verdict.UNRESOLVED,
                    applied_rule="INV-OBS-00: Unarbitrated Claim",
                    reasoning="Claim has not undergone arbitration.",
                    properties={**edge.properties, "verdict": "UNRESOLVED"}
                )
                refined_edges.append(refined_edge)
                verdict_counts["UNRESOLVED"] += 1

        return AttackGraph(
            investigation_id=self.investigation_id,
            graph_type="REFINED",
            nodes=candidate_graph.nodes,
            edges=refined_edges,
            metadata={
                "node_count": len(candidate_graph.nodes),
                "edge_count": len(refined_edges),
                "verdict_summary": verdict_counts
            }
        )
