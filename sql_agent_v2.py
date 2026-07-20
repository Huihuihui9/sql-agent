def validate_sql(sql: str):
    """Check if SQL is safe: only SELECT queries allowed. Returns (is_valid, message)."""
    sql_upper = sql.strip().upper()

    # 检查SELECT * 语句
    if "SELECT * FROM" in sql_upper:
        return False, "禁止使用SELECT *，请明确指定列名"

    # 检查是否以SELECT开头
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed"

    # 检查危险关键词
    for kw in FORBIDDEN_KEYWORDS:
        if re.search(r"\b" + kw + r"\b", sql_upper):
            return False, f"Operation {kw} is forbidden"

    return True, "OK"