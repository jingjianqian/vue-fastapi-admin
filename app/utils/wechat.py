"""微信API工具类"""
import hashlib
import logging
from typing import Optional

import httpx

from app.settings.config import settings

logger = logging.getLogger(__name__)


class WechatAPIError(Exception):
    """微信API异常"""
    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"微信API错误 [{errcode}]: {errmsg}")


async def code2session(code: str, appid: Optional[str] = None) -> dict:
    """
    调用微信 code2session API 获取用户openid
    
    Args:
        code: wx.login() 返回的code
        appid: 小程序appid，不传则使用配置中的默认appid
        
    Returns:
        {
            "openid": "xxx",
            "session_key": "xxx",
            "unionid": "xxx"  # 可选
        }
        
    Raises:
        WechatAPIError: 微信API调用失败
        httpx.HTTPError: 网络请求失败
    """
    use_appid = appid or settings.WXAPP_APPID
    use_secret = settings.WXAPP_SECRET
    
    # 开发环境：如果未配置appid/secret，使用桩实现
    if not use_appid or not use_secret:
        logger.warning("未配置WXAPP_APPID或WXAPP_SECRET，使用桩实现（仅用于开发测试）")
        return _mock_code2session(code)
    
    url = settings.WX_CODE2SESSION_URL
    params = {
        "appid": use_appid,
        "secret": use_secret,
        "js_code": code,
        "grant_type": "authorization_code"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"调用微信code2session API: appid={use_appid}")
            resp = await client.get(url, params=params, timeout=settings.WX_API_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            
            # 检查微信返回的错误码
            if "errcode" in data and data["errcode"] != 0:
                errcode = data.get("errcode", -1)
                errmsg = data.get("errmsg", "未知错误")
                logger.error(f"微信code2session失败: errcode={errcode}, errmsg={errmsg}")
                raise WechatAPIError(errcode, errmsg)
            
            # 成功返回
            result = {
                "openid": data.get("openid", ""),
                "session_key": data.get("session_key", ""),
                "unionid": data.get("unionid"),
            }
            logger.info(f"微信code2session成功: openid={result['openid'][:8]}***")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"微信code2session网络请求失败: {e}")
        raise


def _mock_code2session(code: str) -> dict:
    """
    桩实现：用于开发测试
    通过hash code生成稳定的openid
    
    ⚠️ 仅用于开发测试，生产环境必须配置真实的WXAPP_APPID和WXAPP_SECRET
    """
    openid = hashlib.sha256(code.encode("utf-8")).hexdigest()[:28]
    return {
        "openid": f"mock_{openid}",
        "session_key": "mock_session_key",
        "unionid": None,
    }


async def get_access_token(appid: Optional[str] = None, secret: Optional[str] = None) -> str:
    """
    获取小程序全局access_token
    
    Args:
        appid: 小程序appid
        secret: 小程序secret
        
    Returns:
        access_token字符串
        
    Raises:
        WechatAPIError: 微信API调用失败
    """
    use_appid = appid or settings.WXAPP_APPID
    use_secret = secret or settings.WXAPP_SECRET
    
    if not use_appid or not use_secret:
        raise ValueError("必须配置WXAPP_APPID和WXAPP_SECRET")
    
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": use_appid,
        "secret": use_secret
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=settings.WX_API_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        if "errcode" in data and data["errcode"] != 0:
            raise WechatAPIError(data.get("errcode"), data.get("errmsg"))
        
        return data.get("access_token", "")


def validate_appid(appid: str) -> bool:
    """
    验证appid是否在白名单中
    
    Args:
        appid: 小程序appid
        
    Returns:
        是否在白名单
    """
    # 如果配置了默认appid，则只允许该appid
    if settings.WXAPP_APPID:
        return appid == settings.WXAPP_APPID
    
    # 未配置则允许所有（开发模式）
    return True
