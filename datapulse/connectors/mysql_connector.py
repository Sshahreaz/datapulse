from typing import Any, Dict, List

from .base import BaseConnector


class MySQLConnector(BaseConnector):
    def _get_connection(self):
        import mysql.connector

        return mysql.connector.connect(
            host=self.config["host"],
            port=self.config.get("port", 3306),
            database=self.config["database"],
            user=self.config["user"],
            password=self.config["password"],
        )

    def connect(self) -> None:
        conn = self._get_connection()
        conn.close()

    def get_schema(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
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
        finally:
            conn.close()

    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            conn.close()
