#!/usr/bin/env python3
"""
创建默认 Banner 占位图片

用法：
    python scripts/create_banner_placeholders.py
"""
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ 请先安装 Pillow 库：pip install Pillow")
    sys.exit(1)


def create_banner_placeholder(width=750, height=360, text="Banner", color="#4A90E2", filename="banner.jpg"):
    """创建一个简单的 Banner 占位图"""
    # 创建图片
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    
    # 尝试使用系统字体，如果失败则不绘制文字
    try:
        # Windows 系统字体
        if os.path.exists("C:/Windows/Fonts/msyh.ttc"):
            font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 60)
        elif os.path.exists("C:/Windows/Fonts/arial.ttf"):
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 60)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 绘制文字
    draw.text((x, y), text, fill='white', font=font)
    
    # 保存图片
    banner_dir = os.path.join(project_root, "static", "uploads", "banners")
    os.makedirs(banner_dir, exist_ok=True)
    filepath = os.path.join(banner_dir, filename)
    img.save(filepath, quality=90)
    
    return filepath


def main():
    print("🎨 正在创建 Banner 占位图片...\n")
    
    # 创建 3 个不同颜色的 Banner
    banners = [
        ("banner1.jpg", "小程序导航", "#4A90E2"),  # 蓝色
        ("banner2.jpg", "精选推荐", "#E74C3C"),    # 红色
        ("banner3.jpg", "热门应用", "#27AE60"),    # 绿色
    ]
    
    for filename, text, color in banners:
        filepath = create_banner_placeholder(
            width=750,
            height=360,
            text=text,
            color=color,
            filename=filename
        )
        print(f"✅ 创建成功：{filepath}")
    
    print("\n🎉 完成！")
    print("\n📝 提示：")
    print("  - 你可以直接替换这些图片，文件名保持不变")
    print("  - 推荐尺寸：750x360 像素")
    print("  - 支持格式：jpg, png, webp")
    print("  - 位置：static/uploads/banners/")


if __name__ == "__main__":
    main()
