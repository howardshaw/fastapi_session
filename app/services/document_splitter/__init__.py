from enum import Enum
from typing import Union

from .base import DocumentSplitter
from .langchain import LangChainSplitter


class SplitterType(Enum):
    """文档分割器类型枚举"""
    LANGCHAIN = "langchain"


def create_splitter(
        splitter_type: Union[SplitterType, str],
        mime_type: str = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        **kwargs
) -> DocumentSplitter:
    """
    工厂方法：根据指定的类型创建文档分割器实例

    Args:
        splitter_type: 分割器类型，可以是 SplitterType 枚举或对应的字符串
        mime_type: 文档的 MIME 类型，用于选择合适的分割器
        chunk_size: 每个文本块的最大字符数
        chunk_overlap: 相邻文本块之间的重叠字符数
        **kwargs: 分割器的其他参数

    Returns:
        DocumentSplitter: 对应类型的分割器实例

    Raises:
        ValueError: 当分割器类型不支持时抛出
    """
    if isinstance(splitter_type, str):
        try:
            splitter_type = SplitterType(splitter_type.lower())
        except ValueError:
            raise ValueError(f"不支持的分割器类型: {splitter_type}")

    if splitter_type == SplitterType.LANGCHAIN:
        return LangChainSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            mime_type=mime_type,
            **kwargs
        )
    else:
        raise ValueError(f"不支持的分割器类型: {splitter_type}")
