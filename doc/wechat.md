# 微信小程序端展示需求（mywechat 展示）

## 1. 背景与目标
- 将后台「小程序管理模块（doc/需求.md）」中维护的 mywechat 数据，在微信小程序端进行展示，供用户浏览、收藏并跳转。
- 小程序端采用 3 个 Tab：主页、收藏、我的；满足搜索、分类过滤、置顶、收藏、跳转等核心交互。
- 复用后端既有的鉴权与数据模型，新增面向小程序端的只读/轻写接口，并适配微信登录流程。

## 2. 术语与对象
- WechatApp（MyWechat）：后台维护的小程序实体（见 doc/需求.md 字段）。
- 分类（Category）：用于前台按类过滤展示的维度（可为新表或字典项）。
- 收藏（Favorite）：用户与 WechatApp 的关联，包含是否“常用置顶”标记。
- Banner：用于首页顶部轮播的 WechatApp 或独立素材项。

## 3. 信息架构与导航
- 底部 3 个 Tab：
  1) 首页（home）
     - 吸顶搜索（默认隐藏，向上滚动出现）
     - Banner 轮播
     - 置顶小程序（后台配置置顶或用户“常用置顶”融合）
     - 分类过滤（横向滚动/标签）
     - 小程序列表（分页 + 下拉刷新 + 上拉加载）
  2) 收藏（favorites）
     - 我收藏的小程序列表
     - 列表内支持“设为常用置顶/取消置顶”
  3) 我的（profile）
     - 使用微信公开接口获取头像/昵称
     - 一键登录/绑定，展示账号信息与收藏数

## 4. 交互与行为细则
- 搜索与吸顶：
  - 默认隐藏搜索框；当用户上滑滚动，Banner 与置顶区域收起，搜索框吸顶显示。
  - 搜索输入联动列表查询；清空后回到默认结果。
- 分类过滤：
  - 顶部展示分类标签（全部 + 多个类别），点击切换触发列表刷新；与搜索可叠加。
- 收藏：
  - 未登录点击收藏，弹出登录授权引导（WeChat 登录）；
  - 登录后可收藏/取消；收藏列表实时更新。
- 置顶：
  - 首页“置顶小程序”包含两部分：
    1) 后台配置的置顶项（可取 WechatApp.top=true）；
    2) 用户“常用置顶”的收藏项（Favorite.is_pinned=true）。
  - 收藏页内可设置/取消“常用置顶”，影响首页置顶区。
- 跳转：
  - 若 WechatApp 记录具备可跳转 appId（和 path），调用 `wx.navigateToMiniProgram` 直接跳转；
  - 否则弹出二维码大图（使用 `qrcode_url`），提示长按识别跳转（或复制 appId 提示）。
- 我的：
  - 通过 `wx.getUserProfile` 获取头像昵称（合规时机），结合 `wx.login` code 后端换取 token；
  - 登录后显示用户信息、收藏数、清理缓存、意见反馈入口（占位）。

## 5. 数据模型与变更
采用独立表建模，MyWechat 增加分类外键，Banner 独立存储展示图片与跳转信息：
- WechatApp：
  - category_id: int 外键 -> Category.id
  - is_top: bool 是否后台置顶
  - jump_path: string? 可选直跳路径
- Category：
  - id, name, icon_url?, sort
- Banner：
  - id, image_url, title?, app_id?, jump_appid?, jump_path?, sort, is_online
- Favorite：
  - id, user_id, app_id, is_pinned(bool), created_at
- User：
  - 新增绑定字段：wx_openid, wx_unionid
  - 新用户自动注册为“葡萄用户”角色（见鉴权策略）

说明：
- 跳转规则优先使用 WechatApp.appid；若缺失则使用 Banner.jump_appid；仍无则走二维码兜底。
- Banner 与 WechatApp 为松耦合：Banner 可指向某个 app（app_id），也可仅提供跳转 appid/path。

## 6. 后端接口设计（面向小程序端）
前缀：`/api/v1/wxapp`（建议与后台管理分离，权限只读为主）
- 鉴权：
  - POST `/auth/login` 通过 `code` 登录/注册/绑定，首次登录自动注册为“葡萄用户”角色，返回 `{ token, user: {id, nickname, avatar} }`
  - GET `/auth/profile` 返回当前用户信息与收藏统计
