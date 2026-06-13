from typing import Any, Dict, List

from .base import BaseConnector


class MySQLConnector(BaseConnector):
    def connect(self) -> None:
        import mysql.connector

        self.connection = mysql.connector.connect(
            host=self.config["host"],
            port=self.config.get("port", 3306),
            database=self.config["database"],
            user=self.config["user"],
            password=self.config["password"],
        )

    def get_schema(self) -> Dict[str, Any]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            ORDER BY table_name, ordinal_position
            """
        )
        schema: Dict[str, Any] = {}
        for table, column, dtype in cursor.fetchall():
            schema.setdefault(table, {})[column] = dtype
        return schema

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(sql)
        return cursor.fetchall()

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
