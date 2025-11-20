import os
import time
import uuid

from fastapi import HTTPException, UploadFile

from app.settings.config import settings


def convert_to_absolute_path(relative_path: str | None) -> str | None:
    """
    将相对路径转换为绝对路径
    
    用于将数据库中存储的相对路径（如 'uploads/wechat/logo/123.jpg'）
    转换为本地文件系统的绝对路径，供上传或其他文件操作使用。
    
    Args:
        relative_path: 相对路径，通常以 'uploads/' 或 'static/' 开头
        
    Returns:
        绝对路径，如果输入为空则返回 None
        
    Examples:
        >>> convert_to_absolute_path('uploads/wechat/logo/123.jpg')
        'E:\\code\\my\\vue-fastapi-admin\\static\\uploads\\wechat\\logo\\123.jpg'
        
        >>> convert_to_absolute_path('static/uploads/wechat/logo/123.jpg')
        'E:\\code\\my\\vue-fastapi-admin\\static\\uploads\\wechat\\logo\\123.jpg'
    """
    if not relative_path:
        return None
    
    # 规范化路径分隔符（统一为正斜杠）
    normalized = relative_path.replace("\\", "/")
    
    # 移除开头的 'static/' 前缀（如果存在）
    if normalized.startswith("static/"):
        normalized = normalized[7:]  # 去掉 'static/'
    
    # 拼接绝对路径
    absolute_path = os.path.join(settings.STATIC_DIR, normalized)
    
    # 规范化路径（处理 ../ 等）
    absolute_path = os.path.normpath(absolute_path)
    
    return absolute_path


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def validate_image(file: UploadFile) -> None:
    """验证图片文件类型和MIME类型"""
    ext = get_file_extension(file.filename or "")
    
    if ext not in settings.ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"只允许上传 {', '.join(settings.ALLOWED_IMAGE_EXTS)} 格式的图片"
        )
    
    # 验证 MIME 类型（如果提供了）
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片类型: {content_type}"
        )


def generate_unique_filename(prefix: str, ext: str) -> str:
    """生成唯一的文件名"""
    timestamp = int(time.time() * 1000)
    unique_id = uuid.uuid4().hex[:12]
    return f"{prefix}_{timestamp}_{unique_id}.{ext}"


async def save_upload_file(file: UploadFile, subdir: str = "") -> str:
    """
    保存上传的文件
    
    Args:
        file: 上传的文件对象
        subdir: 子目录名称（如 logo, qrcode）
        
    Returns:
        相对于static目录的路径，用于拼接URL
        
    Raises:
        HTTPException: 文件验证失败或文件过大
    """
    # 验证图片
    validate_image(file)
    
    # 获取扩展名
    ext = get_file_extension(file.filename or "image")
    
    # 生成唯一文件名
    filename = generate_unique_filename(subdir or "img", ext)
    
    # 确定目标目录
    if subdir:
        target_dir = os.path.join(settings.UPLOAD_DIR, subdir)
    else:
        target_dir = settings.UPLOAD_DIR
    
    # 创建目录（如果不存在）
    os.makedirs(target_dir, exist_ok=True)
    
    # 完整文件路径
    file_path = os.path.join(target_dir, filename)
    
    # 分块写入文件，同时检查大小
    written_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    try:
        # 读取文件内容
        content = await file.read()
        
        # 检查文件大小
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大，限制为 {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.0f}MB"
            )
        
        # 写入文件
        with open(file_path, "wb") as f:
            f.write(content)
    
    except HTTPException:
        raise
    except Exception as e:
        # 清理文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 返回相对路径（相对于static目录）
    # 例如: "uploads/wechat/logo/logo_1699999999999_abc123def456.png"
    rel_parts = ["uploads", "wechat"]
    if subdir:
        rel_parts.append(subdir)
    rel_parts.append(filename)
    
    return "/".join(rel_parts)
