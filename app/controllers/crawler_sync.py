from __future__ import annotations

from typing import Tuple

from tortoise.expressions import Q

from app.log import logger
from app.models.wechat import WechatApp
from app.models.crawler import OdsWe123MiniProgram


async def sync_ods_to_wechat(
    only_new: bool = True,
    overwrite: bool = False,
    include_no_appid: bool = False,
    limit: int | None = 500,
) -> Tuple[int, int, int]:
    """将 ODS_We123MiniProgram 同步至 WechatApp

    返回 (created, updated, skipped)
    规则：
    - 优先使用 appid 作为唯一键，同步 name/logo/qrcode/description
    - only_new=True 时，已存在则跳过
    - overwrite=True 时，覆盖已有字段；否则仅填充为空的字段
    - include_no_appid=False 时，跳过无 appid 的记录
    - 仅同步 fetch_status='ok' 的记录
    """
    q = Q(fetch_status="ok")
    if not include_no_appid:
        q &= Q(appid__isnull=False) | Q(appid__not="")

    total = await OdsWe123MiniProgram.filter(q).count()
    qs = OdsWe123MiniProgram.filter(q).order_by("we123_id")
    if limit:
        qs = qs.limit(limit)

    created = updated = skipped = 0

    async for row in qs:
        appid = (row.appid or "").strip()
        if not appid:
            skipped += 1
            continue

        exist = await WechatApp.filter(appid=appid).first()
        if not exist:
            # 新建
            await WechatApp.create(
                name=row.name or f"we123-{row.we123_id}",
                appid=appid,
                secret="",  # ODS 无密钥，置空
                logo_url=row.logo_url or None,
                qrcode_url=row.qrcode_url or None,
                description=row.description or None,
                is_deleted=False,
            )
            created += 1
            continue

        # 已存在
        if only_new:
            skipped += 1
            continue

        # 更新策略
        def pick(dst_val, src_val):
            if overwrite:
                return src_val if src_val not in ("", None) else dst_val
            return dst_val if dst_val not in ("", None) else (src_val or dst_val)

        exist.name = pick(exist.name, row.name)
        exist.logo_url = pick(exist.logo_url, row.logo_url)
        exist.qrcode_url = pick(exist.qrcode_url, row.qrcode_url)
        exist.description = pick(exist.description, row.description)
        exist.is_deleted = False if exist.is_deleted else exist.is_deleted

        await exist.save()
        updated += 1

    logger.info(f"[ODS->Wechat] total={total} created={created} updated={updated} skipped={skipped}")
    return created, updated, skipped
