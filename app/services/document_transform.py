import uuid
from abc import ABC, abstractmethod
from typing import List, Dict

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.logger import get_logger
from app.services.llm import LLMService

logger = get_logger(__name__)


class DocumentTransformer(ABC):
    """文档转换器基类"""

    @abstractmethod
    async def transform(self, documents: List[Document]) -> List[Document]:
        """转换文档"""
        pass


class ContentCleanTransformer(DocumentTransformer):
    """内容清理转换器"""

    async def transform(self, documents: List[Document]) -> List[Document]:
        cleaned_docs = []
        for doc in documents:
            cleaned_text = (doc.page_content
                            .strip()
                            .replace('\n\n', '\n')
                            .replace('\t', ' '))
            doc.page_content = cleaned_text
            cleaned_docs.append(doc)
        return cleaned_docs


class ChunkSplitTransformer(DocumentTransformer):
    """文档分块转换器"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def transform(self, documents: List[Document]) -> List[Document]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        # 分割文档
        split_docs = text_splitter.split_documents(documents)

        # 给每个分割后的文档添加唯一 ID
        for doc in split_docs:
            id = str(uuid.uuid4())
            doc.id = id
            doc.metadata["doc_id"] = id

        return split_docs


class HypotheticalQuestionTransformer(DocumentTransformer):
    """假设问生成"""

    def __init__(self, llm: LLMService):
        llm.with_system_prompt(
            "Generate a list of exactly 3 hypothetical questions that the below document could be used to answer.")
        self.llm = llm
        self._id_counter = 0

    def _get_next_id(self, prefix: str = "faq") -> str:
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}"

    async def transform(self, documents: List[Document]) -> List[Document]:
        question_docs = []

        for doc in documents[:2]:
            response = await self.llm.asend_message(doc.page_content)
            logger.info(f"Generate hypothetical questions: {response}")

            hypothetical_questions = response.content.split('\n')
            for question in hypothetical_questions:
                if len(question.strip()) == 0:
                    continue
                doc_id = self._get_next_id(doc.id or str(uuid.uuid4()))
                question_doc = Document(
                    page_content=f"{question.strip()}",
                    metadata={
                        "doc_id": doc.id,
                        "type": "faq",
                        "source": doc.metadata.get("source", ""),
                    },
                    id=doc_id
                )
                question_docs.append(question_doc)

        return question_docs

    def _parse_faq_response(self, response: str) -> List[Dict]:
        faqs = []
        current_qa = {}

        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('Q:'):
                if current_qa:
                    faqs.append(current_qa)
                current_qa = {'question': line[2:].strip()}
            elif line.startswith('A:') and current_qa:
                current_qa['answer'] = line[2:].strip()

        if current_qa:
            faqs.append(current_qa)

        return faqs


class SummaryTransformer(DocumentTransformer):
    """摘要生成转换器"""

    def __init__(self, llm: LLMService):
        self.llm = llm
        self.llm.with_system_prompt("Please provide a concise summary of the following text.")
        self._id_counter = 0

    def _get_next_id(self) -> str:
        self._id_counter += 1
        return f"summary_{self._id_counter}"

    async def transform(self, documents: List[Document]) -> List[Document]:
        summary_docs = []

        for doc in documents[:2]:
            response = await self.llm.asend_message(doc.page_content)

            doc_id = self._get_next_id()
            summary_doc = Document(
                page_content=response.content.strip(),
                metadata={
                    "doc_id": doc.id,
                    "type": "summary",
                    "source": doc.metadata.get("source", ""),
                },
                id=doc_id
            )
            summary_docs.append(summary_doc)

        return summary_docs
