from typing import List
from fastapi import APIRouter, HTTPException, Header, Query
from datetime import datetime
import logging
import os
import re
import requests
from urllib.parse import urlparse

from app.schemas.base import Success, Fail
from app.schemas.miniprogram import MiniprogramCreate, MiniprogramBatchCreate, MiniprogramResponse
from app.models.miniprogram import Miniprogram, MiniprogramTag, MiniprogramScreenshot, MiniprogramRelatedLink
from app.models.wechat import WechatApp
from app.schemas.wechat import PublishStatus
from app.settings.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["爬虫数据接口(Miniprogram)"])


async def save_miniprogram_data(data: MiniprogramCreate) -> Miniprogram:
    """
    保存或更新小程序数据（包含关联表）
    
    Args:
        data: 小程序数据
        
    Returns:
        Miniprogram实例
    """
    # 处理crawl_time
    if isinstance(data.crawl_time, str):
        try:
            crawl_time = datetime.fromisoformat(data.crawl_time.replace('Z', '+00:00'))
        except:
            crawl_time = datetime.now()
    else:
        crawl_time = data.crawl_time or datetime.now()
    
    # 查找是否已存在（根据source_platform + source_id唯一）
    miniprogram = await Miniprogram.filter(
        source_platform=data.source_platform,
        source_id=data.source_id
    ).first()
    
    # 准备主表数据
    main_data = {
        "name": data.name,
        "category": data.category,
        "description": data.description,
        "update_time_text": data.update_time_text,
        "view_count": data.view_count,
        "logo_url": data.logo_url,
        "logo_local_path": data.logo_local_path,
        "qrcode_url": data.qrcode_url,
        "source_url": data.source_url,
        "crawl_time": crawl_time,
    }
    
    if miniprogram:
        # 更新
        await miniprogram.update_from_dict(main_data)
        await miniprogram.save()
        logger.info(f"更新小程序: ID={miniprogram.id}, Name={data.name}")
    else:
        # 创建
        miniprogram = await Miniprogram.create(
            source_id=data.source_id,
            source_platform=data.source_platform,
            **main_data
        )
        logger.info(f"创建小程序: ID={miniprogram.id}, Name={data.name}")
    
    # 更新标签（增量更新：删除不存在的，添加新的）
    if data.tags:
        # 获取现有标签
        existing_tags = await MiniprogramTag.filter(miniprogram=miniprogram).all()
        existing_tag_names = {tag.tag_name for tag in existing_tags}
        new_tag_names = {tag.strip() for tag in data.tags if tag and tag.strip()}
        
        # 删除不再存在的标签
        tags_to_delete = existing_tag_names - new_tag_names
        if tags_to_delete:
            await MiniprogramTag.filter(
                miniprogram=miniprogram,
                tag_name__in=list(tags_to_delete)
            ).delete()
            logger.debug(f"删除标签: {tags_to_delete}")
        
        # 添加新标签
        tags_to_add = new_tag_names - existing_tag_names
        for tag_name in tags_to_add:
            try:
                await MiniprogramTag.create(
                    miniprogram=miniprogram,
                    tag_name=tag_name
                )
            except Exception as e:
                logger.warning(f"创建标签失败: {tag_name}, {e}")
    
    # 更新截图（增量更新：删除不存在的，添加新的）
    if data.screenshots:
        # 获取现有截图
        existing_screenshots = await MiniprogramScreenshot.filter(miniprogram=miniprogram).all()
        existing_urls = {s.image_url for s in existing_screenshots}
        new_urls = {url for url in data.screenshots if url}
        
        # 删除不再存在的截图
        urls_to_delete = existing_urls - new_urls
        if urls_to_delete:
            await MiniprogramScreenshot.filter(
                miniprogram=miniprogram,
                image_url__in=list(urls_to_delete)
            ).delete()
            logger.debug(f"删除截图: {len(urls_to_delete)}张")
        
        # 添加新截图或更新顺序
        for idx, screenshot_url in enumerate(data.screenshots):
            if screenshot_url:
                # 检查是否已存在
                existing = await MiniprogramScreenshot.filter(
                    miniprogram=miniprogram,
                    image_url=screenshot_url
                ).first()
                
                if existing:
                    # 更新顺序
                    if existing.image_order != idx:
                        existing.image_order = idx
                        await existing.save()
                else:
                    # 创建新截图
                    try:
                        await MiniprogramScreenshot.create(
                            miniprogram=miniprogram,
                            image_url=screenshot_url,
                            image_order=idx
                        )
                    except Exception as e:
                        logger.warning(f"创建截图失败: {screenshot_url}, {e}")
    
    # 更新关联链接（增量更新：删除不存在的，添加新的）
    if data.related_links:
        # 获取现有链接
        existing_links = await MiniprogramRelatedLink.filter(miniprogram=miniprogram).all()
        existing_urls = {link.link_url for link in existing_links}
        new_urls = {url for url in data.related_links if url}
        
        # 删除不再存在的链接
        urls_to_delete = existing_urls - new_urls
        if urls_to_delete:
            await MiniprogramRelatedLink.filter(
                miniprogram=miniprogram,
                link_url__in=list(urls_to_delete)
            ).delete()
            logger.debug(f"删除关联链接: {len(urls_to_delete)}条")
        
        # 添加新链接或更新顺序
        for idx, link_url in enumerate(data.related_links):
            if link_url:
                # 检查是否已存在
                existing = await MiniprogramRelatedLink.filter(
                    miniprogram=miniprogram,
                    link_url=link_url
                ).first()
                
                if existing:
                    # 更新顺序
                    if existing.link_order != idx:
                        existing.link_order = idx
                        await existing.save()
                else:
                    # 创建新链接
                    try:
                        await MiniprogramRelatedLink.create(
                            miniprogram=miniprogram,
                            link_url=link_url,
                            link_order=idx
                        )
                    except Exception as e:
                        logger.warning(f"创建关联链接失败: {link_url}, {e}")
    
    return miniprogram


