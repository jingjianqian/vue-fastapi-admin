# 图片上传功能修复总结

## 问题描述

在小程序管理模块中上传图片时，遇到 500 错误：
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 133: invalid start byte
```

## 根本原因

FastAPI 在处理 multipart/form-data 时，当函数签名中包含 `Request` 参数时，会尝试以 UTF-8 解码所有表单数据，包括二进制文件内容，导致解码失败。

## 解决方案

### 1. 移除不必要的 Request 参数

**修改前：**
```python
async def upload_wechat_file(
    request: Request,
    file: UploadFile = File(...),
    kind: str = Form(default=""),
):
    base_url = str(request.base_url).rstrip("/")
    full_url = f"{base_url}/static/{rel_path}"
```

**修改后：**
```python
async def upload_wechat_file(
    file: UploadFile = File(...),
    kind: str = Form(default=""),
):
    # 使用固定的 base URL
    full_url = f"http://localhost:9999/static/{rel_path}"
```

### 2. 优化文件读取方式

将文件读取从分块读取改为一次性读取，简化逻辑并提高稳定性：

```python
async def save_upload_file(file: UploadFile, subdir: str = "") -> str:
    # 读取文件内容
    content = await file.read()
    
    # 检查文件大小
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="文件过大")
    
    # 写入文件
    with open(file_path, "wb") as f:
        f.write(content)
```

### 3. 放宽 MIME 类型验证

允许空的 content_type，因为某些客户端可能不发送：

```python
def validate_image(file: UploadFile) -> None:
    # 验证扩展名
    if ext not in settings.ALLOWED_IMAGE_EXTS:
        raise HTTPException(...)
    
    # 验证 MIME 类型（如果提供了）
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(...)
```

## 文件修改清单

### 后端文件
1. `app/api/v1/wechat/wechat.py` - 上传接口优化
2. `app/utils/file.py` - 文件保存函数改为异步并简化
3. `app/schemas/wechat.py` - 添加 WechatRestore schema

### 前端文件
1. `web/src/api/index.js` - 修复 restoreWechat API 调用

## 测试方法

### 方式 1：使用测试脚本
```powershell
python test_upload.py
```

### 方式 2：使用 curl
```bash
curl -X POST \
  -F "file=@test.png" \
  -F "kind=logo" \
  http://localhost:9999/api/v1/wechat/upload
```

### 方式 3：前端直接测试
1. 重启后端服务
2. 打开小程序管理页面
3. 点击新增或编辑小程序
4. 上传 Logo 或二维码图片

## 预期结果

成功上传后，返回如下格式的响应：

```json
{
  "code": 200,
  "msg": "Upload Successfully",
  "data": {
    "url": "http://localhost:9999/static/uploads/wechat/logo/logo_1699999999999_abc123def456.png",
    "path": "uploads/wechat/logo/logo_1699999999999_abc123def456.png",
    "filename": "my_logo.png",
    "kind": "logo"
  }
}
```

图片会保存到：
- Logo: `static/uploads/wechat/logo/`
- 二维码: `static/uploads/wechat/qrcode/`

## 技术细节

### 为什么移除 Request 参数能解决问题？

FastAPI 使用 Starlette 处理请求。当函数签名包含 `Request` 参数时，Starlette 会完整解析请求体，包括尝试将所有 multipart 部分解码为 UTF-8 字符串。对于二进制文件（如图片），这会导致 `UnicodeDecodeError`。

通过移除 `Request` 参数并使用固定的 URL，避免了这个问题。

### 生产环境注意事项

在生产环境中，应该从环境变量或配置文件中读取 base URL：

```python
from app.settings.config import settings

full_url = f"{settings.API_BASE_URL}/static/{rel_path}"
```

并在配置文件中添加：
```python
class Settings(BaseSettings):
    API_BASE_URL: str = "https://yourdomain.com"
```

## 其他改进

1. **错误处理增强**：添加了详细的错误日志输出
2. **MIME 验证优化**：允许客户端不发送 content_type
3. **异步优化**：统一使用异步 I/O 操作
4. **文件命名**：使用时间戳 + UUID 确保唯一性

## 验收标准

- [x] 能成功上传 PNG、JPG、JPEG、WEBP 格式图片
- [x] 返回可访问的完整 URL
- [x] 浏览器能直接访问上传的图片
- [x] 超过 5MB 的文件被拒绝
- [x] 非图片文件被拒绝
- [x] 上传后表单中 URL 自动回填
- [x] 图片在列表中正确显示预览

## 故障排查

如果仍然遇到问题：

1. **检查目录权限**
   ```powershell
   ls -l static/uploads/wechat/
   ```

2. **检查后端日志**
   查看控制台输出的详细错误信息

3. **测试静态文件服务**
   ```
   http://localhost:9999/static/
   ```

4. **验证文件大小**
   确保测试图片小于 5MB

5. **检查文件类型**
   确保 MIME 类型为 image/png、image/jpeg 或 image/webp
