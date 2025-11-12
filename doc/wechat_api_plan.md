# 小程序数据查询接口封装规划与建议

## 一、Key与Secret配置化方案

### 1.1 现状分析
- 当前 `WechatApp` 模型中 `secret` 字段直接存储在数据库表 `MyWechat` 中
- 小程序接口未使用 appid/secret 进行鉴权验证
- 缺少统一的配置管理机制

### 1.2 配置化方案设计

#### 方案A：独立配置文件（推荐）
```python
# app/settings/wechat_config.py
from pydantic import BaseModel
from typing import Optional

class WechatConfig(BaseModel):
    # 小程序配置
    WXAPP_APPID: str = ""
    WXAPP_SECRET: str = ""
    
    # 微信开放平台配置（用于 code2session）
    WX_OPEN_APPID: Optional[str] = None
    WX_OPEN_SECRET: Optional[str] = None
    
    # 接口安全配置
    WXAPP_API_KEY: str = ""  # 小程序调用后端接口的密钥
    WXAPP_API_SECRET: str = ""  # 小程序接口签名密钥
    
    # 频率限制
    WXAPP_RATE_LIMIT_PER_MINUTE: int = 60
    WXAPP_RATE_LIMIT_PER_HOUR: int = 1000

wechat_config = WechatConfig()
```

#### 方案B：环境变量（安全性更高）
```bash
# .env
WXAPP_APPID=wx1234567890abcdef
WXAPP_SECRET=your_secret_here
WXAPP_API_KEY=your_api_key
WXAPP_API_SECRET=your_api_secret
```

```python
# app/settings/config.py 添加
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 小程序配置
    WXAPP_APPID: str = ""
    WXAPP_SECRET: str = ""
    WXAPP_API_KEY: str = ""
    WXAPP_API_SECRET: str = ""
    
    class Config:
        env_file = ".env"
```

### 1.3 建议采用方案
**推荐：方案B（环境变量）+ 数据库配置结合**
- 敏感信息（secret、key）使用环境变量
- 业务配置（多个小程序管理）使用数据库
- 支持多租户场景

## 二、接口对应情况核实

### 2.1 当前已实现接口清单

| 接口路径 | 方法 | 功能 | 鉴权 | 状态 |
|---------|------|------|------|------|
| `/api/v1/wxapp/auth/login` | POST | 登录（code2session桩） | 否 | ✅ 已实现 |
| `/api/v1/wxapp/home` | GET | 首页聚合数据 | 否 | ✅ 已实现 |
| `/api/v1/wxapp/list` | GET | 小程序列表 | 否 | ✅ 已实现 |
| `/api/v1/wxapp/categories` | GET | 分类列表 | 否 | ✅ 已实现 |
| `/api/v1/wxapp/favorite/list` | GET | 我的收藏 | 是 | ✅ 已实现 |
| `/api/v1/wxapp/favorite/toggle` | POST | 收藏/取消 | 是 | ✅ 已实现 |
| `/api/v1/wxapp/favorite/pin` | POST | 置顶/取消置顶 | 是 | ✅ 已实现 |
| `/api/v1/wxapp/qr` | GET | 获取二维码 | 否 | ✅ 已实现 |
| `/api/v1/wxapp/track/event` | POST | 埋点上报 | 是 | ✅ 已实现 |

### 2.2 缺失接口分析

#### 需要补充的接口：

1. **用户信息接口**
   - `GET /api/v1/wxapp/auth/profile` - 获取当前用户信息
   - 状态：❌ 未实现

2. **真实的微信登录**
   - 当前使用 `code2session` 桩实现（hash code 生成 openid）
   - 生产环境需要调用微信官方 API
   - 状态：⚠️ 需要改进

3. **小程序详情接口**
   - `GET /api/v1/wxapp/detail/{id}` - 获取单个小程序详细信息
   - 状态：❌ 未实现

4. **Banner管理接口**
   - 当前在 `/home` 接口中返回，但缺少单独的管理接口
   - 状态：✅ 功能已覆盖（通过home接口）

### 2.3 接口完整度评估
- **核心功能覆盖率**: 90%
- **生产就绪度**: 60%（缺少真实微信登录和安全机制）

## 三、登录与数据权限逻辑设计

