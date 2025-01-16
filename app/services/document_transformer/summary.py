from typing import AsyncGenerator, List

from langchain_core.documents import Document
from langchain_core.language_models import BaseLLM
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from .base import DocumentTransformer


class SummaryTransformer(DocumentTransformer):
    def __init__(self, llm: BaseLLM, max_summary_length: int = 200, **kwargs):
        """
        为文档生成摘要的转换器

        Args:
            llm: 用于生成摘要的语言模型
            max_summary_length: 摘要的最大长度
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.max_summary_length = max_summary_length

        prompt = PromptTemplate(
            template="""请为以下文本生成一个简洁的摘要，摘要长度不超过{max_length}个字符：

            文本内容：
            {text}

            摘要：""",
            input_variables=["text", "max_length"]
        )

        # 使用 LCEL 格式构建链
        self.chain = prompt | llm | StrOutputParser()

    async def transform(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        for doc in documents[:2]:
            # 生成摘要
            summary = await self.chain.ainvoke({
                "text": doc.page_content,
                "max_length": self.max_summary_length
            })

            # 创建摘要文档
            yield Document(
                page_content=summary.strip(),
                metadata={
                    **doc.metadata,
                    "document_type": "summary",
                    "original_content": doc.page_content
                }
            )

            # 同时保留原始文档
            # yield doc
