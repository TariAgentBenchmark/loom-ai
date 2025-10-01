#!/usr/bin/env python3
"""
数据库迁移脚本：添加 is_admin 列到 users 表
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


def add_is_admin_column():
    """添加 is_admin 列到 users 表"""
    db = SessionLocal()
    
    try:
        # 检查列是否已存在
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM pragma_table_info('users') 
            WHERE name = 'is_admin'
        """))
        
        column_exists = result.fetchone()[0] > 0
        
        if column_exists:
            logger.info("✅ is_admin 列已存在，跳过迁移")
            return
        
        # 添加 is_admin 列
        logger.info("📝 正在添加 is_admin 列...")
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN is_admin BOOLEAN DEFAULT 0
        """))
        
        db.commit()
        logger.info("✅ is_admin 列添加成功")
        
        # 更新现有的管理员用户（如果有的话）
        logger.info("🔍 正在查找需要更新的管理员用户...")
        result = db.execute(text("""
            UPDATE users 
            SET is_admin = 1 
            WHERE email = 'admin@loom-ai.com'
        """))
        
        db.commit()
        
        if result.rowcount > 0:
            logger.info(f"✅ 已更新 {result.rowcount} 个管理员用户")
        else:
            logger.info("ℹ️  没有找到需要更新的管理员用户")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("🔄 开始执行数据库迁移：添加 is_admin 列...")
    
    try:
        add_is_admin_column()
        print("\n🎉 迁移完成!")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()