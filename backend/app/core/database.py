from sqlalchemy import create_engine, MetaData, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# 根据数据库URL类型配置引擎参数
if settings.database_url.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        settings.database_url,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool,
        echo=settings.sqlalchemy_echo
    )
else:
    # PostgreSQL或其他数据库配置
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=settings.sqlalchemy_echo
    )

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

# 元数据
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库"""
    try:
        # 确保模型已注册到元数据
        import app.models  # noqa: F401
        # 创建所有表
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully")
        except IntegrityError as exc:
            msg = str(exc)
            # Handle race conditions on PostgreSQL when multiple workers create tables concurrently.
            if "pg_type_typname_nsp_index" in msg:
                inspector = inspect(engine)
                if inspector.has_table("task_logs"):
                    logger.warning(
                        "task_logs already exists (likely created by another worker). "
                        "Continuing startup."
                    )
                    return
            raise
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def close_db() -> None:
    """关闭数据库连接"""
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


# 数据库健康检查
def check_db_health() -> bool:
    """检查数据库连接健康状态"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
