#!/usr/bin/env python3
"""
数据库迁移脚本：添加 book_locations 表和 book_copies 表的 location_id 字段
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os
from pathlib import Path
import logging

# Add project root to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Now we can import from app
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """运行数据库迁移"""
    try:
        # Create database engine
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Migration SQL script
        migration_script = r"""
        -- 1. 创建 book_locations 表（如果不存在）
        CREATE TABLE IF NOT EXISTS book_locations (
            location_id SERIAL PRIMARY KEY,
            location_name VARCHAR(255) NOT NULL UNIQUE,
            location_description TEXT,
            qr_code UUID DEFAULT uuid_generate_v4() UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 2. 检查 book_copies 表是否有 location_id 字段
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'book_copies' AND column_name = 'location_id'
            ) THEN
                -- 添加 location_id 字段
                ALTER TABLE book_copies ADD COLUMN location_id INTEGER REFERENCES book_locations(location_id);
                
                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_book_copies_location ON book_copies(location_id);
                
                RAISE NOTICE 'Added location_id column to book_copies table';
            ELSE
                RAISE NOTICE 'location_id column already exists in book_copies table';
            END IF;
        END $$;

        -- 3. 插入一些示例位置数据
        INSERT INTO book_locations (location_name, location_description) VALUES
        ('主书架A区', '主要图书区域，包含文学、历史类图书'),
        ('主书架B区', '科技类图书区域'),
        ('主书架C区', '艺术、音乐类图书区域'),
        ('参考书区', '参考书和工具书区域'),
        ('期刊区', '期刊和杂志区域'),
        ('新书展示区', '新到图书展示区域'),
        ('特藏区', '珍贵图书和特殊收藏区域')
        ON CONFLICT (location_name) DO NOTHING;

        -- 4. 为现有的 book_copies 分配默认位置
        UPDATE book_copies 
        SET location_id = (SELECT location_id FROM book_locations WHERE location_name = '主书架A区' LIMIT 1)
        WHERE location_id IS NULL;

        COMMIT;
        """

        # Execute the migration script
        with SessionLocal() as db:
            logger.info("Starting database migration...")
            db.execute(text(migration_script))
            db.commit()
            logger.info("Database migration completed successfully!")
            logger.info("Added book_locations table and location_id field to book_copies table")
        return True
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Running database migration...")
    success = run_migration()
    if success:
        logger.info("Migration completed successfully!")
    else:
        logger.error("Migration failed!")
        sys.exit(1) 