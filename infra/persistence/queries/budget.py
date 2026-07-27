QUERIES = {
    "insert_budget": """
        INSERT INTO budgets (scope, usd, run_id)
        VALUES (?, ?, ?)
    """,
    "select_budget_by_scope": """
        SELECT * FROM budgets 
        WHERE scope = ? 
        ORDER BY set_at DESC
        LIMIT 1
    """,
    "select_budgets_by_scope": """
        SELECT * FROM budgets 
        WHERE scope = ? 
        ORDER BY set_at DESC
    """,
    "insert_budget_by_tier": """
        INSERT INTO budgets_by_tier (tier, usd)
        VALUES (?, ?)
    """,
    "select_budget_by_tier": """
        SELECT * FROM budgets_by_tier 
        WHERE tier = ? 
        ORDER BY set_at DESC
        LIMIT 1
    """,
}