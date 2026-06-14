import json
import re
from typing import Callable, Optional

import anthropic
import pandas as pd

_WRITE_OPS = re.compile(
    r"^\s*(insert|update|delete|drop|alter|truncate|create|replace|rename)\b",
    re.IGNORECASE,
)


def _is_safe_sql(sql: str) -> bool:
    stripped = re.sub(r"--[^\n]*", "", sql).strip()
    return not _WRITE_OPS.match(stripped)

client = anthropic.Anthropic()
MODEL = "claude-opus-4-8"


def build_system_prompt(schema: dict, db_label: str) -> str:
    schema_str = json.dumps(schema, indent=2)
    return f"""You are DataPulse, an intelligent data analyst assistant connected to {db_label}.

Database Schema:
{schema_str}

You help users explore and analyze their data by:
1. Writing and executing SQL queries to answer questions
2. Detecting anomalies and patterns in the data
3. Providing clear, actionable insights

Always explain what you're doing and interpret results in plain language.
When writing SQL, use the exact table and column names from the schema above."""


def build_tools(schema: dict) -> list:
    table_names = list(schema.keys()) if schema else []
    return [
        {
            "name": "query_database",
            "description": "Execute a SQL query against the database and return the results as a table.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to execute. Use exact table/column names from the schema.",
                    }
                },
                "required": ["sql"],
            },
        },
        {
            "name": "detect_anomalies",
            "description": "Analyze a table for anomalies, outliers, nulls, and data quality issues.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": f"Table name to analyze. Available: {', '.join(table_names)}",
                        "enum": table_names if table_names else ["__none__"],
                    },
                    "column": {
                        "type": "string",
                        "description": "Optional column name to focus on. If omitted, analyzes all columns.",
                    },
                },
                "required": ["table"],
            },
        },
    ]


def run_query_database(connector, sql: str) -> str:
    if not _is_safe_sql(sql):
        return "Blocked: only SELECT queries are permitted."
    try:
        results = connector.execute_query(sql)
        if not results:
            return "Query returned no results."
        df = pd.DataFrame(results)
        if len(df) > 100:
            return f"Query returned {len(df)} rows. Showing first 100:\n\n{df.head(100).to_markdown(index=False)}"
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Query error: {str(e)}"


def run_detect_anomalies(connector, table: str, column: Optional[str] = None) -> str:
    try:
        sql = f'SELECT * FROM "{table}" LIMIT 1000'
        results = connector.execute_query(sql)
        if not results:
            return f"No data found in table '{table}'."
        df = pd.DataFrame(results)
        report = [f"## Anomaly Report for `{table}`" + (f".`{column}`" if column else "")]
        report.append(f"**Rows analyzed:** {len(df)}")
        cols_to_check = [column] if column and column in df.columns else df.columns.tolist()
        for col in cols_to_check:
            col_report = [f"\n### Column: `{col}`"]
            series = df[col]
            null_count = int(series.isna().sum())
            null_pct = (null_count / len(series)) * 100
            col_report.append(f"- Nulls: {null_count} ({null_pct:.1f}%)")
            col_report.append(f"- Unique values: {series.nunique()}")
            if pd.api.types.is_numeric_dtype(series):
                non_null = series.dropna()
                if len(non_null) > 0:
                    q1 = non_null.quantile(0.25)
                    q3 = non_null.quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outliers = non_null[(non_null < lower) | (non_null > upper)]
                    col_report.append(f"- Range: [{non_null.min()}, {non_null.max()}]")
                    col_report.append(f"- Mean: {non_null.mean():.2f}, Std: {non_null.std():.2f}")
                    col_report.append(f"- Outliers (IQR method): {len(outliers)} values")
                    if 0 < len(outliers) <= 10:
                        col_report.append(f"  Outlier values: {sorted(outliers.tolist())}")
            else:
                value_counts = series.value_counts()
                if len(value_counts) <= 10:
                    col_report.append(f"- Values: {dict(value_counts)}")
                else:
                    col_report.append(f"- Top 5 values: {dict(value_counts.head())}")
            report.extend(col_report)
        return "\n".join(report)
    except Exception as e:
        return f"Anomaly detection error: {str(e)}"


def agent_turn(
    connector,
    schema: dict,
    db_label: str,
    user_message: str,
    on_tool_call: Optional[Callable] = None,
) -> str:
    system_prompt = build_system_prompt(schema, db_label)
    tools = build_tools(schema)
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        text_parts = []
        tool_uses = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn" or not tool_uses:
            return "\n".join(text_parts)

        tool_results = []
        for tool_use in tool_uses:
            tool_name = tool_use.name
            tool_input = tool_use.input
            if on_tool_call:
                on_tool_call(tool_name, tool_input)
            if tool_name == "query_database":
                result = run_query_database(connector, tool_input["sql"])
            elif tool_name == "detect_anomalies":
                result = run_detect_anomalies(
                    connector, tool_input["table"], tool_input.get("column")
                )
            else:
                result = f"Unknown tool: {tool_name}"
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                }
            )
        messages.append({"role": "user", "content": tool_results})
