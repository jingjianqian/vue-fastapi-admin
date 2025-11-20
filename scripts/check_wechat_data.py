#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查 MyWechat 表数据状态
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python搜索路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise
from app.settings.config import settings


async def main():
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    from app.models.wechat import WechatApp
    
    total = await WechatApp.filter(is_deleted=False).count()
    print(f"MyWechat 表总数据量: {total}")
    
    with_category = await WechatApp.filter(is_deleted=False, category_id__not=None).count()
    print(f"已分配分类: {with_category}")
    
    without_category = total - with_category
    print(f"未分配分类: {without_category}")
    
    if total > 0:
        samples = await WechatApp.filter(is_deleted=False).limit(5).all()
        print("\n前5条数据示例:")
        for app in samples:
            print(f"  id={app.id}, name={app.name}, category_id={app.category_id}")
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
