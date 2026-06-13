import sqlite3
from .base import BaseConnector

class SQLiteConnector(BaseConnector):

    def connect(self) -> bool:
        path = self.config.get("path")
        if not path:
            raise ValueError("SQLite config requires 'path'")
        conn = sqlite3.connect(path)
        conn.close()
        return True

    def _get_connection(self):
        path = self.config.get("path")
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def get_schema(self) -> dict:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")
            tables = [row[0] for row in cur.fetchall()]
            schema = {}
            for table in tables:
                cur.execute(f"PRAGMA table_info({table})")
                schema[table] = [row[1] for row in cur.fetchall()]
            return schema
        finally:
            conn.close()

    def execute_query(self, sql: str) -> list[dict]:
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
