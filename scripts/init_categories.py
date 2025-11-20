#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化常用分类并为 MyWechat 数据随机分配分类
"""
import asyncio
import random
import sys
from pathlib import Path

# 添加项目根目录到Python搜索路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise

from app.settings.config import settings


# 常用小程序分类参考
COMMON_CATEGORIES = [
    {"name": "工具", "icon_url": "", "sort": 1},
    {"name": "生活服务", "icon_url": "", "sort": 2},
    {"name": "购物", "icon_url": "", "sort": 3},
    {"name": "教育学习", "icon_url": "", "sort": 4},
    {"name": "娱乐", "icon_url": "", "sort": 5},
    {"name": "新闻资讯", "icon_url": "", "sort": 6},
    {"name": "社交", "icon_url": "", "sort": 7},
    {"name": "旅游出行", "icon_url": "", "sort": 8},
    {"name": "健康医疗", "icon_url": "", "sort": 9},
    {"name": "金融理财", "icon_url": "", "sort": 10},
    {"name": "美食餐饮", "icon_url": "", "sort": 11},
    {"name": "运动健身", "icon_url": "", "sort": 12},
    {"name": "家居家装", "icon_url": "", "sort": 13},
    {"name": "母婴亲子", "icon_url": "", "sort": 14},
    {"name": "汽车服务", "icon_url": "", "sort": 15},
]


async def init_categories():
    """初始化分类表"""
    from app.models.wxapp_extra import Category

    print("[init_categories] 初始化分类表...")
    
    existing = await Category.all()
    if existing:
        print(f"[init_categories] 分类表已有 {len(existing)} 条数据，跳过初始化")
        return
    
    created_categories = []
    for cat in COMMON_CATEGORIES:
        obj = await Category.create(**cat)
        created_categories.append(obj)
        print(f"[init_categories] 创建分类: {cat['name']}")
    
    print(f"[init_categories] 完成，共创建 {len(created_categories)} 个分类")
    return created_categories


async def assign_random_categories():
    """为 MyWechat 表中未分配分类的数据随机分配分类"""
    from app.models.wechat import WechatApp
    from app.models.wxapp_extra import Category

    print("[assign_random_categories] 为 MyWechat 数据随机分配分类...")

    # 获取所有分类
    categories = await Category.filter(is_online=True).all()
    if not categories:
        print("[assign_random_categories] 没有可用分类，请先运行初始化分类")
        return

    category_ids = [c.id for c in categories]
    print(f"[assign_random_categories] 可用分类数: {len(category_ids)}")

    # 获取未分配分类的小程序（category_id 为 None 或 0）
    apps = await WechatApp.filter(is_deleted=False).all()
    unassigned = [a for a in apps if not a.category_id]
    
    if not unassigned:
        print("[assign_random_categories] 所有小程序已分配分类")
        return

    print(f"[assign_random_categories] 找到 {len(unassigned)} 个未分配分类的小程序")

    count = 0
    for app in unassigned:
        # 随机分配一个分类
        app.category_id = random.choice(category_ids)
        await app.save()
        count += 1
        print(f"[assign_random_categories] {app.name} (id={app.id}) -> 分类ID={app.category_id}")

    print(f"[assign_random_categories] 完成，共分配 {count} 个小程序")


async def main():
    print("[main] 启动脚本...")
    
    # 初始化 Tortoise ORM
    await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
    print("[main] Tortoise ORM 已初始化")

    # 1. 初始化分类
    await init_categories()

    # 2. 为 MyWechat 随机分配分类
    await assign_random_categories()

    # 关闭连接
    await Tortoise.close_connections()
    print("[main] 脚本执行完成")


if __name__ == "__main__":
    asyncio.run(main())
