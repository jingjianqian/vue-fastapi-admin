"""
确保小程序管理菜单存在的脚本
运行此脚本将在数据库中创建小程序管理菜单（如果不存在）
"""
import asyncio
from tortoise import Tortoise
from app.settings.config import settings
from app.models.admin import Menu, Role, Api
from app.schemas.menus import MenuType


async def ensure_wechat_menu():
    # 初始化数据库连接
    await Tortoise.init(config=settings.TORTOISE_ORM)
    await Tortoise.generate_schemas()
    
    print("检查小程序管理菜单是否存在...")
    
    # 检查是否已存在
    exist = await Menu.filter(component="/system/wechat").exists()
    if exist:
        print("✅ 小程序管理菜单已存在")
        menu = await Menu.filter(component="/system/wechat").first()
        print(f"   菜单ID: {menu.id}")
        print(f"   菜单名称: {menu.name}")
        print(f"   路由路径: {menu.path}")
        print(f"   组件路径: {menu.component}")
    else:
        print("❌ 小程序管理菜单不存在，正在创建...")
        
        # 找到系统管理父级菜单
        parent = await Menu.filter(path="/system", parent_id=0).first()
        if not parent:
            print("   错误：找不到系统管理父级菜单")
            return
        
        print(f"   找到父级菜单: {parent.name} (ID: {parent.id})")
        
        # 创建小程序管理菜单
        menu = await Menu.create(
            menu_type=MenuType.MENU,
            name="小程序管理",
            path="wechat",
            order=7,
            parent_id=parent.id,
            icon="mdi:wechat",
            is_hidden=False,
            component="/system/wechat",
            keepalive=False,
        )
        print(f"✅ 小程序管理菜单创建成功 (ID: {menu.id})")
        
        # 为管理员角色添加菜单权限
        admin = await Role.filter(name="管理员").first()
        if admin:
            await admin.menus.add(menu)
            print(f"✅ 已为管理员角色添加菜单权限")
        
        # 为普通用户角色添加菜单权限
        user = await Role.filter(name="普通用户").first()
        if user:
            await user.menus.add(menu)
            print(f"✅ 已为普通用户角色添加菜单权限")
        
        # 查找并添加API权限
        wechat_apis = await Api.filter(path__startswith="/api/v1/wechat").all()
        print(f"   找到 {len(wechat_apis)} 个 wechat 相关API")
        
        if admin and wechat_apis:
            await admin.apis.add(*wechat_apis)
            print(f"✅ 已为管理员添加 {len(wechat_apis)} 个API权限")
        
        if user and wechat_apis:
            readonly_apis = [api for api in wechat_apis if api.method == "GET"]
            if readonly_apis:
                await user.apis.add(*readonly_apis)
                print(f"✅ 已为普通用户添加 {len(readonly_apis)} 个只读API权限")
    
    # 显示所有系统管理下的子菜单
    print("\n当前系统管理下的所有菜单：")
    parent = await Menu.filter(path="/system", parent_id=0).first()
    if parent:
        children = await Menu.filter(parent_id=parent.id).order_by("order")
        for child in children:
            print(f"  {child.order}. {child.name} - {child.component}")
    
    await Tortoise.close_connections()
    print("\n完成！请刷新浏览器页面查看菜单。")


if __name__ == "__main__":
    asyncio.run(ensure_wechat_menu())
