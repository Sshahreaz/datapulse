from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseConnector(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        pass

    def test_connection(self) -> tuple[bool, str]:
        try:
            self.connect()
            schema = self.get_schema()
            return True, f"Connected. Found {len(schema)} tables."
        except Exception as e:
            return False, str(e)