- 首页数据：
- GET `/home`
    - 入参：`category_id?`, `q?`, `page?=1`, `page_size?=10`
    - 出参：`{ banners: Banner[], top: WechatApp[], categories: Category[], list: WechatApp[], total }`
- 列表：
  - GET `/list` 同 `/home` 的列表出参（不含 banners/top/categories）
- 收藏：
  - GET `/favorite/list` → 我收藏的列表
  - POST `/favorite/toggle` → `{ app_id, value:true|false }`
  - POST `/favorite/pin` → `{ app_id, value:true|false }` （设为常用置顶）
- 元数据：
  - GET `/categories` → 分类集合
- 埋点：
  - POST `/track/event` → `{ event, payload }`；事件含：page_view、banner_click、app_expose、app_click、favorite_toggle、pin_toggle、search、category_select

字段约定（WechatApp 列表项）：
```
{
  id, name, appid, logo_url, qrcode_url, description, version,
  publish_status, category_id,
  jump_path?,
  is_top,
  is_favorited?, is_pinned?
}
```

权限与风控：
- 列表/首页匿名可读；收藏/置顶需登录。
- QPS/分页限制、图片域名白名单、防越权校验（收藏仅限本人）。

## 7. 小程序前端结构（WXML/WXSS/JS）
- pages
  - pages/home/index
    - 组件：SearchBar（吸顶隐藏/显示）、Banner、TopApps、CategoryTabs、AppList
  - pages/favorites/index
    - 组件：FavList（含置顶开关）
  - pages/profile/index
    - 组件：UserCard（头像昵称）、LoginButton、Stats
- components
  - AppCard（展示 logo、名称、描述、收藏按钮、直跳/二维码入口）
  - Empty、Skeleton、Toast、ConfirmModal
- utils
  - http（封装 `baseURL=/api/v1`，携带 header `token`）
  - auth（登录状态管理、登录引导）
  - track（埋点）
- store（全局状态）
  - userStore：`{ token, user }`
  - appStore：`{ categories, banners, topApps }`
  - favStore：`{ favorites }`

## 8. 关键流程（时序）
1) 首页首屏：
- 启动 → 调用 `/wxapp/home` → 渲染 Banner/Top/分类/列表 → 监听滚动，控制 SearchBar 显隐。

2) 收藏操作：
- 点击收藏 → 检查 `userStore.token` → 未登录触发登录 → 登录成功后 POST `/favorite/toggle` → 更新 UI。

3) 直跳/二维码：
- 点击卡片 → 若 `jump_appid` 存在 → `wx.navigateToMiniProgram({ appId: jump_appid, path: jump_path })`；
- 否则 → 弹出二维码大图，提示长按识别。

4) 微信登录：
- `wx.login` 获取 `code` → 后端 `/auth/login` 换取 `token` 与用户信息 → 存储至 userStore。

## 9. UML 设计（Mermaid）

类图：
```mermaid
classDiagram
  class WechatApp {
    +int id
    +string name
    +string appid
    +string logo_url
    +string qrcode_url
    +string description
    +string version
    +string publish_status
    +int category_id
    +bool is_top
    +string jump_path
  }
  class Category {
    +int id
    +string name
    +string icon_url
    +int sort
  }
  class Banner {
    +int id
    +string image_url
    +string title
    +int app_id
    +string jump_appid
    +string jump_path
    +int sort
    +bool is_online
  }
  class User {
    +int id
    +string nickname
    +string avatar
    +string wx_openid
    +string wx_unionid
  }
  class Favorite {
    +int id
    +int user_id
    +int app_id
    +bool is_pinned
    +datetime created_at
  }
  class Event {
    +int id
    +int user_id
    +string event
    +json payload
    +datetime created_at
  }
  User "1" -- "*" Favorite
  WechatApp "1" -- "*" Favorite
  Category "1" -- "*" WechatApp
  WechatApp "1" -- "0..*" Banner : optional link
  User "1" -- "0..*" Event
```

时序图（登录与收藏）：
```mermaid
sequenceDiagram
  participant MP as MiniProgram
  participant WX as WeChat
  participant API as Backend API
  MP->>WX: wx.login()
  WX-->>MP: code
  MP->>API: POST /wxapp/auth/login {code}
  API-->>MP: {token, user}
  MP->>API: POST /wxapp/favorite/toggle {app_id, value}
  API-->>MP: {ok}
```

