from abc import ABC, abstractmethod
from typing import List, Any

from pydantic import BaseModel


class Resource(BaseModel):




class DocumentLoader(ABC):
    @abstractmethod
    async def load(self, file_path: str) -> List[Any]:
        pass

class TextSplitter(ABC):
    @abstractmethod
    async def split(self, documents: List[Any], config: dict) -> List[Any]:
        pass

class EmbeddingGenerator(ABC):
    @abstractmethod
    async def generate(self, config: dict) -> Any:
        pass

class VectorIndexer(ABC):
    @abstractmethod
    async def index(self, documents: List[Any], index_name: str, config: dict) -> None:
        pass
