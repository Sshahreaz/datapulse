import sqlite3
from typing import Any, Dict, List

import pandas as pd

from .base import BaseConnector


class CSVConnector(BaseConnector):
    def connect(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        for file_cfg in self.config.get("files", []):
            path = file_cfg["path"]
            table = file_cfg["table"]
            if path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(path)
            else:
                df = pd.read_csv(path)
            df.to_sql(table, self.connection, if_exists="replace", index=False)

    def get_schema(self) -> Dict[str, Any]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        schema = {}
        for table in tables:
            cursor.execute(f'PRAGMA table_info("{table}")')
            cols = cursor.fetchall()
            schema[table] = {col["name"]: col["type"] for col in cols}
        return schema

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def test_connection(self) -> bool:
        try:
            self.connect()
            return True
        except Exception:
            return False
