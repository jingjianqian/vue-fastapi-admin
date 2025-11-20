# 小程序登录调试指南

## 前置条件

### 1. 后端服务运行中

确保后端在 9999 端口运行：

```powershell
# 在项目根目录
python run.py
```

看到以下输出表示成功：
```
2025-11-19 00:56:39 - INFO - Application startup complete.
2025-11-19 00:56:39 - INFO - Uvicorn running on http://0.0.0.0:9999
```

### 2. 检查后端 API 文档

浏览器访问：`http://localhost:9999/docs`

找到 `/api/v1/wxapp/auth/login` 接口，确认存在。

### 3. 配置信息确认

- **AppID**: `wx94e9f4328118219a`
- **AppSecret**: `69b9d30a74bb454805f6cacc2e2ed439`
- **后端地址**: `http://localhost:9999/api/v1`

## 微信开发者工具配置

### 1. 打开项目

1. 启动微信开发者工具
2. 导入项目，选择 `miniprogram` 目录
3. AppID 填写：`wx94e9f4328118219a`

### 2. 配置不校验域名

**重要**：因为是本地开发，需要关闭域名校验：

1. 点击右上角"详情"
2. 找到"本地设置"
3. 勾选：
   - ✅ **不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书**
   - ✅ **启用调试模式**

### 3. 查看网络请求

打开"调试器" → "Network"标签，可以看到所有网络请求。

## 登录流程调试

### 步骤 1：进入登录页

小程序启动后会自动检查登录状态，未登录会跳转到登录页。

### 步骤 2：点击"微信授权登录"

观察控制台输出：

```javascript
登录页加载 Object
使用 Mock 登录  // 如果看到这个，说明还是 Mock 模式
```

或者（真实模式）：

```javascript
登录页加载 Object
wx.login 调用...
```

### 步骤 3：查看网络请求

在 Network 标签查看：

**请求信息：**
- URL: `http://localhost:9999/api/v1/wxapp/auth/login`
- Method: POST
- Request Body:
  ```json
  {
    "code": "xxxxxx",
    "nickname": "",
    "avatarUrl": ""
  }
  ```

**响应信息（成功）：**
```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "username": "wx_xxxxx"
  }
}
```

### 步骤 4：检查 Storage

登录成功后，查看 Storage（调试器 → Storage → Local Storage）：

- `token`: 应该存在 JWT token
- `userInfo`: 应该存在用户信息 `{username: "wx_xxxxx"}`

## 常见问题排查

### 问题 1：请求失败 - 连接拒绝

**错误信息：**
```
request:fail url not in domain list
或
net::ERR_CONNECTION_REFUSED
```

**解决方案：**
1. 确认后端服务正在运行
2. 确认已勾选"不校验合法域名"
3. 检查 `app.js` 中的 `baseURL` 是否正确

### 问题 2：code2session 失败

**后端日志显示：**
```
微信code2session失败: errcode=40163, errmsg=code been used
```

**原因：** 微信的 code 只能使用一次

**解决方案：**
- 重新点击登录按钮获取新的 code
- 或者先用 Mock 模式调试 UI

### 问题 3：使用 Mock 登录

**现象：** 后端没配置 AppID/Secret，或想快速测试

**解决方案：** 后端会自动使用 Mock 实现

查看后端日志：
```
未配置WXAPP_APPID或WXAPP_SECRET，使用桩实现（仅用于开发测试）
```

Mock 模式下会生成假的 openid，但不影响登录流程测试。

### 问题 4：Token 存储失败

**检查：**
1. 登录是否返回了 `access_token`
2. `app.js` 中的 `setUserInfo` 方法是否正确调用
3. Storage 是否有写入权限

## 验证登录成功

登录成功后，应该：

1. ✅ 自动跳转到首页（tabBar 页面）
2. ✅ Storage 中存在 token 和 userInfo
3. ✅ 全局 `app.globalData.token` 有值
4. ✅ 后续请求会自动带上 token header

测试方法：

```javascript
// 在控制台执行
const app = getApp()
console.log('Token:', app.globalData.token)
console.log('UserInfo:', app.globalData.userInfo)
```

## 下一步

登录成功后，可以测试其他需要认证的接口：

- `/api/v1/wxapp/auth/profile` - 获取用户信息
- `/api/v1/wxapp/favorite/list` - 我的收藏
- `/api/v1/wxapp/favorite/toggle` - 收藏操作

这些接口都会自动带上 token 进行认证。

## 切换回 Mock 模式

如果需要快速调试 UI 而不依赖后端：

修改 `pages/login/login.js`：

```javascript
data: {
  useMock: true  // 改回 true
}
```

这样可以不受网络和后端限制，专注于前端开发。
