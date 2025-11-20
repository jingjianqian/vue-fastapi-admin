#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设置置顶小程序
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


async def set_top_apps(count: int = 20):
    """随机设置指定数量的小程序为置顶"""
    from app.models.wechat import WechatApp
    
    print(f"[set_top_apps] 开始设置置顶小程序，目标数量: {count}")
    
    # 获取所有小程序
    all_apps = await WechatApp.filter(is_deleted=False).all()
    total = len(all_apps)
    
    if total == 0:
        print("[set_top_apps] 没有可用的小程序数据")
        return
    
    print(f"[set_top_apps] 当前小程序总数: {total}")
    
    # 如果现有数据少于目标数量，则全部置顶
    if total <= count:
        print(f"[set_top_apps] 小程序总数({total})不足{count}个，将全部置顶")
        for app in all_apps:
            if not app.is_top:
                app.is_top = True
                await app.save()
                print(f"[set_top] {app.name} (id={app.id})")
        print(f"[set_top_apps] 完成，共设置 {total} 个置顶小程序")
        return
    
    # 随机选择指定数量的小程序置顶
    selected = random.sample(all_apps, count)
    
    # 先将所有小程序取消置顶
    for app in all_apps:
        if app.is_top:
            app.is_top = False
            await app.save()
    
    # 设置选中的小程序为置顶
    topped_count = 0
    for app in selected:
        app.is_top = True
        await app.save()
        topped_count += 1
        print(f"[set_top] {app.name} (id={app.id}, category_id={app.category_id})")
    
    print(f"\n[set_top_apps] 完成，共设置 {topped_count} 个置顶小程序")
    
    # 验证结果
    top_apps = await WechatApp.filter(is_deleted=False, is_top=True).all()
    print(f"[verify] 数据库中置顶小程序数量: {len(top_apps)}")


async def main():
    await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
    
    # 设置20个置顶小程序
    await set_top_apps(count=20)
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
