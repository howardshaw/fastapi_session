from enum import Enum
from typing import Union

from app.repositories.resource import ResourceRepository
from app.services.storage import StorageService
from .base import DocumentLoader
from .langchain import LangChainLoader


class LoaderType(Enum):
    """文档加载器类型枚举"""
    LANGCHAIN = "langchain"


def create_loader(
        loader_type: Union[LoaderType, str],
        resource_repository: ResourceRepository,
        storage_service: StorageService,
        **kwargs
) -> DocumentLoader:
    """
    工厂方法：根据指定的类型创建文档加载器实例

    Args:
        loader_type: 加载器类型，可以是 LoaderType 枚举或对应的字符串
        resource_repository: 资源仓库实例
        storage_service: 存储服务实例
        **kwargs: 加载器的其他参数

    Returns:
        DocumentLoader: 对应类型的加载器实例

    Raises:
        ValueError: 当加载器类型不支持时抛出
    """
    if isinstance(loader_type, str):
        try:
            loader_type = LoaderType(loader_type.lower())
        except ValueError:
            raise ValueError(f"不支持的加载器类型: {loader_type}")

    if loader_type == LoaderType.LANGCHAIN:
        return LangChainLoader(
            resource_repository=resource_repository,
            storage_service=storage_service,
            **kwargs
        )
    else:
        raise ValueError(f"不支持的加载器类型: {loader_type}")