@router.post("/submit", summary="提交单个小程序数据（爬虫使用）")
async def submit_miniprogram(
    data: MiniprogramCreate,
    x_api_key: str = Header(None, description="API密钥")
):
    """
    爬虫提交单个小程序数据
    
    - 需要在Header中提供 X-API-Key
    - 如果source_id已存在，则更新；否则创建
    - 自动处理标签、截图、关联链接的关联关系
    """
    # API Key验证（从配置读取）
    if x_api_key != settings.CRAWLER_API_KEY:
        return Fail(code=401, msg="无效的API Key")
    
    try:
        miniprogram = await save_miniprogram_data(data)
        return Success(
            msg="提交成功",
            data={
                "id": miniprogram.id,
                "source_id": miniprogram.source_id,
                "name": miniprogram.name
            }
        )
    except Exception as e:
        logger.error(f"提交小程序数据失败: {e}", exc_info=True)
        return Fail(code=500, msg=f"提交失败: {str(e)}")


@router.post("/batch-submit", summary="批量提交小程序数据（爬虫使用）")
async def batch_submit_miniprogram(
    data: MiniprogramBatchCreate,
    x_api_key: str = Header(None, description="API密钥")
):
    """
    爬虫批量提交小程序数据
    
    - 需要在Header中提供 X-API-Key
    - 批量处理，返回成功和失败的统计
    """
    # API Key验证（从配置读取）
    if x_api_key != settings.CRAWLER_API_KEY:
        return Fail(code=401, msg="无效的API Key")
    
    results = {
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    for item in data.items:
        try:
            await save_miniprogram_data(item)
            results["success"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "source_id": item.source_id,
                "name": item.name,
                "error": str(e)
            })
            logger.error(f"批量提交失败 source_id={item.source_id}: {e}")
    
    return Success(
        msg=f"批量提交完成: 成功{results['success']}条, 失败{results['failed']}条",
        data=results
    )


