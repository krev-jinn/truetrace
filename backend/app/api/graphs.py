"""
TrueTrace Attack Graph Visualization API
Provides candidate and refined attack graphs formatted for interactive flow rendering (@xyflow/react).
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import json

from ..models import AttackGraph
from ..database import get_db_connection

router = APIRouter(prefix="/api/graphs", tags=["Graphs"])


def convert_to_xyflow(graph: AttackGraph) -> Dict[str, Any]:
    """
    Transforms backend domain graph into React Flow (@xyflow/react) layout nodes and edges.
    Calculates deterministic hierarchical positioning.
    """
    xy_nodes = []
    xy_edges = []

    # Simple layered layout based on node type
    type_layer = {
        "PROCESS": 0,
        "FILE": 1,
        "ENDPOINT": 2,
        "SOCKET": 2
    }

    # Group nodes by type
    layer_counters = {0: 0, 1: 0, 2: 0}

    for n in graph.nodes:
        layer = type_layer.get(n.node_type.value, 0)
        idx_in_layer = layer_counters[layer]
        layer_counters[layer] += 1

        # Calculate x, y
        x = 50 + (layer * 340)
        y = 50 + (idx_in_layer * 140)

        xy_nodes.append({
            "id": n.id,
            "type": "customNode",
            "position": {"x": x, "y": y},
            "data": {
                "id": n.id,
                "label": n.label,
                "nodeType": n.node_type.value,
                "properties": n.properties
            }
        })

    for e in graph.edges:
        verdict = e.verdict.value if e.verdict else ("PENDING" if e.is_network_dependent else "INTERNAL")
        
        # Edge styling based on verdict
        stroke_color = "#94a3b8"  # slate-400 default
        stroke_dash = None
        stroke_width = 2
        
        if verdict == "SUPPORTED":
            stroke_color = "#10b981"  # emerald-500
            stroke_width = 3
        elif verdict == "CONTRADICTED":
            stroke_color = "#ef4444"  # red-500
            stroke_dash = "5,5"
            stroke_width = 3
        elif verdict == "UNRESOLVED":
            stroke_color = "#f59e0b"  # amber-500
            stroke_dash = "3,3"
            stroke_width = 2

        # Form clear edge label indicating relationship and verdict
        if e.is_network_dependent and verdict and verdict not in ("PENDING", "INTERNAL"):
            edge_label = f"{e.relation} [{verdict}]"
        else:
            edge_label = e.relation

        xy_edges.append({
            "id": e.id,
            "source": e.source,
            "target": e.target,
            "type": "default",
            "label": edge_label,
            "labelStyle": {
                "fill": stroke_color,
                "fontWeight": 700,
                "fontSize": 11
            },
            "labelBgStyle": {
                "fill": "#0b1329",
                "fillOpacity": 0.9,
                "stroke": stroke_color,
                "strokeWidth": 1.5
            },
            "labelBgPadding": [6, 3],
            "labelBgBorderRadius": 4,
            "animated": verdict == "SUPPORTED",
            "data": {
                "id": e.id,
                "relation": e.relation,
                "isNetworkDependent": e.is_network_dependent,
                "claimId": e.claim_id,
                "verdict": verdict,
                "appliedRule": e.applied_rule,
                "reasoning": e.reasoning,
                "properties": e.properties
            },
            "style": {
                "stroke": stroke_color,
                "strokeWidth": stroke_width,
                "strokeDasharray": stroke_dash
            }
        })

    return {
        "graphType": graph.graph_type,
        "investigationId": graph.investigation_id,
        "nodes": xy_nodes,
        "edges": xy_edges,
        "metadata": graph.metadata
    }


@router.get("/{inv_id}/candidate")
def get_candidate_graph(inv_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT graph_data FROM attack_graphs WHERE investigation_id = ? AND graph_type = 'CANDIDATE'", (inv_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Candidate graph not found. Please upload host evidence first.")
    
    cand_graph = AttackGraph(**json.loads(row[0]))
    return convert_to_xyflow(cand_graph)


@router.get("/{inv_id}/refined")
def get_refined_graph(inv_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT graph_data FROM attack_graphs WHERE investigation_id = ? AND graph_type = 'REFINED'", (inv_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Refined graph not found. Please run claim arbitration first.")
    
    refined_graph = AttackGraph(**json.loads(row[0]))
    return convert_to_xyflow(refined_graph)
