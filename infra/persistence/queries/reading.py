QUERIES = {
    "insert_hook": """
        INSERT INTO hooks (chapter, hook_type, strength, position, content)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(chapter, hook_type, position) DO UPDATE SET
            strength = excluded.strength,
            content = excluded.content
    """,
    "select_hooks_by_chapter": """
        SELECT * FROM hooks 
        WHERE chapter = ? 
        ORDER BY position ASC
    """,
    "select_hooks_by_type": """
        SELECT * FROM hooks 
        WHERE hook_type = ? 
        ORDER BY chapter ASC, position ASC
    """,
    "insert_coolpoint": """
        INSERT INTO coolpoints (chapter, pattern, density, combo_with, content)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(chapter, pattern) DO UPDATE SET
            density = excluded.density,
            combo_with = excluded.combo_with,
            content = excluded.content
    """,
    "select_coolpoints_by_chapter": """
        SELECT * FROM coolpoints 
        WHERE chapter = ? 
        ORDER BY pattern ASC
    """,
    "upsert_chapter_summary": """
        INSERT INTO chapter_summary (chapter, hook_count, hook_strength_avg, coolpoint_count, coolpoint_density, reading_power_score, last_analyzed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(chapter) DO UPDATE SET
            hook_count = excluded.hook_count,
            hook_strength_avg = excluded.hook_strength_avg,
            coolpoint_count = excluded.coolpoint_count,
            coolpoint_density = excluded.coolpoint_density,
            reading_power_score = excluded.reading_power_score,
            last_analyzed_at = excluded.last_analyzed_at,
            updated_at = CURRENT_TIMESTAMP
    """,
    "select_chapter_summary": """
        SELECT * FROM chapter_summary 
        WHERE chapter = ?
    """,
    "select_all_chapter_summaries": """
        SELECT * FROM chapter_summary 
        ORDER BY chapter ASC
    """,
    "insert_analysis_log": """
        INSERT INTO analysis_log (chapter, analyzer_type, input_tokens, output_tokens, duration_ms, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
}