时序图（点击卡片跳转）：
```mermaid
sequenceDiagram
  participant MP as MiniProgram
  MP->>MP: 点击 AppCard
  alt 有 jump_appid
    MP->>WX: wx.navigateToMiniProgram(appId, path)
  else 无 jump_appid
    MP->>MP: 弹出二维码大图，提示长按识别
  end
```

## 10. 接口定义（示例）
- POST `/api/v1/wxapp/auth/login`
```
Req: { code: string, nickname?, avatarUrl? }
Res: { token: string, user: { id, nickname, avatar } }
```
- GET `/api/v1/wxapp/home`
```
Req: { q?, category_id?, page?, page_size? }
Res: { banners: WechatApp[], top: WechatApp[], categories: Category[], list: WechatApp[], total }
```
- POST `/api/v1/wxapp/favorite/toggle`
```
Req: { app_id: number, value: boolean }
Res: { ok: true }
```
- POST `/api/v1/wxapp/favorite/pin`
```
Req: { app_id: number, value: boolean }
Res: { ok: true }
```
- POST `/api/v1/wxapp/track/event`
```
Req: { event: string, payload: object }
Res: { ok: true }
事件取值：page_view | banner_click | app_expose | app_click | favorite_toggle | pin_toggle | search | category_select
```

## 11. 非功能与兼容
- 性能：首屏 API ≤ 300ms（内网）；分页 10~20 条；图片使用 CDN/压缩图。
- 兼容：iOS/Android 主流版本；网络异常降级（空态、重试）。
- 安全：接口鉴权、越权检查、资源域名白名单、跳转白名单配置。

## 12. 验收标准
- 首页：
  - 默认隐藏搜索，滚动出现；分类可切换；Banner（独立表）/置顶/列表展示正确；点击卡片按策略直跳或二维码弹窗。
- 收藏：
  - 登录后可收藏/取消；收藏列表展示正确；可设为常用置顶并在首页置顶区生效。
- 我的：
  - 可通过微信授权登录并展示头像昵称；未注册用户自动创建为“葡萄用户”；登出后状态清理。
- 接口与埋点：
  - 面向小程序端的接口均可匿名读（除收藏相关），权限校验严谨；字段契约与本文一致。
  - 埋点事件可成功上报与查询（至少记录事件名、user_id、payload、时间）。

## 13. 参考与复用
- 可参考项目中 guide 现有实现片段（前端结构/样式/接口封装）进行复用；
- 后端沿用 JWT 与“token”头部约定，新增 `/wxapp` 命名空间只读接口与收藏写接口。

## 14. 待确认/开放问题
1. “葡萄用户”角色权限范围确认（建议仅开放 /api/v1/wxapp + 基础资料）。
2. Banner 跳转策略：仅图片展示 vs. 允许绑定 app_id / jump_appid 的优先级与校验。
3. 埋点留存与报表：是否需要聚合看板/导出，事件保留周期与脱敏策略。

## 15. 数据库与迁移方案

15.1 新增/变更的表结构（Tortoise 模型示意）

```python
# Category
class Category(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=64, unique=True)
    icon_url = fields.CharField(max_length=255, null=True)
    sort = fields.IntField(default=0)
    is_online = fields.BooleanField(default=True)
    class Meta:
        table = "Category"

# Banner（独立展示图，可指向 app 或使用 jump_appid/path）
class Banner(BaseModel, TimestampMixin):
    image_url = fields.CharField(max_length=255)
    title = fields.CharField(max_length=64, null=True)
    app = fields.ForeignKeyField("models.WechatApp", null=True, on_delete=fields.SET_NULL)
    jump_appid = fields.CharField(max_length=64, null=True)
    jump_path = fields.CharField(max_length=128, null=True)
    sort = fields.IntField(default=0)
    is_online = fields.BooleanField(default=True)
    class Meta:
        table = "Banner"

# Favorite（用户收藏与常用置顶）
class Favorite(BaseModel, TimestampMixin):
    user = fields.ForeignKeyField("models.User", on_delete=fields.CASCADE)
    app = fields.ForeignKeyField("models.WechatApp", on_delete=fields.CASCADE)
    is_pinned = fields.BooleanField(default=False)
    class Meta:
        table = "Favorite"
        unique_together = ("user_id", "app_id")

# Event（埋点）
class Event(BaseModel, TimestampMixin):
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL)
    event = fields.CharField(max_length=64)
    payload = fields.JSONField(null=True)
    class Meta:
        table = "Event"

# WechatApp 增加外键与可选跳转路径（保留表名 MyWechat）
class WechatApp(BaseModel, TimestampMixin):
    # ... 现有字段 ...
    category = fields.ForeignKeyField("models.Category", null=True, on_delete=fields.SET_NULL)
    is_top = fields.BooleanField(default=False)
    jump_path = fields.CharField(max_length=128, null=True)
    class Meta:
        table = "MyWechat"
```

