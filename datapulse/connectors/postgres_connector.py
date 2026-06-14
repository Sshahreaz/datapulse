from typing import Any, Dict, List

from .base import BaseConnector


class PostgreSQLConnector(BaseConnector):
    def _get_connection(self):
        import psycopg2
        import psycopg2.extras

        conn = psycopg2.connect(
            host=self.config["host"],
            port=self.config.get("port", 5432),
            database=self.config["database"],
            user=self.config["user"],
            password=self.config["password"],
        )
        return conn, psycopg2.extras.RealDictCursor

    def connect(self) -> None:
        conn, _ = self._get_connection()
        conn.close()

    def get_schema(self) -> Dict[str, Any]:
        conn, _ = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
                """
            )
            schema: Dict[str, Any] = {}
            for table, column, dtype in cursor.fetchall():
                schema.setdefault(table, {})[column] = dtype
            return schema
        finally:
            conn.close()

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        conn, RealDictCursor = self._get_connection()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