### 3.1 登录流程设计

#### 当前实现（桩版本）
```
小程序端 -> wx.login() -> code
         -> POST /api/v1/wxapp/auth/login {code}
         -> 后端: hash(code) -> openid
         -> 创建/查找用户
         -> 授予"葡萄用户"角色
         -> 返回 JWT token
```

#### 生产版本设计
```
小程序端 -> wx.login() -> code
         -> POST /api/v1/wxapp/auth/login {code, appid}
         -> 后端: 验证 appid 是否在白名单
         -> 调用微信 API: code2Session
         -> 获取 openid, session_key, unionid
         -> 创建/更新用户（绑定 wx_openid, wx_unionid）
         -> 授予"葡萄用户"角色
         -> 返回 JWT token
```

#### 实现代码示例
```python
# app/utils/wechat.py
import httpx
from app.settings import settings

async def code2session(code: str, appid: str) -> dict:
    """调用微信 code2session API"""
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": appid or settings.WXAPP_APPID,
        "secret": settings.WXAPP_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
        data = resp.json()
        if "errcode" in data and data["errcode"] != 0:
            raise ValueError(f"微信登录失败: {data.get('errmsg')}")
        return {
            "openid": data.get("openid"),
            "session_key": data.get("session_key"),
            "unionid": data.get("unionid"),
        }
```

### 3.2 权限模型设计

#### 角色定义
| 角色名称 | 角色代码 | 权限范围 |
|---------|---------|---------|
| 葡萄用户 | grape_user | 小程序端只读 + 收藏/置顶/埋点 |
| 管理员 | admin | 后台全部管理权限 |
| 超级管理员 | superuser | 系统全部权限 |

#### 权限清单（葡萄用户）
```python
GRAPE_USER_PERMISSIONS = {
    # 允许的端点
    "allowed_endpoints": [
        "/api/v1/wxapp/home",
        "/api/v1/wxapp/list",
        "/api/v1/wxapp/categories",
        "/api/v1/wxapp/qr",
        "/api/v1/wxapp/detail/*",
        "/api/v1/wxapp/auth/profile",
        "/api/v1/wxapp/favorite/*",
        "/api/v1/wxapp/track/event",
    ],
    # 禁止访问的端点
    "denied_endpoints": [
        "/api/v1/wechat/*",  # 后台管理接口
        "/api/v1/users/*",
        "/api/v1/roles/*",
        "/api/v1/menus/*",
    ]
}
```

### 3.3 数据权限策略

#### 读权限
- **匿名用户**: 可访问 home, list, categories, qr（公开数据）
- **登录用户**: 在匿名基础上 + 收藏状态、置顶状态
- **管理员**: 全部数据 + 敏感字段（secret、is_deleted=True的记录）

#### 写权限
- **匿名用户**: 无写权限
- **登录用户（葡萄用户）**: 
  - 可写: 自己的收藏、置顶、埋点数据
  - 不可写: 其他用户数据、小程序信息、分类、Banner
- **管理员**: 全部写权限

#### 数据隔离实现
```python
# 收藏接口自动过滤当前用户
async def favorite_list(current_user=DependAuth):
    # 自动限制为当前用户的收藏
    favs = await Favorite.filter(user_id=current_user.id)
    # 防止越权查询他人收藏
```

### 3.4 安全增强建议

#### 1. 请求签名验证（可选，高安全场景）
```python
# 小程序端生成签名
timestamp = Date.now()
sign = md5(appid + timestamp + api_secret)
headers = {
    "X-Wxapp-Appid": appid,
    "X-Wxapp-Timestamp": timestamp,
    "X-Wxapp-Sign": sign,
    "token": token
}
```

#### 2. Token刷新机制
```python
# 当前token过期时间: 7天
# 建议: 访问token 2小时 + 刷新token 7天
@router.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    # 验证刷新token
    # 颁发新的访问token
    pass
```

#### 3. 设备指纹（防刷机制）
```python
# 记录设备信息，限制单设备登录数量
class UserDevice(BaseModel):
    user_id: int
    device_id: str  # 小程序生成的唯一设备ID
    last_login_at: datetime
```

## 四、其他潜在问题与建议

### 4.1 数据库迁移问题

