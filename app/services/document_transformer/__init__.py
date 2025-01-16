from enum import Enum
from typing import List, Optional, Union

from langchain_core.language_models import BaseLLM

from .base import DocumentTransformer
from .chain import ChainTransformer
from .clean import CleanTransformer
from .hypothetical_question import HypotheticalQuestionTransformer
from .lower import LowercaseTransformer
from .merge import MergeDocumentsTransformer
from .prefix import PrefixTransformer
from .summary import SummaryTransformer


class TransformerType(Enum):
    """文档转换器类型枚举"""
    SUMMARY = "summary"
    HYPOTHETICAL_QUESTION = "hypothetical_question"
    CHAIN = "chain"
    LOWERCASE = "lowercase"
    MERGE = "merge"
    PREFIX = "prefix"
    CLEAN = "clean"


def create_transformer(
        transformer_type: Union[TransformerType, str],
        llm: Optional[BaseLLM] = None,
        **kwargs
) -> DocumentTransformer:
    """
    工厂方法：根据指定的转换器类型创建对应的转换器实例

    Args:
        transformer_type: 转换器类型，可以是 TransformerType 枚举或对应的字符串
        llm: 语言模型，用于需要 LLM 的转换器
        **kwargs: 转换器的其他参数

    Returns:
        DocumentTransformer: 对应类型的转换器实例

    Raises:
        ValueError: 当转换器类型不支持时抛出
    """
    if isinstance(transformer_type, str):
        try:
            transformer_type = TransformerType(transformer_type.lower())
        except ValueError:
            raise ValueError(f"不支持的转换器类型: {transformer_type}")

    if transformer_type == TransformerType.SUMMARY:
        if llm is None:
            raise ValueError("SummaryTransformer 需要提供 llm 参数")
        return SummaryTransformer(llm=llm, **kwargs)

    elif transformer_type == TransformerType.HYPOTHETICAL_QUESTION:
        if llm is None:
            raise ValueError("HypotheticalQuestionTransformer 需要提供 llm 参数")
        return HypotheticalQuestionTransformer(llm=llm, **kwargs)
    elif transformer_type == TransformerType.LOWERCASE:
        return LowercaseTransformer(**kwargs)
    elif transformer_type == TransformerType.MERGE:
        max_length = kwargs.pop("max_length", 0)
        if not max_length:
            raise ValueError("MergeDocumentsTransformer 需要提供 max_length 参数")
        return MergeDocumentsTransformer(max_length=max_length, **kwargs)
    elif transformer_type == TransformerType.PREFIX:
        prefix_str = kwargs.pop("prefix", "")
        if not prefix_str:
            raise ValueError("PrefixTransformer 需要提供 prefix 参数")
        return PrefixTransformer(prefix=prefix_str, **kwargs)
    elif transformer_type == TransformerType.CLEAN:
        return CleanTransformer(**kwargs)
    elif transformer_type == TransformerType.CHAIN:
        transforms = kwargs.pop("transforms", None)
        if not transforms:
            raise ValueError("ChainTransformer 需要提供 transforms 参数")
        return ChainTransformer(transforms=transforms, **kwargs)

    else:
        raise ValueError(f"不支持的转换器类型: {transformer_type}")


def create_chain_transformer(
        transformer_types: List[Union[TransformerType, str]],
        llm: Optional[BaseLLM] = None,
        **kwargs
) -> ChainTransformer:
    """
    创建串联多个转换器的 ChainTransformer

    Args:
        transformer_types: 要串联的转换器类型列表
        llm: 语言模型，用于需要 LLM 的转换器
        **kwargs: 转换器的其他参数

    Returns:
        ChainTransformer: 串联的转换器实例
    """
    transforms = []
    for t_type in transformer_types:
        transformer = create_transformer(t_type, llm=llm, **kwargs)
        transforms.append(transformer)

    return ChainTransformer(transforms=transforms)