15.2 迁移步骤（Aerich）
- 定义模型后执行：
  - aerich init -t app.settings.config.TORTOISE_ORM
  - aerich init-db（首次）
  - aerich migrate -m "add category/banner/favorite/event and alter MyWechat"
  - aerich upgrade
- 索引：为 Category.name、Banner.is_online、Favorite(user_id, app_id)、Event.event/created_at 建立索引。
- 回滚：aerich downgrade 可逐步回退；变更涉及外键时注意数据备份。

## 16. 后端接口契约与伪代码

16.1 命名空间与鉴权
- 前缀：/api/v1/wxapp（注册到 API 权限表，匿名 GET 放行，POST 需登录）
- 首登自动注册“葡萄用户”角色：仅授权 /wxapp 下的读写（收藏/埋点）与个人资料读取。

16.2 接口清单与请求/响应
- POST /auth/login { code, nickname?, avatarUrl? } → { token, user }
  - 逻辑：code2session → 取 openid/unionid → 绑定/创建用户（角色=葡萄用户）→ 签发 JWT（放入 header token）。
- GET /auth/profile → { user, stats: { favorites, pinned } }
- GET /home?q=&category_id=&page=1&page_size=10 → { banners: Banner[], top: App[], categories: Category[], list: App[], total }
- GET /list?q=&category_id=&page=&page_size= → { list: App[], total }
- GET /categories → Category[]
- GET /favorite/list → App[]（附 is_pinned）
- POST /favorite/toggle { app_id, value } → { ok: true }
- POST /favorite/pin { app_id, value } → { ok: true }
- POST /track/event { event, payload } → { ok: true }

16.3 伪代码片段（示意）
```python
@router.post("/auth/login")
async def mp_login(body: MpLogin):
    sess = await wechat_code2session(body.code)  # openid, unionid?
    user = await user_svc.bind_or_create_wechat(sess.openid, sess.unionid, body)
    await role_svc.ensure_granted(user, role_name="葡萄用户")
    token = jwt_issue(user)
    return Success(data={"token": token, "user": to_user_info(user)})

@router.get("/home")
async def home(q: str | None, category_id: int | None, page: int = 1, page_size: int = 10):
    categories = await Category.filter(is_online=True).order_by("sort", "id")
    banners = await Banner.filter(is_online=True).order_by("sort", "id")
    top = await WechatApp.filter(is_deleted=False, is_top=True)
    total, items = await app_svc.query_list(q, category_id, page, page_size)
    return Success(data={"categories": categories, "banners": banners, "top": top, "list": items, "total": total})

@router.post("/favorite/toggle")
@DependJwt()
async def fav_toggle(body: FavToggle, user=Depends(current_user)):
    await fav_svc.set(user.id, body.app_id, value=body.value)
    return Success(data={"ok": True})
```

16.4 权限与速率
- 收藏与置顶：需登录（JWT）；其余 GET 匿名可访问。
- 速率限制建议：基于 IP 的匿名 GET 频控、基于 user_id 的写接口频控。

## 17. 小程序前端任务拆分与里程碑

M1（D1-D2）：Schema 与迁移
- 定义 Category/Banner/Favorite/Event 模型；Aerich 迁移并验证。

M2（D3-D4）：后端 /wxapp 接口
- 实现 home/list/categories/favorite/track；完成单元验证与 API 文档。

M3（D5-D7）：前端首页与组件
- SearchBar 吸顶交互；Banner、TopApps、CategoryTabs、AppList；滚动联动与分页。

M4（D8-D9）：登录与收藏
- wx.login + /auth/login；收藏/取消与置顶；收藏页展示。

