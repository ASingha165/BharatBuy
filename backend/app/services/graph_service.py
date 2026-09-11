import json
import os
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.responses import RelatedStandardItem, ReactFlowNode, ReactFlowEdge, GraphNodeData

class GraphService:
    def __init__(self, graph_path: Optional[str] = None):
        self.graph_path = graph_path or settings.GRAPH_PATH
        if not os.path.isabs(self.graph_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.graph_path = os.path.join(base_dir, self.graph_path)
            
        self.nodes_map: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.load_graph()

    def load_graph(self):
        try:
            if os.path.exists(self.graph_path):
                with open(self.graph_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    nodes = data.get("nodes", [])
                    self.nodes_map = {n["id"]: n for n in nodes}
                    self.edges = data.get("edges", [])
                logger.info(f"Loaded Knowledge Graph with {len(self.nodes_map)} nodes and {len(self.edges)} edges.")
            else:
                logger.warning(f"Graph path '{self.graph_path}' does not exist.")
        except Exception as e:
            logger.error(f"Failed to load Knowledge Graph JSON: {e}")

    def get_related_standards(self, standard_id: str) -> List[RelatedStandardItem]:
        related = []
        # Find edges where standard_id is source or target
        for edge in self.edges:
            rel_type = edge.get("relation", "RELATED")
            desc = edge.get("description", "")
            
            if edge["source"] == standard_id:
                target_id = edge["target"]
                target_node = self.nodes_map.get(target_id)
                related.append(RelatedStandardItem(
                    standard_id=target_id,
                    is_code=target_node.get("is_code", target_id) if target_node else target_id,
                    relationship_type=rel_type,
                    title=target_node.get("title", "") if target_node else "",
                    description=desc
                ))
            elif edge["target"] == standard_id:
                source_id = edge["source"]
                source_node = self.nodes_map.get(source_id)
                related.append(RelatedStandardItem(
                    standard_id=source_id,
                    is_code=source_node.get("is_code", source_id) if source_node else source_id,
                    relationship_type=f"INVERSE_{rel_type}",
                    title=source_node.get("title", "") if source_node else "",
                    description=desc
                ))
        return related

    def get_react_flow_graph(self, standard_id: str) -> Dict[str, Any]:
        center_node = self.nodes_map.get(standard_id)
        
        # Build node set for standard + direct neighbors
        neighbor_ids = set()
        neighbor_edges = []
        
        for edge in self.edges:
            if edge["source"] == standard_id or edge["target"] == standard_id:
                neighbor_ids.add(edge["source"])
                neighbor_ids.add(edge["target"])
                neighbor_edges.append(edge)
                
        if not neighbor_ids and center_node:
            neighbor_ids.add(standard_id)

        nodes_res: List[ReactFlowNode] = []
        edges_res: List[ReactFlowEdge] = []
        
        # Center node position
        center_x, center_y = 350.0, 200.0
        
        # Position connected nodes radially
        import math
        connected_list = list(neighbor_ids - {standard_id})
        num_neighbors = len(connected_list)
        radius = 220.0
        
        # Add center node
        if center_node or standard_id in neighbor_ids:
            nodes_res.append(ReactFlowNode(
                id=standard_id,
                data=GraphNodeData(
                    label=center_node.get("is_code", standard_id) if center_node else standard_id,
                    title=center_node.get("title", "") if center_node else standard_id,
                    department=center_node.get("department", "Engineering") if center_node else "",
                    type="MAIN"
                ),
                position={"x": center_x, "y": center_y},
                type="input"
            ))

        for idx, n_id in enumerate(connected_list):
            node_data = self.nodes_map.get(n_id, {})
            angle = (2 * math.pi * idx) / max(num_neighbors, 1)
            x_pos = center_x + radius * math.cos(angle)
            y_pos = center_y + radius * math.sin(angle)
            
            nodes_res.append(ReactFlowNode(
                id=n_id,
                data=GraphNodeData(
                    label=node_data.get("is_code", n_id),
                    title=node_data.get("title", ""),
                    department=node_data.get("department", "Engineering"),
                    type="RELATED"
                ),
                position={"x": round(x_pos, 1), "y": round(y_pos, 1)},
                type="output"
            ))

        for idx, edge in enumerate(neighbor_edges):
            edges_res.append(ReactFlowEdge(
                id=f"e_{edge['source']}_{edge['target']}_{idx}",
                source=edge["source"],
                target=edge["target"],
                label=edge.get("relation", "RELATED"),
                animated=True,
                style={"stroke": "#3b82f6", "strokeWidth": 2}
            ))

        return {
            "center_standard_id": standard_id,
            "nodes": [n.model_dump() for n in nodes_res],
            "edges": [e.model_dump() for e in edges_res]
        }
