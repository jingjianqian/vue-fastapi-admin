# 葡萄小程序

基于微信小程序原生框架开发的小程序应用，对接后端 FastAPI 接口。

## 项目结构

```
miniprogram/
├── pages/              # 页面目录
│   ├── home/          # 首页
│   ├── login/         # 登录页
│   ├── detail/        # 详情页
│   ├── favorite/      # 收藏页
│   └── profile/       # 个人中心
├── components/        # 组件目录
├── utils/            # 工具类
│   └── request.js    # 统一请求封装
├── api/              # API接口
│   └── index.js      # 接口定义
├── assets/           # 静态资源
├── app.js            # 小程序入口
├── app.json          # 全局配置
├── app.wxss          # 全局样式
├── project.config.json  # 项目配置
└── sitemap.json      # 索引配置
```

## 功能特性

- ✅ 统一的后端接口请求封装
- ✅ Token 认证机制（符合 PC 端规范）
- ✅ Mock 数据模式（便于开发调试）
- ✅ 页面路由配置（首页、详情、收藏、我的）
- ✅ 微信登录集成
- ✅ 全局样式和布局

## 快速开始

### 1. 开发工具

下载并安装[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)

### 2. 导入项目

1. 打开微信开发者工具
2. 选择"小程序" → "导入项目"
3. 选择 `miniprogram` 目录
4. AppID 使用测试号或配置的 AppID: `wx94e9f4328118219a`

### 3. 配置后端地址

修改 `app.js` 中的 `baseURL`:

```javascript
globalData: {
  baseURL: 'http://localhost:9999/api/v1' // 改为实际后端地址
}
```

### 4. Mock 模式

当前所有页面默认使用 Mock 数据，无需后端接口即可调试 UI。

**切换到真实接口模式：**

在各页面的 `.js` 文件中，将 `useMock: true` 改为 `useMock: false`：

```javascript
// pages/home/home.js
data: {
  useMock: false  // 改为 false 使用真实接口
}
```

## API 接口

### 认证相关

- `POST /wxapp/auth/login` - 小程序登录
  - 请求：`{ code, nickname, avatarUrl }`
  - 响应：`{ access_token, username }`

- `GET /wxapp/auth/profile` - 获取用户信息（需登录）

### 小程序相关

- `GET /wxapp/home` - 首页数据（横幅、分类、置顶、列表）
- `GET /wxapp/list` - 小程序列表
- `GET /wxapp/detail/:id` - 小程序详情
- `GET /wxapp/categories` - 分类列表

### 收藏相关（需登录）

- `GET /wxapp/favorite/list` - 我的收藏列表
- `POST /wxapp/favorite/toggle` - 收藏/取消收藏
- `POST /wxapp/favorite/pin` - 设为常用/取消常用

## Token 认证

与 PC 端保持一致的认证方式：

1. 登录后获取 `access_token`
2. 存储到本地缓存和全局状态
3. 后续请求通过 `header: token` 传递
4. Token 过期自动跳转登录页

## 页面说明

### 首页 (home)
- 搜索栏
- 横幅 Banner（轮播）
- 分类导航（横向滚动）
- 置顶小程序（网格布局）
- 小程序列表（列表布局）

### 登录页 (login)
- 微信授权登录按钮
- Mock 模式：模拟登录成功
- 真实模式：调用 `wx.login` + 后端接口

### 详情页 (detail)
- 小程序基本信息
- 打开小程序按钮
- 收藏/取消收藏
- 小程序码展示

### 收藏页 (favorite)
- 我的收藏列表
- 跳转详情页

### 个人中心 (profile)
- 用户信息展示
- 我的收藏入口
- 退出登录

## 开发建议

### 开发流程

1. **先用 Mock 数据调试 UI**
   - 所有页面默认 Mock 模式
   - 快速验证页面布局和交互

2. **后端接口开发完成后切换真实接口**
   - 将各页面的 `useMock` 改为 `false`
   - 配置正确的 `baseURL`

3. **真机调试**
   - 配置服务器域名白名单
   - 使用真实 AppID 和 Secret

### 注意事项

- **域名配置**：小程序正式版需要在微信公众平台配置合法域名
- **HTTPS**：正式环境后端必须使用 HTTPS
- **Token 存储**：使用 `wx.setStorageSync` 存储，注意安全
- **请求封装**：所有接口统一通过 `utils/request.js` 调用

## 下一步

- [ ] 添加更多通用组件（加载、空状态、错误提示）
- [ ] 对接真实后端接口
- [ ] 添加埋点统计
- [ ] 完善错误处理
- [ ] 性能优化
- [ ] 提交审核发布

## 技术支持

如有问题，请查看：
- [微信小程序官方文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [FastAPI 后端接口文档](../app/api/v1/wxapp/)