#### 问题1: Category、Banner、Favorite、Event 表未创建
- **现象**: 代码中已定义模型，但数据库表可能未迁移
- **影响**: 接口调用时捕获异常返回空数据
- **解决**: 执行 Aerich 迁移

```bash
# 生成迁移文件
aerich migrate -m "add wxapp extra tables"

# 执行迁移
aerich upgrade
```

#### 问题2: User 表缺少 wx_openid 和 wx_unionid 字段
- **现状**: User模型未包含微信绑定字段
- **影响**: 无法正确关联微信用户
- **建议**: 添加字段

```python
# app/models/admin.py - User 模型添加
class User(BaseModel, TimestampMixin):
    # ... 现有字段 ...
    wx_openid = fields.CharField(max_length=64, null=True, unique=True, index=True, description="微信OpenID")
    wx_unionid = fields.CharField(max_length=64, null=True, index=True, description="微信UnionID")
```

### 4.2 性能优化建议

#### 1. 收藏状态批量查询优化
当前实现问题: `/home` 接口返回列表时，`is_favorited` 和 `is_pinned` 固定为 False

**优化方案**:
```python
async def home(current_user=DependAuth):
    # ... 查询列表 ...
    
    # 如果用户已登录，批量查询收藏状态
    if current_user:
        app_ids = [item["id"] for item in items]
        favs = await Favorite.filter(user_id=current_user.id, app_id__in=app_ids)
        fav_map = {f.app_id: f for f in favs}
        
        for item in items:
            fav = fav_map.get(item["id"])
            if fav:
                item["is_favorited"] = True
                item["is_pinned"] = fav.is_pinned
```

#### 2. 分类/Banner 缓存
```python
from functools import lru_cache
from datetime import datetime, timedelta

# 简单内存缓存（5分钟）
_category_cache = {"data": None, "expire": None}

async def get_categories_cached():
    now = datetime.now()
    if _category_cache["data"] and _category_cache["expire"] > now:
        return _category_cache["data"]
    
    cats = await Category.filter(is_online=True).order_by("sort", "id")
    data = [{"id": c.id, "name": c.name, "icon_url": c.icon_url} for c in cats]
    _category_cache["data"] = data
    _category_cache["expire"] = now + timedelta(minutes=5)
    return data
```

#### 3. 数据库索引检查
```python
# 确保以下字段有索引
WechatApp:
  - appid (unique, index) ✅
  - name (index) ✅
  - category_id (index) ❌ 需要添加
  - is_deleted (index) ✅
  - is_top (index) ❌ 需要添加

Favorite:
  - (user_id, app_id) unique_together ✅
  - user_id (index) ❌ 需要添加

Event:
  - user_id (index) ❌ 需要添加
  - event (index) ❌ 需要添加
  - created_at (index) ❌ 需要添加
```

### 4.3 API响应格式统一

#### 问题: 返回格式不一致
- `/home` 返回: `{code: 2000, data: {...}}`
- 前端期望: `{code: 2000, result: {...}}`

**建议**: 统一为 `result` 字段，与文档保持一致
```python
# app/schemas/base.py 修改
class Success(BaseModel):
    code: int = 2000
    result: Any = None  # 改为 result
    msg: str = "Success"
```

### 4.4 错误处理完善

#### 当前问题
```python
except Exception:
    return Success(data=[])  # 隐藏了错误信息
```

**改进建议**:
```python
import logging
logger = logging.getLogger(__name__)

except Exception as e:
    logger.error(f"查询分类失败: {e}", exc_info=True)
    if settings.DEBUG:
        return Fail(code=500, msg=str(e))
    return Success(data=[])  # 生产环境降级
```

### 4.5 频率限制（防刷）

#### 建议使用中间件
```python
# app/core/middlewares.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limit=60):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.requests = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/wxapp"):
            # 根据 IP 或 token 限流
            client_id = request.client.host
            now = datetime.now()
            
            # 清理过期记录
            self.requests[client_id] = [
                t for t in self.requests[client_id]
                if now - t < timedelta(minutes=1)
            ]
            
            if len(self.requests[client_id]) >= self.rate_limit:
                return JSONResponse(
                    status_code=429,
                    content={"code": 429, "msg": "请求过于频繁"}
                )
            
            self.requests[client_id].append(now)
        
        response = await call_next(request)
        return response
```

