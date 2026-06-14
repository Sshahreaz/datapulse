import sqlite3
from typing import Any, Dict, List

import pandas as pd

from .base import BaseConnector


class CSVConnector(BaseConnector):
    def connect(self) -> None:
        self._dataframes: Dict[str, pd.DataFrame] = {}
        for file_cfg in self.config.get("files", []):
            path = file_cfg["path"]
            table = file_cfg["table"]
            if path.endswith((".xlsx", ".xls")):
                df = pd.read_excel(path)
            else:
                try:
                    df = pd.read_csv(path, encoding="utf-8")
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(path, encoding="latin-1")
                    except UnicodeDecodeError:
                        df = pd.read_csv(path, encoding="cp1252")
            self._dataframes[table] = df

    def _fresh_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        for table, df in self._dataframes.items():
            df.to_sql(table, conn, if_exists="replace", index=False)
        return conn

    def get_schema(self) -> Dict[str, Any]:
        schema = {}
        for table, df in self._dataframes.items():
            schema[table] = {col: str(dtype) for col, dtype in df.dtypes.items()}
        return schema

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        conn = self._fresh_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def disconnect(self) -> None:
        self._dataframes = {}
