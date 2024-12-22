import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import Database
from app.core.exceptions import (
    AccountNotFoundError,
    DatabaseError,
    InsufficientFundsError,
    AccountLockedError,
)
from app.models import Account
from app.services.transaction import TransactionService


class AsyncContextManagerMock:
    """模拟异步上下文管理器"""
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_db():
    db = MagicMock(spec=Database)
    # 创建一个异步上下文管理器的 mock
    transaction_context = AsyncContextManagerMock()
    db.transaction = MagicMock(return_value=transaction_context)
    return db


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def service(mock_db, mock_session):
    mock_db.get_session.return_value = mock_session
    return TransactionService(mock_db)


@pytest.fixture
def mock_account():
    return Account(
        id=1,
        user_id=1,
        balance=1000.0,
    )


@pytest.mark.asyncio
async def test_get_account_by_id_success(service, mock_session, mock_account):
    """测试成功获取账户"""
    # 设置 mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_account
    mock_session.execute.return_value = mock_result

    # 执行测试
    account = await service.get_account_by_id(1)

    # 验证结果
    assert account == mock_account
    assert account.balance == 1000.0
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_account_by_id_not_found(service, mock_session):
    """测试获取不存在的账户"""
    # 设置 mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # 执行测试并验证异常
    with pytest.raises(AccountNotFoundError):
        await service.get_account_by_id(999)


@pytest.mark.asyncio
async def test_get_account_by_id_database_error(service, mock_session):
    """测试数据库错误场景"""
    # 设置 mock
    mock_session.execute.side_effect = SQLAlchemyError("Database error")

    # 执行测试并验证异常
    with pytest.raises(DatabaseError):
        await service.get_account_by_id(1)


@pytest.mark.asyncio
async def test_withdraw_success(service, mock_session, mock_account):
    """测试成功取款"""
    # 设置 mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_account
    mock_session.execute.return_value = mock_result

    # 执行测试
    account = await service.withdraw(1, 500.0)

    # 验证结果
    assert account.balance == 500.0
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_account)


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(service, mock_session, mock_account):
    """测试余额不足"""
    # 设置 mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_account
    mock_session.execute.return_value = mock_result

    # 执行测试并验证异常
    with pytest.raises(InsufficientFundsError):
        await service.withdraw(1, 2000.0)


@pytest.mark.asyncio
async def test_deposit_success(service, mock_session, mock_account):
    """测试成功存款"""
    # 设置 mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_account
    mock_session.execute.return_value = mock_result

    # 执行测试
    account = await service.deposit(1, 500.0)

    # 验证结果
    assert account.balance == 1500.0
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_account)


@pytest.mark.asyncio
async def test_deposit_account_locked(service, mock_session, mock_account):
    """测试账户锁定场景"""
    # 设置 mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_account
    mock_session.execute.return_value = mock_result

    # 执行测试并验证异常
    with pytest.raises(AccountLockedError):
        await service.deposit(1, 10.0)  # 特殊金额 10 会触发账户锁定


@pytest.mark.asyncio
async def test_transfer_success(service, mock_session):
    """测试成功转账"""
    # 设置 mock accounts
    from_account = Account(id=1, user_id=1, balance=1000.0)
    to_account = Account(id=2, user_id=2, balance=500.0)

    mock_result_from = MagicMock()
    mock_result_from.scalar_one_or_none.return_value = from_account
    mock_result_to = MagicMock()
    mock_result_to.scalar_one_or_none.return_value = to_account

    mock_session.execute.side_effect = [mock_result_from, mock_result_to]

    # 执行测试
    result = await service.transfer(1, 2, 300.0)

    # 验证结果
    assert from_account.balance == 700.0
    assert to_account.balance == 800.0
    assert result["status"] == "success"
    assert result["amount"] == 300.0
    assert mock_session.flush.call_count == 2


@pytest.mark.asyncio
async def test_transfer_insufficient_funds(service, mock_session):
    """测试转账余额不足"""
    # 设置 mock accounts
    from_account = Account(id=1, user_id=1, balance=100.0)
    to_account = Account(id=2, user_id=2, balance=500.0)

    mock_result_from = MagicMock()
    mock_result_from.scalar_one_or_none.return_value = from_account
    mock_result_to = MagicMock()
    mock_result_to.scalar_one_or_none.return_value = to_account

    mock_session.execute.side_effect = [mock_result_from, mock_result_to]

    # 执行测试并验证异常
    with pytest.raises(InsufficientFundsError):
        await service.transfer(1, 2, 200.0)


@pytest.mark.asyncio
async def test_transfer_account_locked(service, mock_session):
    """测试转账时账户锁定"""
    # 设置 mock accounts
    from_account = Account(id=1, user_id=1, balance=1000.0)
    to_account = Account(id=2, user_id=2, balance=500.0)

    mock_result_from = MagicMock()
    mock_result_from.scalar_one_or_none.return_value = from_account
    mock_result_to = MagicMock()
    mock_result_to.scalar_one_or_none.return_value = to_account

    mock_session.execute.side_effect = [mock_result_from, mock_result_to]

    # 执行测试并验证异常
    with pytest.raises(AccountLockedError):
        await service.transfer(1, 2, 10.0)  # 特殊金额 10 会触发账户锁定
