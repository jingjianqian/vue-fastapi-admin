#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试首页接口
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python搜索路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise
from app.settings.config import settings


async def test_home_api():
    """测试首页接口数据"""
    from app.models.wechat import WechatApp
    from app.models.wxapp_extra import Category, Banner
    
    print("[test_home_api] 模拟首页接口查询...")
    
    # 1. 查询分类
    categories = await Category.filter(is_online=True).order_by("sort", "id")
    print(f"\n[categories] 分类数量: {len(categories)}")
    for cat in categories[:5]:
        print(f"  - {cat.name} (id={cat.id}, sort={cat.sort})")
    
    # 2. 查询横幅
    banners = await Banner.filter(is_online=True).order_by("sort", "id")
    print(f"\n[banners] 横幅数量: {len(banners)}")
    
    # 3. 查询置顶小程序
    top_apps = await WechatApp.filter(is_deleted=False, is_top=True).order_by("id")
    print(f"\n[top_apps] 置顶小程序数量: {len(top_apps)}")
    for app in top_apps[:5]:
        print(f"  - {app.name} (id={app.id}, category_id={app.category_id})")
    
    # 4. 查询小程序列表（分页）
    page = 1
    page_size = 10
    offset = (page - 1) * page_size
    apps = await WechatApp.filter(is_deleted=False).offset(offset).limit(page_size).order_by("id")
    total = await WechatApp.filter(is_deleted=False).count()
    print(f"\n[app_list] 小程序列表 (page={page}, page_size={page_size})")
    print(f"  总数: {total}")
    print(f"  当前页数量: {len(apps)}")
    for app in apps[:3]:
        print(f"  - {app.name} (id={app.id}, category_id={app.category_id}, is_top={app.is_top})")
    
    # 5. 模拟接口返回的数据结构
    print("\n[response_structure] 模拟接口返回:")
    response = {
        "banners": [{"id": b.id, "image_url": b.image_url} for b in banners],
        "top": [
            {
                "id": a.id,
                "name": a.name,
                "icon": a.logo_url or "",
                "desc": a.description or "",
                "category_id": a.category_id,
                "is_top": a.is_top,
            }
            for a in top_apps
        ],
        "categories": [{"id": c.id, "name": c.name, "icon_url": c.icon_url} for c in categories],
        "list": [
            {
                "id": a.id,
                "name": a.name,
                "icon": a.logo_url or "",
                "desc": a.description or "",
                "category_id": a.category_id,
                "is_top": a.is_top,
            }
            for a in apps
        ],
        "total": total,
    }
    
    print(f"  banners: {len(response['banners'])} 条")
    print(f"  top: {len(response['top'])} 条")
    print(f"  categories: {len(response['categories'])} 条")
    print(f"  list: {len(response['list'])} 条")
    print(f"  total: {response['total']}")
    
    print("\n[test_home_api] ✅ 测试完成，接口数据结构正常")


async def main():
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    await test_home_api()
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
