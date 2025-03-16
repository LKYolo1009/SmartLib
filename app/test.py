#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库连接测试脚本
用于测试PostgreSQL数据库连接和验证数据表内容
"""

import sys
import traceback
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# 从应用配置导入设置（如果无法导入，请替换为直接设置）
try:
    from app.core.config import settings
    DATABASE_URI = settings.SQLALCHEMY_DATABASE_URI
except ImportError:
    # 如果无法导入settings，手动设置连接信息
    DB_USER = "postgres"      # 替换为你的用户名
    DB_PASSWORD = "123456"  # 替换为你的密码
    DB_HOST = "localhost"     # 数据库主机
    DB_PORT = "5432"          # 数据库端口
    DB_NAME = "mylibrary"       # 数据库名称
    
    DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def test_database_connection():
    """测试数据库连接"""
    try:
        # 创建引擎
        print(f"尝试连接到数据库: {DATABASE_URI.split('@')[1]}")
        engine = create_engine(DATABASE_URI)
        
        # 测试连接
        with engine.connect() as connection:
            print("✅ 数据库连接成功!")
            
            # 获取数据库版本
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"数据库版本: {version}")
            
            # 获取所有表
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if not tables:
                print("⚠️ 数据库中没有表！")
                return False
            
            print(f"\n发现 {len(tables)} 个表:")
            for table in tables:
                print(f"  - {table}")
                
                # 获取表的列信息
                columns = inspector.get_columns(table)
                print(f"    列数: {len(columns)}")
                
                # 获取表中的行数
                row_count = connection.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
                print(f"    行数: {row_count}")
                
                # 如果表中有数据，显示一些示例数据
                if row_count > 0:
                    print(f"    数据样例:")
                    sample = connection.execute(text(f"SELECT * FROM {table} LIMIT 3")).fetchall()
                    for i, row in enumerate(sample, 1):
                        print(f"      行 {i}: {row}")
                else:
                    print(f"    ⚠️ 表 {table} 中没有数据!")
                
                print()  # 为可读性添加空行
            
            # 修改这里以使用复数形式的表名
            required_tables = ["books", "authors", "publishers", "categories"]
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️ 缺少表: {', '.join(missing_tables)}")
                return False
                
            # 验证外键约束
   
            for table in ["books"]:
                if table in tables:
                    print(f"\n检查 {table} 表中的外键值:")
                    
                    # 检查author_id
                    if "authors" in tables:
                        invalid_authors = connection.execute(text(
                            f"SELECT b.book_id, b.author_id FROM {table} b LEFT JOIN authors a ON b.author_id = a.author_id "
                            f"WHERE b.author_id IS NOT NULL AND a.author_id IS NULL"
                        )).fetchall()
                        
                        if invalid_authors:
                            print(f"  ⚠️ 发现 {len(invalid_authors)} 本书引用了不存在的author_id:")
                            for book in invalid_authors[:5]:  # 只显示前5个
                                print(f"    - 书籍ID: {book[0]}, 无效的author_id: {book[1]}")
                    
                    # 检查publisher_id
                    if "publishers" in tables:
                        invalid_publishers = connection.execute(text(
                            f"SELECT b.book_id, b.publisher_id FROM {table} b LEFT JOIN publishers p ON b.publisher_id = p.publisher_id "
                            f"WHERE b.publisher_id IS NOT NULL AND p.publisher_id IS NULL"
                        )).fetchall()
                        
                        if invalid_publishers:
                            print(f"  ⚠️ 发现 {len(invalid_publishers)} 本书引用了不存在的publisher_id:")
                            for book in invalid_publishers[:5]:
                                print(f"    - 书籍ID: {book[0]}, 无效的publisher_id: {book[1]}")
                    
                    # 检查category_id
                    if "categories" in tables:
                        invalid_categories = connection.execute(text(
                            f"SELECT b.book_id, b.category_id FROM {table} b LEFT JOIN categories c ON b.category_id = c.category_id "
                            f"WHERE b.category_id IS NOT NULL AND c.category_id IS NULL"
                        )).fetchall()
                        
                        if invalid_categories:
                            print(f"  ⚠️ 发现 {len(invalid_categories)} 本书引用了不存在的category_id:")
                            for book in invalid_categories[:5]:
                                print(f"    - 书籍ID: {book[0]}, 无效的category_id: {book[1]}")
            
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ 数据库连接错误: {str(e)}")
        print("\n详细错误信息:")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ 发生未知错误: {str(e)}")
        print("\n详细错误信息:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 数据库连接测试 ===")
    success = test_database_connection()
    print("\n=== 测试结果 ===")
    if success:
        print("✅ 数据库连接和基本检查成功!")
        sys.exit(0)
    else:
        print("❌ 数据库测试失败，请检查上面的错误信息!")
        sys.exit(1)