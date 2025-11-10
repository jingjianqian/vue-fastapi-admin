from typing import Optional

from app.core.crud import CRUDBase
from app.models.wechat import WechatApp
from app.schemas.wechat import WechatCreate, WechatUpdate, PublishStatus


class WechatController(CRUDBase[WechatApp, WechatCreate, WechatUpdate]):
    def __init__(self):
        super().__init__(model=WechatApp)

    async def get_by_appid(self, appid: str) -> Optional[WechatApp]:
        return await self.model.filter(appid=appid).first()

    async def set_logo(self, id: int, url: str):
        obj = await self.get(id=id)
        obj.logo_url = url
        await obj.save()
        return obj

    async def set_qrcode(self, id: int, url: str):
        obj = await self.get(id=id)
        obj.qrcode_url = url
        await obj.save()
        return obj

    async def set_status(self, id: int, status: PublishStatus):
        obj = await self.get(id=id)
        obj.publish_status = status
        await obj.save()
        return obj


wechat_controller = WechatController()