# Banner 管理使用指南

## 快速开始

### 1. 数据库初始化

运行以下脚本创建默认 Banner 记录和占位图片：

```bash
# 创建 Banner 数据库记录
python scripts/check_banners.py

# 生成默认占位图片
python scripts/create_banner_placeholders.py
```

执行后会在 `static/uploads/banners/` 目录下生成 3 张占位图片：
- `banner1.jpg` - 蓝色 "小程序导航"
- `banner2.jpg` - 红色 "精选推荐"  
- `banner3.jpg` - 绿色 "热门应用"

### 2. 更换 Banner 图片

**方式一：直接替换文件（推荐）**

1. 准备你的轮播图片（推荐尺寸：750x360 像素）
2. 将图片重命名为 `banner1.jpg`、`banner2.jpg`、`banner3.jpg`
3. 直接替换 `static/uploads/banners/` 目录下的对应文件
4. 刷新小程序即可看到新图片

**方式二：在后台管理系统上传**

1. 访问后台管理 → 系统管理 → Banner管理
2. 点击"编辑"按钮
3. 在弹出的表单中上传新图片
4. 或者直接修改 `image_url` 字段为相对路径

### 3. 在后台管理 Banner

访问：`http://your-domain/system/banner`

功能包括：
- ✅ 查看所有 Banner
- ✅ 新建 Banner
- ✅ 编辑 Banner（标题、图片、排序、跳转链接）
- ✅ 上传图片
- ✅ 上下线控制
- ✅ 删除 Banner

### 4. Banner 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| title | 字符串 | Banner 标题（用于管理识别） |
| image_url | 字符串 | 图片相对路径，如 `uploads/banners/banner1.jpg` |
| sort | 整数 | 排序号，数字越小越靠前 |
| is_online | 布尔 | 是否上线，只有上线的 Banner 才会在小程序显示 |
| jump_appid | 字符串 | 可选，点击跳转的小程序 AppID |
| jump_path | 字符串 | 可选，点击跳转的小程序页面路径 |

## 图片规范

### 推荐尺寸
- **宽度**：750px（小程序标准宽度）
- **高度**：360px（常用轮播比例）
- **比例**：约 2.08:1

### 支持格式
- JPG/JPEG
- PNG
- WebP

### 文件大小
- 建议单张不超过 500KB
- 压缩工具推荐：TinyPNG、Squoosh

## 小程序端展示

Banner 会自动在小程序首页顶部以轮播形式展示：

```javascript
// 接口：GET /api/v1/wxapp/home
{
  "code": 200,
  "data": {
    "banners": [
      {
        "id": 1,
        "image_url": "http://your-domain/static/uploads/banners/banner1.jpg",
        "title": "轮播图 1",
        "sort": 1
      },
      // ...
    ]
  }
}
```

## 常见问题

### Q: 图片不显示？
A: 检查以下几点：
1. 图片文件是否存在于 `static/uploads/banners/` 目录
2. Banner 的 `is_online` 字段是否为 `True`
3. 后端服务是否已重启（修改代码后需要重启）
4. 浏览器缓存，可以强制刷新（Ctrl+F5）

### Q: 如何添加更多 Banner？
A: 在后台管理系统点击"新建Banner"，上传图片并填写相关信息即可。

### Q: Banner 顺序如何调整？
A: 编辑 Banner，修改 `sort` 字段，数字越小越靠前。

### Q: 如何临时下线某个 Banner？
A: 编辑 Banner，关闭"上线状态"开关即可，无需删除。

## API 接口

### 后台管理接口（需要登录）

- `GET /api/v1/banner/list` - 获取 Banner 列表
- `GET /api/v1/banner/get?id=1` - 获取单个 Banner
- `POST /api/v1/banner/create` - 创建 Banner
- `POST /api/v1/banner/update` - 更新 Banner
- `DELETE /api/v1/banner/delete?id=1` - 删除 Banner
- `POST /api/v1/banner/upload` - 上传图片

### 小程序端接口（匿名可访问）

- `GET /api/v1/wxapp/home` - 首页数据（包含 banners）

## 数据库表结构

```sql
CREATE TABLE Banner (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(64),
    image_url VARCHAR(255) NOT NULL,
    app_id INT,
    jump_appid VARCHAR(64),
    jump_path VARCHAR(128),
    sort INT DEFAULT 0,
    is_online BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
);
```
