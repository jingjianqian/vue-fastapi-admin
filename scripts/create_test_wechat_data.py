#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建 MyWechat 测试数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python搜索路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from tortoise import Tortoise
from app.settings.config import settings


# 测试小程序数据
TEST_APPS = [
    {
        "name": "番茄待办",
        "appid": "wx1234567890abcd01",
        "secret": "test_secret_001",
        "description": "专注学习工作的时间管理工具",
        "logo_url": "https://via.placeholder.com/120/ff6b6b/ffffff?text=番茄",
    },
    {
        "name": "美团外卖",
        "appid": "wx1234567890abcd02",
        "secret": "test_secret_002",
        "description": "送啥都快的外卖平台",
        "logo_url": "https://via.placeholder.com/120/ffd93d/ffffff?text=美团",
    },
    {
        "name": "每日英语",
        "appid": "wx1234567890abcd03",
        "secret": "test_secret_003",
        "description": "每天学习一句英语，提升英语能力",
        "logo_url": "https://via.placeholder.com/120/6bcf7f/ffffff?text=英语",
    },
    {
        "name": "健康计步",
        "appid": "wx1234567890abcd04",
        "secret": "test_secret_004",
        "description": "记录每日步数，养成运动习惯",
        "logo_url": "https://via.placeholder.com/120/4ecdc4/ffffff?text=计步",
    },
    {
        "name": "天气助手",
        "appid": "wx1234567890abcd05",
        "secret": "test_secret_005",
        "description": "实时天气预报，出行无忧",
        "logo_url": "https://via.placeholder.com/120/95e1d3/ffffff?text=天气",
    },
    {
        "name": "记账本",
        "appid": "wx1234567890abcd06",
        "secret": "test_secret_006",
        "description": "简单实用的个人记账工具",
        "logo_url": "https://via.placeholder.com/120/f38181/ffffff?text=记账",
    },
    {
        "name": "音乐播放器",
        "appid": "wx1234567890abcd07",
        "secret": "test_secret_007",
        "description": "海量音乐，随心畅听",
        "logo_url": "https://via.placeholder.com/120/aa96da/ffffff?text=音乐",
    },
    {
        "name": "快递查询",
        "appid": "wx1234567890abcd08",
        "secret": "test_secret_008",
        "description": "一键查询所有快递物流信息",
        "logo_url": "https://via.placeholder.com/120/fcbad3/ffffff?text=快递",
    },
    {
        "name": "电影票房",
        "appid": "wx1234567890abcd09",
        "secret": "test_secret_009",
        "description": "实时电影票房排行榜",
        "logo_url": "https://via.placeholder.com/120/ffffd2/ffffff?text=票房",
    },
    {
        "name": "決车违章查询",
        "appid": "wx1234567890abcd10",
        "secret": "test_secret_010",
        "description": "快速查询车辆违章信息",
        "logo_url": "https://via.placeholder.com/120/a8d8ea/ffffff?text=违章",
    },
    {
        "name": "口笔计算器",
        "appid": "wx1234567890abcd11",
        "secret": "test_secret_011",
        "description": "多功能科学计算器",
        "logo_url": "https://via.placeholder.com/120/ff9f1c/ffffff?text=计算",
    },
    {
        "name": "读书笔记",
        "appid": "wx1234567890abcd12",
        "secret": "test_secret_012",
        "description": "记录阅读感悟，分享读书心得",
        "logo_url": "https://via.placeholder.com/120/cbf3f0/ffffff?text=读书",
    },
    {
        "name": "拍照识花",
        "appid": "wx1234567890abcd13",
        "secret": "test_secret_013",
        "description": "AI智能识别植物名称",
        "logo_url": "https://via.placeholder.com/120/2ec4b6/ffffff?text=识花",
    },
    {
        "name": "健身教练",
        "appid": "wx1234567890abcd14",
        "secret": "test_secret_014",
        "description": "专业健身计划与指导",
        "logo_url": "https://via.placeholder.com/120/e71d36/ffffff?text=健身",
    },
    {
        "name": "菜谱大全",
        "appid": "wx1234567890abcd15",
        "secret": "test_secret_015",
        "description": "海量菜谱，在家轻松做大餐",
        "logo_url": "https://via.placeholder.com/120/ff6f59/ffffff?text=菜谱",
    },
    {
        "name": "宝宝辅食",
        "appid": "wx1234567890abcd16",
        "secret": "test_secret_016",
        "description": "科学的婴儿辅食指导",
        "logo_url": "https://via.placeholder.com/120/ffbe0b/ffffff?text=辅食",
    },
    {
        "name": "医院挂号",
        "appid": "wx1234567890abcd17",
        "secret": "test_secret_017",
        "description": "在线医院预约挂号服务",
        "logo_url": "https://via.placeholder.com/120/fb5607/ffffff?text=挂号",
    },
    {
        "name": "理财助手",
        "appid": "wx1234567890abcd18",
        "secret": "test_secret_018",
        "description": "个人理财规划与建议",
        "logo_url": "https://via.placeholder.com/120/3a86ff/ffffff?text=理财",
    },
    {
        "name": "社区购物",
        "appid": "wx1234567890abcd19",
        "secret": "test_secret_019",
        "description": "社区团购，价格优惠",
        "logo_url": "https://via.placeholder.com/120/8338ec/ffffff?text=团购",
    },
    {
        "name": "星座运势",
        "appid": "wx1234567890abcd20",
        "secret": "test_secret_020",
        "description": "每日星座运势与分析",
        "logo_url": "https://via.placeholder.com/120/c77dff/ffffff?text=星座",
    },
    {
        "name": "小说阅读",
        "appid": "wx1234567890abcd21",
        "secret": "test_secret_021",
        "description": "热门小说在线免费阅读",
        "logo_url": "https://via.placeholder.com/120/9d4edd/ffffff?text=小说",
    },
    {
        "name": "酒店预订",
        "appid": "wx1234567890abcd22",
        "secret": "test_secret_022",
        "description": "全球酒店在线预订平台",
        "logo_url": "https://via.placeholder.com/120/7209b7/ffffff?text=酒店",
    },
    {
        "name": "摄影教程",
        "appid": "wx1234567890abcd23",
        "secret": "test_secret_023",
        "description": "从入门到精通的摄影教学",
        "logo_url": "https://via.placeholder.com/120/560bad/ffffff?text=摄影",
    },
    {
        "name": "家政服务",
        "appid": "wx1234567890abcd24",
        "secret": "test_secret_024",
        "description": "专业家政保洁服务",
        "logo_url": "https://via.placeholder.com/120/480ca8/ffffff?text=家政",
    },
    {
        "name": "车辆保养",
        "appid": "wx1234567890abcd25",
        "secret": "test_secret_025",
        "description": "汽车保养知识与预约",
        "logo_url": "https://via.placeholder.com/120/3f37c9/ffffff?text=保养",
    },
    {
        "name": "学习计划",
        "appid": "wx1234567890abcd26",
        "secret": "test_secret_026",
        "description": "制定和跟踪学习目标",
        "logo_url": "https://via.placeholder.com/120/4361ee/ffffff?text=学习",
    },
    {
        "name": "语音翻译",
        "appid": "wx1234567890abcd27",
        "secret": "test_secret_027",
        "description": "多语言实时语音翻译",
        "logo_url": "https://via.placeholder.com/120/4895ef/ffffff?text=翻译",
    },
    {
        "name": "心情日记",
        "appid": "wx1234567890abcd28",
        "secret": "test_secret_028",
        "description": "记录生活点滴，守护内心平静",
        "logo_url": "https://via.placeholder.com/120/4cc9f0/ffffff?text=日记",
    },
    {
        "name": "宠物社区",
        "appid": "wx1234567890abcd29",
        "secret": "test_secret_029",
        "description": "宠物交流与养护知识分享",
        "logo_url": "https://via.placeholder.com/120/06d6a0/ffffff?text=宠物",
    },
    {
        "name": "水果生鲜",
        "appid": "wx1234567890abcd30",
        "secret": "test_secret_030",
        "description": "新鲜水果生鲜快速送达",
        "logo_url": "https://via.placeholder.com/120/06ffa5/ffffff?text=水果",
    },
]


async def main():
    await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
    
    from app.models.wechat import WechatApp
    
    print("[create_test_data] 开始创建测试数据...")
    
    count = 0
    for app_data in TEST_APPS:
        # 检查是否已存在
        exists = await WechatApp.filter(appid=app_data["appid"]).exists()
        if exists:
            print(f"[skip] {app_data['name']} (appid={app_data['appid']}) 已存在")
            continue
        
        await WechatApp.create(**app_data)
        count += 1
        print(f"[created] {app_data['name']} (appid={app_data['appid']})")
    
    print(f"\n[create_test_data] 完成，共创建 {count} 个测试小程序")
    
    # 再次运行分配分类
    print("\n[assign_categories] 为新创建的小程序分配分类...")
    from scripts.init_categories import assign_random_categories
    await assign_random_categories()
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
