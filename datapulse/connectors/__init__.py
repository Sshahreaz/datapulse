from .csv_connector import CSVConnector
from .mysql_connector import MySQLConnector
from .postgres_connector import PostgreSQLConnector
from .sqlite_connector import SQLiteConnector

CONNECTOR_MAP = {
    "SQLite": SQLiteConnector,
    "CSV / Excel": CSVConnector,
    "PostgreSQL": PostgreSQLConnector,
    "MySQL": MySQLConnector,
}