### 4.6 日志与监控

#### 建议添加访问日志
```python
# 在 wxapp.py 各接口添加日志
import logging
logger = logging.getLogger(__name__)

@router.get("/home")
async def home(...):
    logger.info(f"wxapp.home called: q={q}, category_id={category_id}, page={page}")
    # ...
```

#### 埋点数据分析接口（管理端）
```python
# app/api/v1/admin/analytics.py
@router.get("/wxapp/analytics/events")
async def event_analytics(
    event: str = Query(None),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
):
    """埋点数据统计（仅管理员）"""
    qexp = Q()
    if event:
        qexp &= Q(event=event)
    if start_date:
        qexp &= Q(created_at__gte=start_date)
    if end_date:
        qexp &= Q(created_at__lte=end_date)
    
    events = await Event.filter(qexp).order_by("-created_at").limit(1000)
    # 聚合统计
    stats = {}
    for e in events:
        stats[e.event] = stats.get(e.event, 0) + 1
    
    return Success(data={"stats": stats, "events": events})
```

### 4.7 测试覆盖

#### 建议添加测试用例
```python
# tests/test_wxapp.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_home_anonymous(client: AsyncClient):
    """测试匿名访问首页"""
    resp = await client.get("/api/v1/wxapp/home")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data or "result" in data

@pytest.mark.asyncio
async def test_favorite_require_auth(client: AsyncClient):
    """测试收藏需要登录"""
    resp = await client.post("/api/v1/wxapp/favorite/toggle", json={"app_id": 1, "value": True})
    assert resp.status_code == 401 or resp.status_code == 403
```

### 4.8 文档与API规范

#### OpenAPI 文档完善
```python
@router.get(
    "/home",
    summary="首页聚合数据",
    description="""
    获取小程序首页所需的全部数据，包括：
    - banners: 轮播图列表
    - top: 置顶小程序列表（后台配置 + 用户常用）
    - categories: 分类列表
    - list: 小程序列表（支持搜索、分类过滤、分页）
    - total: 总数
    """,
    response_description="首页数据",
    tags=["小程序端接口"],
)
async def home(...):
    pass
```

## 五、实施优先级建议

### P0 - 必须完成（阻塞上线）
1. ✅ Key/Secret 配置化（环境变量）
2. ❌ 真实微信登录实现（code2session API调用）
3. ❌ User表添加 wx_openid/wx_unionid 字段
4. ❌ 数据库迁移（Category、Banner、Favorite、Event表）
5. ❌ 收藏状态批量查询优化（/home接口）

### P1 - 应该完成（影响体验）
6. ❌ 添加 `/auth/profile` 接口
7. ❌ 添加 `/detail/{id}` 接口
8. ❌ 响应格式统一（result字段）
9. ❌ 错误处理完善（日志记录）
10. ❌ 频率限制中间件

### P2 - 可以推迟（优化项）
11. ❌ 缓存机制（分类/Banner）
12. ❌ 数据库索引优化
13. ❌ Token刷新机制
14. ❌ 埋点数据分析接口
15. ❌ 测试用例覆盖

### P3 - 长期规划
16. ❌ 设备指纹防刷
17. ❌ 请求签名验证
18. ❌ 监控告警系统
19. ❌ API文档完善

## 六、总结

### 当前完成度
- ✅ 核心接口已实现（9个接口）
- ⚠️ 使用桩实现（非真实微信登录）
- ❌ 配置未分离（secret硬编码在数据库）
- ❌ 部分表未迁移（可能影响功能）
- ⚠️ 性能优化不足（收藏状态查询）
- ❌ 缺少安全机制（频率限制、签名验证）

### 预计工作量
- P0任务: 2-3工作日
- P1任务: 2工作日
- P2任务: 3工作日
- P3任务: 5+工作日

**总计**: 约12-15工作日可达到生产就绪状态

### 风险评估
1. **高风险**: 数据库迁移可能影响现有数据
2. **中风险**: 微信API调用失败处理
3. **低风险**: 性能优化和缓存实现

### 建议行动
1. 立即执行P0任务（阻塞上线）
2. 并行进行P1任务（提升体验）
3. 根据实际负载情况决定P2/P3任务优先级