M5（D10）：埋点与可视化
- 前端埋点封装；后端落库；在管理端提供简易查询接口或导出。

M6（D11）：验收与优化
- 性能与体验优化；边界与异常处理；验收清单过测。

## 18. 埋点方案细化
- 事件：page_view、banner_click、app_expose、app_click、favorite_toggle、pin_toggle、search、category_select。
- 公共字段：ts、user_id（可空）、client(ver、os、wx_ver)、scene、page。
- payload 示例：
  - banner_click: { banner_id, pos }
  - app_click: { app_id, jump: "appid|qrcode" }
  - search: { q, category_id, result_count }
- 留存：建议 90 天；每日离线聚合 UV/PV、点击率、收藏率；脱敏导出。

## 19. 角色与权限配置
- 新建角色：葡萄用户（code: grape_user）
  - 允许：/api/v1/wxapp/**（GET），/api/v1/wxapp/favorite/**、/api/v1/wxapp/track/event（POST）
- 管理员：全量权限；
- 首登赋权：用户首次通过微信登录，自动授予葡萄用户角色。

已确认：采用上述“默认权限边界”方案实施。

## 20. 风险、回滚与测试路线
- 风险：表结构变更导致服务短暂不可用；外键约束导致删除/变更失败；
- 回滚：保留 Aerich 迁移版本；提供数据备份与恢复脚本；
- 测试：
  - 单测：fav/track/service 层；
  - 集成：/wxapp/home 与登录流程；
  - E2E：小程序真机预览（滚动吸顶、直跳/二维码、收藏、置顶、埋点）。

## 21. 示例返回（摘录）

```json
{
  "banners": [{"id":1,"image_url":"https://.../b1.png","app_id":2,"sort":1}],
  "top": [{"id":2,"name":"xxx","appid":"wx123","logo_url":"...","is_top":true}],
  "categories": [{"id":1,"name":"工具"},{"id":2,"name":"生活"}],
  "list": [{"id":3,"name":"yyy","appid":"wx456","category_id":1,"is_favorited":false}],
  "total": 20
}
```

## 22. guide 现状复用与界面方案

- 复用目录与页面：保留 pages/index（首页）、pages/favorites（收藏）、pages/my（我的）的整体框架与路由；
- 新增通用组件：
  - components/app-card：展示 logo/name/desc/收藏与常用置顶按钮；事件 tap/toggleCollect/togglePin；
  - components/qr-modal：统一二维码弹窗；参数 visible/item/imageUrl/loading；
  - components/search-bar：吸顶搜索，默认隐藏，滚动阈值出现；支持关键字输入与清空；
- 首页交互：
  - 顶部 Banner+置顶区保留（8 个/页分页）；
  - 分类横向标签与搜索可叠加过滤；
  - 列表点击直跳优先 appid，失败/缺失则二维码兜底；
  - 埋点：page_view、banner_click、app_expose、app_click、search、category_select、favorite_toggle、pin_toggle；
- 收藏页交互：
  - 我收藏列表保留；新增“常用置顶”切换并与首页置顶区联动；
  - 列表项复用 app-card；
- 我的页交互：
  - 使用 wx.login + /api/v1/wxapp/auth/login，首次自动注册“葡萄用户”；
  - 显示收藏/置顶统计；清缓存与关于入口；埋点 page_view/login_success；

## 23. API 对接与字段映射规范（前端适配层）

- 统一前缀：/api/v1/wxapp；GET 可匿名，收藏/置顶/埋点需登录；
- 统一响应：兼容 200/2000 与 data/result，前端适配为 { code:2000, result }；
- 字段对齐（列表项）：
  - id, appid, name, icon(=logo_url), desc(=description), category_id, is_top, is_favorited, is_pinned；
- 二维码接口：GET /api/v1/wxapp/qr?id= 或 appid= → { result:{ qr_code_url } }；
- 登录与存储：以 token 判定登录，openid 作为附属；authUtil 统一落 { token, user, openid }；
- 缓存与命名：为 topApps/categories/appList 设置统一 key 与版本号；
- 错误与兜底：二维码失败统一 toast；网络失败尝试缓存兜底并提示一致；
- 曝光节流：app_expose 需去重与节流；滚动侦听限频；

## 24. 改造清单与质量项（guide 代码级）

- API 路径与方法统一（如 qr_code_url GET/POST 混用、末尾斜杠不一致）；
- 字段映射清理：移除 openid 充当 appid 的做法，由适配层兼容老数据；
- 登录判断切换为 token 优先；
- 导航栏高度算法统一为 favorites 页实现；修复 index 页 3*navBarHeight 异常；
- 抽取重复逻辑：initImageUrls、loadFavoriteStatus → utils；
- 组件化：二维码弹窗合并为 qr-modal；卡片与收藏/置顶操作合并为 app-card；
- UI/UX：Skeleton 占位、加载/无更多状态、收藏成功动画；

## 25. 实施顺序（不立即落地，仅作为后续计划）

1) 统一 apiUtil 适配与字段映射；
2) 抽取 app-card/qr-modal/search-bar 并替换页面内重复代码；
3) 首页吸顶搜索、分类+搜索联动；
4) 埋点接入与节流；
5) 体验优化与代码清理；

## 26. 决议与确认（已采纳）

- 字段对齐：后端提供标准字段（见第 23 节），前端适配兼容既有返回；
- 二维码接口：统一为 GET /api/v1/wxapp/qr（参数 id 或 appid）；
- 登录与角色：前端以 token 判定登录；首次登录自动授予“葡萄用户”；
- 埋点：/api/v1/wxapp/track/event 按第 18 节与第 23 节规范接入；管理端查询后续迭代；
- 分类：/categories 返回 id/name，可在前端映射为 label/code 以兼容旧代码；
- 置顶：首页置顶区融合“后台置顶+常用置顶”，排序优先后台置顶；
- 文案：tabBar 第二项名称统一为“收藏”。

## 27. 通用组件设计约定（前端）

27.1 app-card
- Props
  - id: number
  - appid: string
  - icon: string
  - name: string
  - desc?: string
  - isCollected?: boolean
  - isPinned?: boolean
  - swipeOffset?: number
  - verified?: boolean
- Events
  - onTap: () => void
  - onToggleCollect: (id: number, value: boolean) => void
  - onTogglePin: (id: number, value: boolean) => void
- 用法示例（WXML）
```
<app-card
  id="{{item.id}}"
  appid="{{item.appid}}"
  icon="{{item.icon}}"
  name="{{item.name}}"
  desc="{{item.desc}}"
  isCollected="{{item.isCollected}}"
  isPinned="{{item.isPinned}}"
  bind:tap="handleTapItem"
  bind:toggleCollect="handleToggleCollect"
  bind:togglePin="handleTogglePin"
/>
```

27.2 qr-modal
- Props
  - visible: boolean
  - item: any
  - imageUrl?: string
  - loading?: boolean
- Events
  - onClose: () => void
  - onLoadError?: (err) => void
- 用法示例（WXML）
```
<qr-modal
  visible="{{showQrPopup}}"
  item="{{currentQrItem}}"
  imageUrl="{{qrCodeUrl}}"
  loading="{{qrCodeLoading}}"
  bind:close="hideQrCodePopup"
/>
```

27.3 search-bar（吸顶）
- Props
  - value: string
  - visible: boolean
  - placeholder?: string = "搜索小程序"
- Events
  - onInput: (val: string) => void
  - onSearch: (val: string) => void
  - onClear: () => void
- 用法示例（WXML）
```
<search-bar
  value="{{searchText}}"
  visible="{{searchVisible}}"
  bind:input="onSearchInput"
  bind:search="onSearchSubmit"
  bind:clear="onSearchClear"
/>
```

## 28. apiUtil 适配层接口与字段映射

28.1 目标
- 统一 /api/v1/wxapp 命名空间；
- 兼容 200/2000、data/result 差异，前端规范化为 { code:2000, result }；
- 字段归一：{ id, appid, name, icon, desc, category_id, is_top, is_favorited, is_pinned }。

28.2 接口草案（JS）
```
// guide/utils/api.js
const { api: BASE } = require('../util/config.js')

function normalize(res) {
  const raw = res?.data ?? res
  if (!raw) return { code: 5000, result: null, message: 'EMPTY' }
  if (raw.code === 2000 && 'result' in raw) return raw
  if (raw.code === 200 && 'data' in raw) return { code: 2000, result: raw.data }
  if ('result' in raw) return { code: 2000, result: raw.result }
  return { code: raw.code ?? 5000, result: raw.data ?? null, message: raw.message }
}

function mapWechatApp(v) {
  if (!v) return null
  return {
    id: v.id,
    appid: v.appid || v.openid || '',
    name: v.name,
    icon: v.icon || v.logo_url || '',
    desc: v.desc || v.description || v.short_desc || '',
    category_id: v.category_id ?? null,
    is_top: !!v.is_top,
    is_favorited: !!v.is_favorited,
    is_pinned: !!v.is_pinned,
  }
}

function get(url, params = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE + url,
      method: 'GET',
      data: params,
      header: { token: wx.getStorageSync('token') || '' },
      success: (res) => resolve(normalize(res)),
      fail: reject,
    })
  })
}

function post(url, data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE + url,
      method: 'POST',
      data,
      header: { 'content-type': 'application/json', token: wx.getStorageSync('token') || '' },
      success: (res) => resolve(normalize(res)),
      fail: reject,
    })
  })
}

module.exports = {
  login: (code, nickname, avatarUrl) =>
    post('api/v1/wxapp/auth/login', { code, nickname, avatarUrl }),

  getHome: (params) => get('api/v1/wxapp/home', params),
  getList: (params) => get('api/v1/wxapp/list', params),
  getCategories: () => get('api/v1/wxapp/categories'),
  getFavorites: (page = 1, page_size = 10, category_id) =>
    get('api/v1/wxapp/favorite/list', { page, page_size, category_id }),

  toggleFavorite: (app_id, value) =>
    post('api/v1/wxapp/favorite/toggle', { app_id, value }),

  pinFavorite: (app_id, value) =>
    post('api/v1/wxapp/favorite/pin', { app_id, value }),

  getQr: ({ id, appid }) =>
    get('api/v1/wxapp/qr', { id, appid }),

  track: (event, payload = {}) =>
    post('api/v1/wxapp/track/event', { event, payload }),

  mapWechatApp,
}
```

28.3 字段映射约束
- 列表项统一：{ id, appid, name, icon, desc, category_id, is_top, is_favorited, is_pinned }；
- 页面消费前一律 mapWechatApp 归一化。

## 29. 逐文件改造清单（设计，不立即落地）

29.1 guide/pages/index/index.js
- 导航栏高度：用 favorites 页算法（menuButton.bottom - statusBarHeight）。
- Data：新增 searchVisible、searchText；
- 分类：apiUtil.getCategories → 前端映射 {id,label:name,code:id}；
- 列表：apiUtil.getList({ q, category_id, page, page_size }) 并 mapWechatApp；
- 收藏/置顶：toggleFavorite/pinFavorite；
- 二维码：apiUtil.getQr({ id 或 appid })，UI 用 qr-modal；
- 跳转：优先 appid，失败弹二维码；
- 埋点：page_view、banner_click、app_expose（去重节流）、app_click、search、category_select、favorite_toggle、pin_toggle。

29.2 guide/pages/index/index.wxml
- nav-bar 下插入 <search-bar ...>；
- scroll-view 绑定 scroll 控制吸顶显示；
- 列表项替换为 <app-card ...>；
- 弹窗替换为 <qr-modal ...>。

29.3 guide/pages/favorites/index.js
- getFavorites → mapWechatApp；
- 收藏：toggleFavorite；常用置顶：pinFavorite；
- 二维码：统一 apiUtil.getQr + qr-modal；
- 登录：以 token 判定；
- 埋点：page_view、favorite_toggle、pin_toggle、app_click。

29.4 guide/pages/my/index.js
- 登录：wx.login → apiUtil.login，落 { token,user,openid }；
- 统计：展示收藏/置顶数（/auth/profile 或汇总）；
- 埋点：page_view、login_success。

29.5 guide/app.json
- tabBar 第二项文案改为“收藏”（如需）。

29.6 guide/utils
- api.js：按 28 节实现；
- favorite.js（如有）：仅保留状态合并工具，接口统一走 api.js；
- image.js：保留 getImageUrl，提供防缓存参数；
- track.js（可选）：封装批量上报、节流与重试。

29.7 guide/components
- 新增 app-card、qr-modal、search-bar；
- 将现有重复卡片/二维码/搜索 UI 抽离替换。
