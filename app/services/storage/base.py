from abc import ABC, abstractmethod
from datetime import timedelta
from typing import BinaryIO, Optional, Dict


class StorageService(ABC):
    """存储服务基类"""

    @abstractmethod
    async def upload_file(
            self,
            file: BinaryIO,
            path: str,
            content_type: Optional[str] = None,
            metadata: Optional[Dict] = None
    ) -> str:
        """
        上传文件
        
        Args:
            file: 文件对象
            path: 存储路径
            content_type: 内容类型
            metadata: 元数据
            
        Returns:
            str: 文件的完整访问路径
        """
        pass

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """
        删除文件
        
        Args:
            path: 文件路径
            
        Returns:
            bool: 是否删除成功
        """
        pass

    @abstractmethod
    async def get_file_url(self, path: str, expire: timedelta = timedelta(days=7)) -> str:
        """
        获取文件访问URL
        
        Args:
            path: 文件路径
            expire: URL过期时间(秒)
            
        Returns:
            str: 文件访问URL
        """
        pass

    @abstractmethod
    async def download(self, source_path: str, dest_path: str) -> None:
        """
        获取文件内容
        
        Args:
            source_path: 文件路径
            dest_path: 下载路径
            
        Returns:

        """
        pass
