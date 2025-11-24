#!/usr/bin/env python3
"""
批量设置前 20 条小程序为置顶（is_top=True）

用法：
    python scripts/set_top_wechat.py
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from tortoise import Tortoise
from app.settings.config import settings
from app.models.wechat import WechatApp


async def set_top_wechat():
    """批量设置前 20 条小程序为置顶"""
    # 初始化数据库连接（使用项目的 TORTOISE_ORM 配置）
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    try:
        # 获取前 20 条未删除的小程序（按 ID 正序）
        apps = await WechatApp.filter(is_deleted=False).order_by("id").limit(20)
        
        if not apps:
            print("❌ 未找到任何小程序记录")
            return
        
        print(f"📋 找到 {len(apps)} 条小程序记录，开始设置为置顶...")
        
        updated_count = 0
        for app in apps:
            if not app.is_top:
                app.is_top = True
                await app.save()
                updated_count += 1
                print(f"✅ ID={app.id}, Name={app.name}, 已设置为置顶")
            else:
                print(f"⏭️  ID={app.id}, Name={app.name}, 已经是置顶状态，跳过")
        
        print(f"\n🎉 完成！共更新 {updated_count} 条记录")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(set_top_wechat())