@router.get("/list", summary="查询小程序列表")
async def list_miniprogram(
    page: int = 1,
    page_size: int = 20,
    source_platform: str = None
):
    """
    查询小程序列表（支持分页）
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    
    query = Miniprogram.all()
    if source_platform:
        query = query.filter(source_platform=source_platform)
    
    total = await query.count()
    items = await query.offset((page - 1) * page_size).limit(page_size).order_by("-id")
    
    return Success(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": item.id,
                "source_id": item.source_id,
                "name": item.name,
                "category": item.category,
                "source_platform": item.source_platform,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ]
    })


@router.get("/{miniprogram_id}", summary="查询小程序详情")
async def get_miniprogram_detail(miniprogram_id: int):
    """
    查询小程序详情（包含标签、截图、关联链接）
    """
    miniprogram = await Miniprogram.filter(id=miniprogram_id).first()
    
    if not miniprogram:
        return Fail(code=404, msg="小程序不存在")
    
    # 查询关联数据
    tags = await MiniprogramTag.filter(miniprogram=miniprogram).all()
    screenshots = await MiniprogramScreenshot.filter(miniprogram=miniprogram).order_by("image_order").all()
    related_links = await MiniprogramRelatedLink.filter(miniprogram=miniprogram).order_by("link_order").all()
    
    return Success(data={
        "id": miniprogram.id,
        "source_id": miniprogram.source_id,
        "name": miniprogram.name,
        "category": miniprogram.category,
        "description": miniprogram.description,
        "logo_url": miniprogram.logo_url,
        "qrcode_url": miniprogram.qrcode_url,
        "source_platform": miniprogram.source_platform,
        "source_url": miniprogram.source_url,
        "view_count": miniprogram.view_count,
        "update_time_text": miniprogram.update_time_text,
        "crawl_time": miniprogram.crawl_time.isoformat() if miniprogram.crawl_time else None,
        "created_at": miniprogram.created_at.isoformat() if miniprogram.created_at else None,
        "updated_at": miniprogram.updated_at.isoformat() if miniprogram.updated_at else None,
        "tags": [tag.tag_name for tag in tags],
        "screenshots": [
            {
                "url": s.image_url,
                "local_path": s.image_local_path,
                "order": s.image_order
            }
            for s in screenshots
        ],
        "related_links": [link.link_url for link in related_links]
    })


# ============ 同步：从 Miniprogram -> MyWechat ============

def _safe_ext_from_url(url: str) -> str:
    try:
        path = urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if ext in {".png", ".jpg", ".jpeg", ".webp"}:
            return ext
    except Exception:
        pass
    return ".jpg"


def _download_image(url: str, subdir: str, filename_prefix: str) -> str | None:
    """
    下载远程图片到 static/uploads/wechat/{subdir}/ 并返回相对路径（不含 /static 前缀）
    返回 None 表示下载失败
    """
    if not url:
        return None
    try:
        ext = _safe_ext_from_url(url)
        os.makedirs(os.path.join(settings.UPLOAD_DIR, subdir), exist_ok=True)
        # 生成文件名：{prefix}_{数字}.ext 或 {prefix}.ext
        filename = f"{filename_prefix}{ext}"
        if not re.search(r"\.(png|jpg|jpeg|webp)$", filename, re.I):
            filename += ".jpg"
        abs_path = os.path.join(settings.UPLOAD_DIR, subdir, filename)

        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        with open(abs_path, "wb") as f:
            f.write(resp.content)

        # 返回相对路径，形如 uploads/wechat/{subdir}/{filename}
        rel_parts = ["uploads", "wechat", subdir, filename]
        return "/".join(rel_parts)
    except Exception as e:
        logger.warning(f"下载图片失败: {url} -> {e}")
        return None


@router.post("/sync_to_wechat", summary="从 Miniprogram 同步到 MyWechat（支持id一一对应，默认未发布）")
async def sync_from_miniprogram(
    ids: list[int] | None = Query(None, description="仅同步这些 miniprogram.source_id；为空同步全部"),
    limit: int = Query(0, description="最多同步多少条，0表示不限制"),
    x_api_key: str = Header(None, alias="X-API-Key", description="API密钥：settings.CRAWLER_API_KEY")
):
    """
    将 Miniprogram 表数据同步到 MyWechat 表
    - 要求：id 一一对应（MyWechat.id = Miniprogram.source_id）
    - logo/二维码(qrcode)/截图下载到 vue-fastapi-admin 静态目录
    - 默认为未发布状态（draft）
    """
    # 校验 API Key
    if x_api_key != settings.CRAWLER_API_KEY:
        return Fail(code=401, msg="无效的API Key")

    # 查询源数据（仅 we123 平台；如需扩展可增加过滤条件）
    q = Miniprogram.all().order_by("id")
    if ids:
        q = q.filter(source_id__in=ids)
    total = await q.count()
    if limit and limit > 0:
        q = q.limit(limit)

    items = await q

    created = 0
    updated = 0
    failed: list[dict] = []

    for mp in items:
        try:
            # 目标ID = source_id，确保一一对应
            target_id = mp.source_id
            if not target_id:
                continue

            # 先构造（或占位）appid/secret，满足唯一/非空约束
            auto_appid = f"wx-auto-{mp.source_platform}-{mp.source_id}"
            auto_secret = ""

            # Upsert（保持主键）
            obj = await WechatApp.filter(id=target_id).first()
            is_create = obj is None
            if is_create:
                obj = await WechatApp.create(
                    id=target_id,
                    name=mp.name or f"App-{target_id}",
                    appid=auto_appid,
                    secret=auto_secret,
                    description=mp.description or "",
                    publish_status=PublishStatus.DRAFT,
                    is_deleted=False,
                )
                created += 1
            else:
                # 更新
                # 避免 appid 冲突：如果已被人工设定，则不覆盖；否则使用占位
                if not obj.appid:
                    obj.appid = auto_appid
                obj.name = mp.name or obj.name
                obj.description = mp.description or obj.description
                obj.publish_status = PublishStatus.DRAFT  # 默认未发布
                obj.is_deleted = False
                await obj.save()
                updated += 1

            # 下载 Logo -> 存相对路径到 logo_url
            rel_logo = None
            # 优先用 Miniprogram.logo_url（远程）下载
            if mp.logo_url:
                rel_logo = _download_image(mp.logo_url, subdir="logo", filename_prefix=f"{target_id}")
            if rel_logo:
                obj.logo_url = rel_logo
                await obj.save()

            # 下载二维码(QRCode) -> 存相对路径到 qrcode_url（处理逻辑与 logo 一致）
            rel_qrcode = None
            if mp.qrcode_url:
                rel_qrcode = _download_image(mp.qrcode_url, subdir="qrcode", filename_prefix=f"{target_id}")
            if rel_qrcode:
                obj.qrcode_url = rel_qrcode
                await obj.save()

            # 下载截图到 screenshots/{id}/ 下（不入库，仅落盘提供静态访问）
            shots = await MiniprogramScreenshot.filter(miniprogram=mp).order_by("image_order").all()
            for idx, s in enumerate(shots):
                if s.image_url:
                    _download_image(s.image_url, subdir=f"screenshots/{target_id}", filename_prefix=f"{idx+1}")

        except Exception as e:
            logger.error(f"同步失败 source_id={getattr(mp, 'source_id', None)}: {e}")
            failed.append({"source_id": getattr(mp, "source_id", None), "error": str(e)})

    return Success(
        msg=f"同步完成：新增{created}，更新{updated}，失败{len(failed)} / 总计{len(items)}（源共{total}）",
        data={"created": created, "updated": updated, "failed": failed, "total": len(items)}
    )
