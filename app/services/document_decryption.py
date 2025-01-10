from abc import ABC, abstractmethod
from typing import Optional, Dict

class DocumentDecryptionService(ABC):
    """文档解密服务基类"""
    
    @abstractmethod
    async def decrypt(self, content: str, encryption_info: Optional[Dict] = None) -> str:
        """解密文档内容"""
        pass

class SimpleDocumentDecryptionService(DocumentDecryptionService):
    """简单的文档解密服务实现"""
    
    async def decrypt(self, content: str, encryption_info: Optional[Dict] = None) -> str:
        if not encryption_info:
            return content
            
        encryption_type = encryption_info.get("type")
        if encryption_type == "base64":
            import base64
            return base64.b64decode(content).decode()
        elif encryption_type == "aes":
            # 实现AES解密
            pass
        
        return content 