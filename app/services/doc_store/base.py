from abc import abstractmethod, ABC
from typing import Optional, Sequence

from langchain_core.documents import Document
from langchain_core.runnables import run_in_executor


class DocumentStore(ABC):

    @abstractmethod
    def mget(self, keys: Sequence[str]) -> list[Optional[Document]]:
        pass

    async def amget(self, keys: Sequence[str]) -> list[Optional[Document]]:
        return await run_in_executor(None, self.mget, keys)

    @abstractmethod
    def mset(self, key_value_pairs: Sequence[tuple[str, Document]]) -> None:
        pass

    async def amset(self, key_value_pairs: Sequence[tuple[str, Document]]) -> None:
        return await run_in_executor(None, self.mset, key_value_pairs)

    @abstractmethod
    def mdelete(self, keys: Sequence[str]) -> None:
        pass

    async def amdelete(self, keys: Sequence[str]) -> None:
        return await run_in_executor(None, self.mdelete, keys)
