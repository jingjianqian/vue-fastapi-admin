#!/usr/bin/env python3
"""
为前 20 条小程序分配分类

用法：
    python scripts/assign_categories.py
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
from app.models.wxapp_extra import Category


async def assign_categories():
    """为前 20 条小程序分配分类"""
    # 初始化数据库连接
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    try:
        # 获取所有在线分类
        categories = await Category.filter(is_online=True).order_by("sort")
        if not categories:
            print("❌ 没有可用的分类，请先运行 check_categories.py 创建分类")
            return
        
        print(f"📋 找到 {len(categories)} 个可用分类")
        
        # 获取前 20 条小程序
        apps = await WechatApp.filter(is_deleted=False).order_by("id").limit(20)
        if not apps:
            print("❌ 未找到任何小程序")
            return
        
        print(f"📱 找到 {len(apps)} 条小程序，开始分配分类...\n")
        
        # 根据小程序名称智能分配分类
        category_mapping = {
            "医生": 7,  # 健康医疗
            "医疗": 7,
            "健康": 7,
            "快递": 1,  # 生活服务
            "计算器": 8,  # 工具效率
            "基金": 4,  # 金融理财
            "理财": 4,
            "购物": 5,  # 购物消费
            "买": 5,
            "酒店": 6,  # 出行旅游
            "旅游": 6,
            "出行": 6,
            "相册": 2,  # 社交网络
            "语言": 3,  # 教育学习
            "学": 3,
            "词": 3,
            "书法": 3,
            "企业": 8,  # 工具效率
            "查询": 8,
            "文字": 8,
        }
        
        updated_count = 0
        for i, app in enumerate(apps):
            # 如果已经有分类，跳过
            if app.category_id:
                cat = next((c for c in categories if c.id == app.category_id), None)
                cat_name = cat.name if cat else "未知"
                print(f"⏭️  [{i+1:2d}] ID={app.id:2d}, {app.name:20s} - 已有分类: {cat_name}")
                continue
            
            # 智能匹配分类
            assigned_category_id = None
            for keyword, cat_id in category_mapping.items():
                if keyword in app.name:
                    assigned_category_id = cat_id
                    break
            
            # 如果没有匹配到，按照顺序循环分配
            if not assigned_category_id:
                assigned_category_id = categories[i % len(categories)].id
            
            # 更新分类
            app.category_id = assigned_category_id
            await app.save()
            
            cat = next((c for c in categories if c.id == assigned_category_id), None)
            cat_name = cat.name if cat else "未知"
            
            updated_count += 1
            print(f"✅ [{i+1:2d}] ID={app.id:2d}, {app.name:20s} → {cat_name}")
        
        print(f"\n🎉 完成！共更新 {updated_count} 条记录")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(assign_categories())
