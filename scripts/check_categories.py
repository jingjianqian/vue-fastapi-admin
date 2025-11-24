#!/usr/bin/env python3
"""
检查并初始化分类数据

用法：
    python scripts/check_categories.py
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tortoise import Tortoise
from app.settings.config import settings
from app.models.wxapp_extra import Category


async def check_and_init_categories():
    """检查并初始化分类数据"""
    # 初始化数据库连接
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    try:
        # 查询所有分类
        cats = await Category.all()
        print(f"📋 找到 {len(cats)} 个分类：")
        
        if cats:
            for c in cats:
                status = "✅ 在线" if c.is_online else "❌ 下线"
                print(f"  ID={c.id}, Name={c.name}, Sort={c.sort}, {status}")
        else:
            print("❌ 数据库中没有任何分类数据")
            print("\n正在创建默认分类...")
            
            # 创建一些默认分类
            default_categories = [
                {"name": "生活服务", "sort": 1, "is_online": True},
                {"name": "社交网络", "sort": 2, "is_online": True},
                {"name": "教育学习", "sort": 3, "is_online": True},
                {"name": "金融理财", "sort": 4, "is_online": True},
                {"name": "购物消费", "sort": 5, "is_online": True},
                {"name": "出行旅游", "sort": 6, "is_online": True},
                {"name": "健康医疗", "sort": 7, "is_online": True},
                {"name": "工具效率", "sort": 8, "is_online": True},
            ]
            
            for cat_data in default_categories:
                cat = await Category.create(**cat_data)
                print(f"  ✅ 创建分类：ID={cat.id}, Name={cat.name}")
            
            print("\n🎉 默认分类创建完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(check_and_init_categories())
