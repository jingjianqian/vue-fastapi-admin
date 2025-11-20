#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通过 HTTP 请求测试首页接口
"""
import requests
import json


def test_home_api():
    """测试首页 API"""
    base_url = "http://localhost:9999/api/v1"
    url = f"{base_url}/wxapp/home"
    
    print(f"[test_home_http] 请求接口: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"[response] HTTP状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[error] 请求失败: {response.text}")
            return
        
        data = response.json()
        print(f"[response] 业务状态码: {data.get('code')}")
        
        if data.get('code') != 200:
            print(f"[error] 业务错误: {data.get('msg')}")
            return
        
        result = data.get('data', {})
        
        print("\n[接口返回数据]")
        print(f"  banners: {len(result.get('banners', []))} 条")
        print(f"  top: {len(result.get('top', []))} 条")
        print(f"  categories: {len(result.get('categories', []))} 条")
        print(f"  list: {len(result.get('list', []))} 条")
        print(f"  total: {result.get('total', 0)}")
        
        # 显示置顶小程序
        top_apps = result.get('top', [])
        if top_apps:
            print(f"\n[置顶小程序] 共 {len(top_apps)} 个:")
            for i, app in enumerate(top_apps[:5], 1):
                print(f"  {i}. {app.get('name')} (id={app.get('id')}, category_id={app.get('category_id')})")
            if len(top_apps) > 5:
                print(f"  ... 还有 {len(top_apps) - 5} 个")
        
        # 显示分类
        categories = result.get('categories', [])
        if categories:
            print(f"\n[分类列表] 共 {len(categories)} 个:")
            for i, cat in enumerate(categories[:5], 1):
                print(f"  {i}. {cat.get('name')} (id={cat.get('id')})")
            if len(categories) > 5:
                print(f"  ... 还有 {len(categories) - 5} 个")
        
        # 显示小程序列表
        app_list = result.get('list', [])
        if app_list:
            print(f"\n[小程序列表] 共 {len(app_list)} 个:")
            for i, app in enumerate(app_list[:3], 1):
                print(f"  {i}. {app.get('name')} (id={app.get('id')}, is_top={app.get('is_top')})")
        
        print("\n[test_home_http] ✅ 接口测试成功")
        
    except requests.exceptions.ConnectionError:
        print("[error] ❌ 无法连接到后端服务，请确保后端已启动")
        print("       提示: 运行 'python main.py' 启动后端服务")
    except requests.exceptions.Timeout:
        print("[error] ❌ 请求超时")
    except Exception as e:
        print(f"[error] ❌ 请求失败: {e}")


if __name__ == "__main__":
    test_home_api()
