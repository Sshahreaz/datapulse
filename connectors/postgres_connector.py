from typing import Any, Dict, List

from .base import BaseConnector


class PostgreSQLConnector(BaseConnector):
    def connect(self) -> None:
        import psycopg2
        import psycopg2.extras

        self.connection = psycopg2.connect(
            host=self.config["host"],
            port=self.config.get("port", 5432),
            database=self.config["database"],
            user=self.config["user"],
            password=self.config["password"],
        )
        self._RealDictCursor = psycopg2.extras.RealDictCursor

    def get_schema(self) -> Dict[str, Any]:
        cursor = self.connection.cursor()
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

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor(cursor_factory=self._RealDictCursor)
        cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]

    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def test_connection(self) -> bool:
        try:
            self.connect()
            self.connection.cursor().execute("SELECT 1")
            return True
        except Exception:
            return False
