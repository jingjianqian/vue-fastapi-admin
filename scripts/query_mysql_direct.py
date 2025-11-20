#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接连接 MySQL 查询 MyWechat 表数据
"""
import pymysql
import sys

# MySQL 连接配置（请根据实际情况修改）
MYSQL_CONFIGS = [
    {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "Jing.jianqian2334",
        "database": "myweb_dev2",
    },
    {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "Jing.jianqian2334",
        "database": "myweb_dev2",
    },
]


def try_connect_and_query():
    """尝试连接 MySQL 并查询数据"""
    
    for i, config in enumerate(MYSQL_CONFIGS, 1):
        print(f"\n[尝试 {i}] 连接配置: host={config['host']}, port={config['port']}, db={config['database']}")
        
        try:
            # 连接 MySQL
            conn = pymysql.connect(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"],
                database=config["database"],
                charset="utf8mb4",
            )
            print(f"✅ 连接成功！")
            
            cursor = conn.cursor()
            
            # 查询 MyWechat 表总数
            cursor.execute("SELECT COUNT(*) FROM MyWechat WHERE is_deleted = 0")
            total = cursor.fetchone()[0]
            print(f"\n[MyWechat表] 总数据量（未删除）: {total}")
            
            # 查询置顶数量
            cursor.execute("SELECT COUNT(*) FROM MyWechat WHERE is_deleted = 0 AND is_top = 1")
            top_count = cursor.fetchone()[0]
            print(f"[MyWechat表] 置顶数量: {top_count}")
            
            # 查询分类分配情况
            cursor.execute("""
                SELECT COUNT(*) 
                FROM MyWechat 
                WHERE is_deleted = 0 AND (category_id IS NOT NULL AND category_id != 0)
            """)
            with_category = cursor.fetchone()[0]
            print(f"[MyWechat表] 已分配分类: {with_category}")
            
            without_category = total - with_category
            print(f"[MyWechat表] 未分配分类: {without_category}")
            
            # 查询前5条数据
            cursor.execute("""
                SELECT id, name, appid, category_id, is_top 
                FROM MyWechat 
                WHERE is_deleted = 0 
                LIMIT 5
            """)
            rows = cursor.fetchall()
            print(f"\n[前5条数据示例]")
            for row in rows:
                print(f"  id={row[0]}, name={row[1]}, appid={row[2]}, category_id={row[3]}, is_top={row[4]}")
            
            # 查询 Category 表
            try:
                cursor.execute("SELECT COUNT(*) FROM Category WHERE is_online = 1")
                cat_count = cursor.fetchone()[0]
                print(f"\n[Category表] 在线分类数量: {cat_count}")
            except Exception as e:
                print(f"\n[Category表] 查询失败: {e}")
            
            cursor.close()
            conn.close()
            
            print(f"\n✅ 成功连接并查询 MySQL！正确的连接配置是：")
            print(f"   host: {config['host']}")
            print(f"   port: {config['port']}")
            print(f"   database: {config['database']}")
            
            return config
            
        except pymysql.Error as e:
            print(f"❌ 连接失败: {e}")
            continue
        except Exception as e:
            print(f"❌ 查询出错: {e}")
            continue
    
    print("\n❌ 所有连接配置都失败了")
    print("提示：请检查 MySQL 服务是否运行，或者提供正确的 host 地址")
    return None


if __name__ == "__main__":
    try_connect_and_query()
