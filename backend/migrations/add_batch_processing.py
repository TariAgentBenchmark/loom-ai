#!/usr/bin/env python3
"""
数据库迁移脚本：添加批量处理功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_batch_processing_tables():
    """添加批量处理相关表"""
    db = SessionLocal()
    
    try:
        # 检查 batch_tasks 表是否已存在
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM sqlite_master 
            WHERE type='table' AND name='batch_tasks'
        """))
        
        table_exists = result.fetchone()[0] > 0
        
        if table_exists:
            logger.info("✅ batch_tasks 表已存在，跳过创建")
        else:
            # 创建 batch_tasks 表
            logger.info("📝 正在创建 batch_tasks 表...")
            db.execute(text("""
                CREATE TABLE batch_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id VARCHAR(50) NOT NULL UNIQUE,
                    user_id INTEGER NOT NULL,
                    task_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) DEFAULT 'queued',
                    total_images INTEGER NOT NULL DEFAULT 0,
                    completed_images INTEGER NOT NULL DEFAULT 0,
                    failed_images INTEGER NOT NULL DEFAULT 0,
                    options JSON,
                    total_credits_used DECIMAL(18, 2) NOT NULL DEFAULT 0,
                    estimated_time INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            
            # 创建索引
            db.execute(text("CREATE INDEX ix_batch_tasks_batch_id ON batch_tasks(batch_id)"))
            db.execute(text("CREATE INDEX ix_batch_tasks_user_id ON batch_tasks(user_id)"))
            db.execute(text("CREATE INDEX ix_batch_tasks_task_type ON batch_tasks(task_type)"))
            db.execute(text("CREATE INDEX ix_batch_tasks_status ON batch_tasks(status)"))
            
            db.commit()
            logger.info("✅ batch_tasks 表创建成功")
        
        # 检查 tasks 表是否已有 batch_id 列
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM pragma_table_info('tasks') 
            WHERE name = 'batch_id'
        """))
        
        column_exists = result.fetchone()[0] > 0
        
        if column_exists:
            logger.info("✅ tasks.batch_id 列已存在，跳过添加")
        else:
            # 添加 batch_id 列到 tasks 表
            logger.info("📝 正在添加 batch_id 列到 tasks 表...")
            db.execute(text("""
                ALTER TABLE tasks 
                ADD COLUMN batch_id INTEGER REFERENCES batch_tasks(id)
            """))
            
            # 创建索引
            db.execute(text("CREATE INDEX ix_tasks_batch_id ON tasks(batch_id)"))
            
            db.commit()
            logger.info("✅ tasks.batch_id 列添加成功")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("🔄 开始执行数据库迁移：添加批量处理功能...")
    
    try:
        add_batch_processing_tables()
        print("\n🎉 迁移完成!")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
