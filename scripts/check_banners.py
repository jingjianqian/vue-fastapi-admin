#!/usr/bin/env python3
"""
检查并初始化 Banner 数据

用法：
    python scripts/check_banners.py
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tortoise import Tortoise
from app.settings.config import settings
from app.models.wxapp_extra import Banner


async def check_and_init_banners():
    """检查并初始化 Banner 数据"""
    # 初始化数据库连接
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    try:
        # 查询所有 Banner
        banners = await Banner.all()
        print(f"📋 找到 {len(banners)} 个 Banner：")
        
        if banners:
            for b in banners:
                status = "✅ 在线" if b.is_online else "❌ 下线"
                print(f"  ID={b.id}, Title={b.title or '无标题'}, Sort={b.sort}, {status}")
                print(f"     Image: {b.image_url}")
        else:
            print("❌ 数据库中没有任何 Banner 数据")
            print("\n正在创建默认 Banner（使用占位图片）...")
            
            # 创建 3 个默认 Banner，使用固定本地路径
            # 你只需要把图片放到 static/uploads/banners/ 目录下即可
            default_banners = [
                {
                    "title": "轮播图 1",
                    "image_url": "uploads/banners/banner1.jpg",
                    "sort": 1,
                    "is_online": True,
                },
                {
                    "title": "轮播图 2",
                    "image_url": "uploads/banners/banner2.jpg",
                    "sort": 2,
                    "is_online": True,
                },
                {
                    "title": "轮播图 3",
                    "image_url": "uploads/banners/banner3.jpg",
                    "sort": 3,
                    "is_online": True,
                },
            ]
            
            for banner_data in default_banners:
                banner = await Banner.create(**banner_data)
                print(f"  ✅ 创建 Banner：ID={banner.id}, Title={banner.title}")
            
            print("\n📝 提示：")
            print("  1. 请将你的轮播图片放到项目的 static/uploads/banners/ 目录下")
            print("  2. 文件名分别为：banner1.jpg, banner2.jpg, banner3.jpg")
            print("  3. 推荐尺寸：750x360 像素（小程序常用比例）")
            print("  4. 支持格式：jpg, png, webp")
            print("\n🎉 默认 Banner 创建完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(check_and_init_banners())
