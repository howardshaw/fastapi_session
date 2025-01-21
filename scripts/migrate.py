import asyncio
import os
import subprocess

from aiomysql import create_pool, Error as MySQLError
from dotenv import load_dotenv

load_dotenv()


async def ensure_database():
    """
    确保数据库存在，不存在则创建。
    从环境变量加载数据库连接信息并实现重试机制。
    """
    # 从环境变量获取连接信息
    user = os.getenv("DATABASE__USER", "root")
    password = os.getenv("DATABASE__PASSWORD", "root")
    database = os.getenv("DATABASE__DATABASE", "temporal")
    host = os.getenv("DATABASE__HOST", "mysql")
    port = int(os.getenv("DATABASE__PORT", 3306))
    max_retries = 30  # 最大重试次数
    retry_delay = 1   # 每次重试的等待时间（秒）

    retry_count = 0

    while retry_count < max_retries:
        try:
            # 使用连接池简化资源管理
            async with create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                charset="utf8mb4",
                autocommit=True,
                maxsize=5
            ) as pool:
                async with pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        # 检查数据库是否存在
                        await cur.execute(f"SHOW DATABASES LIKE %s", (database,))
                        result = await cur.fetchone()

                        # 如果数据库不存在则创建
                        if not result:
                            print(f"Creating database '{database}'...")
                            await cur.execute(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                            print(f"Database '{database}' created successfully!")

                print("Database is ready!")
                return  # 数据库准备完成，退出循环

        except MySQLError as e:
            retry_count += 1
            print(f"Database connection failed: {e}. Retrying ({retry_count}/{max_retries})...")
            await asyncio.sleep(retry_delay)

        except Exception as e:
            retry_count += 1
            print(f"Unexpected error: {e}. Retrying ({retry_count}/{max_retries})...")
            await asyncio.sleep(retry_delay)

    # 如果超出最大重试次数，抛出异常
    raise Exception(f"Failed to ensure database after {max_retries} retries")


def run_migrations():
    print("Running database migrations...")
    result = subprocess.run(["alembic", "upgrade", "head"], check=True)
    if result.returncode == 0:
        print("Migrations completed successfully!")
    else:
        raise Exception("Migration failed!")


if __name__ == "__main__":
    # 确保数据库存在
    asyncio.run(ensure_database())

    # 运行数据库迁移
    run_migrations()
