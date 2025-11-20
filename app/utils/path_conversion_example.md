# 路径转换使用说明

## 问题背景

同步脚本保存的是相对路径（如 `uploads/wechat/logo/123.jpg`），但在某些场景下需要使用绝对路径（如上传文件到微信平台）。

## 解决方案

使用 `convert_to_absolute_path()` 工具函数进行路径转换。

## 使用方法

### 1. 基础用法

```python
from app.utils.file import convert_to_absolute_path

# 相对路径转绝对路径
relative_path = "uploads/wechat/logo/123.jpg"
absolute_path = convert_to_absolute_path(relative_path)
# 结果: E:\code\my\vue-fastapi-admin\static\uploads\wechat\logo\123.jpg
```

### 2. 在 Controller 中使用

```python
from app.controllers.wechat import wechat_controller

# 获取logo的绝对路径
wechat_id = 123
logo_abs_path = await wechat_controller.get_logo_absolute_path(wechat_id)

# 获取二维码的绝对路径
qrcode_abs_path = await wechat_controller.get_qrcode_absolute_path(wechat_id)
```

### 3. 上传到微信平台示例

```python
from app.controllers.wechat import wechat_controller
import requests

async def upload_logo_to_wechat(wechat_id: int):
    """将logo上传到微信平台"""
    
    # 1. 获取图片的绝对路径
    logo_path = await wechat_controller.get_logo_absolute_path(wechat_id)
    
    if not logo_path:
        raise ValueError("Logo不存在")
    
    # 2. 读取文件并上传到微信平台
    with open(logo_path, 'rb') as f:
        files = {'media': f}
        response = requests.post(
            'https://api.weixin.qq.com/cgi-bin/material/add_material',
            files=files,
            params={'access_token': 'YOUR_ACCESS_TOKEN', 'type': 'image'}
        )
    
    return response.json()
```

### 4. 批量处理截图

```python
import os
from app.models.wechat import WechatApp
from app.utils.file import convert_to_absolute_path

async def get_screenshots_absolute_paths(wechat_id: int) -> list[str]:
    """获取小程序所有截图的绝对路径"""
    
    screenshots_dir = f"uploads/wechat/screenshots/{wechat_id}"
    abs_dir = convert_to_absolute_path(screenshots_dir)
    
    if not abs_dir or not os.path.exists(abs_dir):
        return []
    
    # 获取目录下所有图片文件
    screenshots = []
    for filename in sorted(os.listdir(abs_dir)):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            abs_path = os.path.join(abs_dir, filename)
            screenshots.append(abs_path)
    
    return screenshots
```

## 支持的路径格式

函数会自动处理以下格式：

- `uploads/wechat/logo/123.jpg` ✅
- `static/uploads/wechat/logo/123.jpg` ✅（会自动去除 `static/` 前缀）
- `uploads\\wechat\\logo\\123.jpg` ✅（Windows路径分隔符）

## 注意事项

1. **相对路径基准**：所有相对路径都是相对于 `settings.STATIC_DIR`
2. **路径存在性**：函数不验证文件是否存在，只负责路径转换
3. **空值处理**：输入为 `None` 或空字符串时，返回 `None`
4. **跨平台兼容**：自动处理 Windows 和 Unix 的路径分隔符

## 相关文件

- 工具函数：`app/utils/file.py::convert_to_absolute_path()`
- Controller方法：`app/controllers/wechat.py::get_logo_absolute_path()`
- 同步接口：`app/api/v1/miniprogram/miniprogram.py::sync_from_miniprogram()`
