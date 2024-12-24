from passlib.context import CryptContext

# 创建一个模块级别的密码上下文实例
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    使用 bcrypt 算法对密码进行哈希处理

    Args:
        password: 原始密码

    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配

    Args:
        plain_password: 原始密码
        hashed_password: 哈希后的密码

    Returns:
        bool: 如果密码匹配返回 True，否则返回 False
    """
    return pwd_context.verify(plain_password, hashed_password)
