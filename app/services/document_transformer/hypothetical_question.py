from typing import AsyncGenerator, List

from langchain_core.documents import Document
from langchain_core.language_models import BaseLLM
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from .base import DocumentTransformer


class HypotheticalQuestionTransformer(DocumentTransformer):
    def __init__(self, llm: BaseLLM, num_questions: int = 3, **kwargs):
        """
        为文档生成问题的转换器

        Args:
            llm: 用于生成问题的语言模型
            num_questions: 每个文档生成的问题数量
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)
        self.num_questions = num_questions

        prompt = PromptTemplate(
            template="""根据以下文本生成 {num_questions} 个相关的问题：

            文本内容：
            {text}

            生成的问题：""",
            input_variables=["text", "num_questions"]
        )

        # 使用 LCEL 格式构建链
        self.chain = prompt | llm | StrOutputParser()

    async def transform(self, documents: List[Document]) -> AsyncGenerator[Document, None]:
        for doc in documents:
            # 生成问题
            questions = await self.chain.ainvoke({
                "text": doc.page_content,
                "num_questions": self.num_questions
            })

            # 为每个问题创建新的文档
            for i, question in enumerate(questions.split("\n")):
                if question.strip():
                    yield Document(
                        page_content=question.strip(),
                        metadata={
                            **doc.metadata,
                            "document_type": "question",
                            "question_index": i,
                            "original_content": doc.page_content
                        }
                    )

            # 同时保留原始文档
            # yield doc
