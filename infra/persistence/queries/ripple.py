QUERIES = {
    "select_nodes_by_volume": """
        SELECT * FROM reference_nodes 
        WHERE volume = ? 
        ORDER BY chapter ASC
    """,
    "select_nodes_by_dimension": """
        SELECT * FROM reference_nodes 
        WHERE dimension = ? 
        ORDER BY volume ASC, chapter ASC
    """,
    "select_node_by_id": """
        SELECT * FROM reference_nodes 
        WHERE id = ?
    """,
    "insert_node": """
        INSERT INTO reference_nodes (id, dimension, volume, chapter, title, description, payload, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    "update_node": """
        UPDATE reference_nodes 
        SET title = ?, description = ?, payload = ?
        WHERE id = ?
    """,
    "delete_node": """
        DELETE FROM reference_nodes WHERE id = ?
    """,
    "select_edges_by_from": """
        SELECT * FROM reference_edges 
        WHERE from_node_id = ?
    """,
    "select_edges_by_to": """
        SELECT * FROM reference_edges 
        WHERE to_node_id = ?
    """,
    "insert_edge": """
        INSERT INTO reference_edges (id, from_node_id, to_node_id, relationship_type, weight, payload, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    "select_ripples": """
        SELECT * FROM reference_ripples 
        ORDER BY created_at DESC
    """,
    "select_ripple_by_id": """
        SELECT * FROM reference_ripples 
        WHERE id = ?
    """,
    "insert_ripple": """
        INSERT INTO reference_ripples (id, trigger_volume, trigger_chapter, affected_nodes, affected_edges, proposed_actions, status, created_at, payload, parent_ripple_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    "update_ripple_status": """
        UPDATE reference_ripples 
        SET status = ?, confirmed_at = ?, applied_at = ?
        WHERE id = ?
    """,
    "select_audit_by_ripple": """
        SELECT * FROM ripple_audit 
        WHERE ripple_id = ? 
        ORDER BY created_at DESC
    """,
    "insert_audit": """
        INSERT INTO ripple_audit (ripple_id, action, prev_status, new_status, actor, origin, reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
}