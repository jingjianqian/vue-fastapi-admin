from typing import Optional

from app.core.crud import CRUDBase
from app.models.wechat import WechatApp
from app.schemas.wechat import WechatCreate, WechatUpdate, PublishStatus
from app.utils.file import convert_to_absolute_path


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

    async def restore(self, id: int):
        """恢复已删除的记录"""
        obj = await self.get(id=id)
        obj.is_deleted = False
        await obj.save()
        return obj

    async def get_logo_absolute_path(self, id: int) -> str | None:
        """
        获取小程序logo的绝对路径
        
        用于上传到微信平台或其他需要本地文件绝对路径的操作
        
        Args:
            id: 小程序主键id
            
        Returns:
            logo的绝对路径，如果不存在则返回 None
        """
        obj = await self.get(id=id)
        return convert_to_absolute_path(obj.logo_url)

    async def get_qrcode_absolute_path(self, id: int) -> str | None:
        """
        获取小程序二维码的绝对路径
        
        用于上传到微信平台或其他需要本地文件绝对路径的操作
        
        Args:
            id: 小程序主键id
            
        Returns:
            二维码的绝对路径，如果不存在则返回 None
        """
        obj = await self.get(id=id)
        return convert_to_absolute_path(obj.qrcode_url)


wechat_controller = WechatController()