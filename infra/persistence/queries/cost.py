QUERIES = {
    "insert_cost_record": """
        INSERT INTO cost_records (scenario, tier, input_tokens, output_tokens, cost_usd)
        VALUES (?, ?, ?, ?, ?)
    """,
    "select_cost_by_scenario": """
        SELECT * FROM cost_records 
        WHERE scenario = ? 
        ORDER BY timestamp DESC
    """,
    "select_cost_by_tier": """
        SELECT * FROM cost_records 
        WHERE tier = ? 
        ORDER BY timestamp DESC
    """,
    "select_cost_range": """
        SELECT * FROM cost_records 
        WHERE timestamp >= ? AND timestamp <= ? 
        ORDER BY timestamp ASC
    """,
    "sum_cost_by_scenario": """
        SELECT scenario, SUM(cost_usd) as total_cost
        FROM cost_records 
        WHERE timestamp >= ? 
        GROUP BY scenario
    """,
    "sum_cost_total": """
        SELECT SUM(cost_usd) as total_cost 
        FROM cost_records 
        WHERE timestamp >= ?
    """,
}