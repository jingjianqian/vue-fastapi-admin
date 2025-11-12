# DrissionPage 4.x API 使用总结

## 版本信息
- DrissionPage: 4.x
- Python: 3.11

## 1. 正确的初始化方式

### ❌ 错误用法
```python
co = ChromiumOptions().headless(True)  # headless()返回self,但参数不对
page = ChromiumPage(co)  # 参数名不对
```

### ✅ 正确用法
```python
from DrissionPage import ChromiumOptions, ChromiumPage

# 方式1: 使用ChromiumOptions
co = ChromiumOptions()
co.headless()  # 或 co.headless(True)，设置无头模式
co.set_user_agent("custom ua")  # 设置UA
co.set_proxy("http://host:port")  # 设置代理
page = ChromiumPage(addr_or_opts=co)

# 方式2: 直接初始化
page = ChromiumPage()
```

## 2. 元素选择

### ✅ 正确的API
```python
# 获取单个元素 (index从1开始)
element = page.ele(locator, index=1, timeout=None)

# 获取多个元素列表
elements = page.eles(locator, timeout=None)

# locator可以是:
# - XPath: 'xpath://div[@class="test"]' 或 '//div[@class="test"]'
# - CSS: 'css:.class' 或 '.class'
# - 文本: 'text:搜索文字'
# - Tag: 'tag:div'
```

## 3. 获取文本和属性

### ✅ 正确用法
```python
# 获取文本
text = element.text

# 获取单个属性
src = element.attr('src')
href = element.attr('href')
class_name = element.attr('class')

# 获取所有属性(返回字典)
all_attrs = element.attrs
```

## 4. XPath的重要注意事项

### ❌ 错误: XPath直接选择属性
```python
# XPath如果写成 /@src，会直接返回属性值字符串，不是元素对象
xpath = "//img/@src"
result = page.eles(xpath)  # 返回字符串列表，不是元素列表
# 无法对字符串调用 .attr() 方法！
```

### ✅ 正确: 先选择元素，再获取属性
```python
# 方式1: 选择元素，然后获取属性
xpath = "//img"
elements = page.eles(xpath)
for ele in elements:
    src = ele.attr('src')  # 正确

# 方式2: 如果只需要属性值，可以用JS
srcs = page.run_js('return Array.from(document.querySelectorAll("img")).map(e=>e.src);')
```

## 5. 页面等待

### ✅ 等待页面加载
```python
# 访问页面
page.get(url)

# 等待文档加载完成
page.wait.doc_loaded()

# 等待特定元素出现
element = page.ele('xpath://div[@id="content"]', timeout=10)

# 等待元素加载
page.wait.ele_loaded('xpath://div[@id="content"]', timeout=10)
```

## 6. 代码修复要点

### we123_xcx.py 需要修复的地方

#### 1. 初始化部分 (138-146行)
```python
# ❌ 当前错误代码
co = ChromiumOptions().headless(True)
page = ChromiumPage(co)

# ✅ 正确代码
co = ChromiumOptions()
co.headless()
if self.cfg.ua:
    co.set_user_agent(self.cfg.ua)
if self.cfg.proxy:
    co.set_proxy(self.cfg.proxy)
page = ChromiumPage(addr_or_opts=co)
```

#### 2. 页面加载 (171行)
```python
# ❌ 当前代码
page.get(base_url)
data = self._extract_with_xpaths(page, cur_id, base_url)

# ✅ 改进代码
page.get(base_url)
# 等待页面主要内容加载
try:
    page.wait.doc_loaded()
    # 等待关键元素出现(可选)
    # page.wait.ele_loaded('xpath://h1', timeout=5)
except:
    pass
data = self._extract_with_xpaths(page, cur_id, base_url)
```

#### 3. XPath选择器修正 (206-234行)

**❌ 当前错误逻辑:**
```python
def _attr_list(xp: str) -> list[str]:
    eles = page.eles(xp=xp)  # API错误，应该是 page.eles(xp)
    for e in eles:
        v = e.attr("src") if "@src" in xp else e.attr("href")  # 逻辑错误
```

**✅ 正确逻辑:**
```python
def _text_list(xp: str) -> list[str]:
    try:
        eles = page.eles(xp)  # 不是 xp=xp
        vals = []
        for e in eles:
            if hasattr(e, 'text') and e.text:
                vals.append(e.text.strip())
        return vals
    except Exception:
        return []

def _text_one(xp: str) -> Optional[str]:
    arr = _text_list(xp)
    return arr[0] if arr else None

def _attr_list(xp: str, attr_name: str) -> list[str]:
    """
    获取元素属性列表
    :param xp: XPath，选择元素（不要包含/@attr）
    :param attr_name: 属性名，如 'src', 'href'
    """
    try:
        eles = page.eles(xp)
        out = []
        for e in eles:
            if hasattr(e, 'attr'):
                v = e.attr(attr_name)
                if v and isinstance(v, str):
                    out.append(v)
        return out
    except Exception:
        return []
```

#### 4. XPath配置修正 (24-38行)

**❌ 当前配置（会导致问题）:**
```python
DEFAULT_XPATHS = {
    "icon_url": "//img[contains(@class,'logo')]/@src",  # /@src会返回字符串
    "screenshot_urls": "//div[contains(@class,'screenshots')]//img/@src",
}
```

**✅ 正确配置:**
```python
DEFAULT_XPATHS = {
    # 文本选择器: 选择到元素，用 .text 获取
    "name": "//h1[contains(@class,'xcx')]",
    "category": "//a[contains(@href,'/xcxcat/')]",
    "tags": "//div[contains(@class,'tags')]//a",
    "desc": "//div[contains(@class,'desc')]",
    
    # 属性选择器: 选择到元素，用 .attr('src') 获取
    "icon_img": "//img[contains(@class,'logo')]",  # 选择元素
    "qrcode_img": "//img[contains(@alt,'小程序码')]",
    "screenshot_imgs": "//div[contains(@class,'screenshots')]//img",
    
    # 其他
    "developer": "//li[contains(.,'开发者')]/span",
    "rating": "//span[contains(@class,'rating')]",
    "version": "//li[contains(.,'版本')]/span",
    "updated_at_src": "//li[contains(.,'更新')]/span",
}
```

## 7. 完整修复示例

```python
def _extract_with_xpaths(self, page, src_id: int, url: str) -> Dict[str, Any]:
    """提取页面数据"""
    
    def _text_one(xp: str) -> Optional[str]:
        try:
            ele = page.ele(xp, timeout=2)
            return ele.text.strip() if ele and ele.text else None
        except:
            return None
    
    def _text_list(xp: str) -> list[str]:
        try:
            eles = page.eles(xp, timeout=2)
            return [e.text.strip() for e in eles if e and e.text and e.text.strip()]
        except:
            return []
    
    def _attr_one(xp: str, attr: str) -> Optional[str]:
        try:
            ele = page.ele(xp, timeout=2)
            return ele.attr(attr) if ele else None
        except:
            return None
    
    def _attr_list(xp: str, attr: str) -> list[str]:
        try:
            eles = page.eles(xp, timeout=2)
            return [e.attr(attr) for e in eles if e and e.attr(attr)]
        except:
            return []
    
    x = self.xpaths
    name = _text_one(x.get("name", DEFAULT_XPATHS["name"]))
    category = _text_one(x.get("category", DEFAULT_XPATHS["category"]))
    tags = _text_list(x.get("tags", DEFAULT_XPATHS["tags"]))
    desc = _text_one(x.get("desc", DEFAULT_XPATHS["desc"]))
    
    # 属性提取
    icon_url = _attr_one(x.get("icon_img", DEFAULT_XPATHS["icon_img"]), "src")
    qrcode_url = _attr_one(x.get("qrcode_img", DEFAULT_XPATHS["qrcode_img"]), "src")
    screenshot_urls = _attr_list(x.get("screenshot_imgs", DEFAULT_XPATHS["screenshot_imgs"]), "src")
    
    # ... 其他字段
    
    return {
        "src_id": src_id,
        "name": name,
        "category": category,
        "tags_json": json.dumps(tags, ensure_ascii=False) if tags else None,
        # ...
    }
```

## 8. 调试技巧

### 1. 测试页面结构
```python
# 访问页面后打印HTML
page.get(url)
print(page.html[:1000])  # 打印前1000个字符

# 测试XPath
elements = page.eles('//h1')
for e in elements:
    print(e.text, e.attrs)
```

### 2. 保存页面截图
```python
page.get_screenshot(path='debug.png')
```

### 3. 使用浏览器开发者工具
- 在Chrome中手动访问页面
- 按F12打开开发者工具
- 在Console中测试XPath: `$x('//h1[@class="title"]')`
- 验证选择器是否正确

## 9. 常见错误和解决方案

| 错误现象 | 原因 | 解决方案 |
|---------|------|---------|
| AttributeError: 'str' object has no attribute 'attr' | XPath包含/@attr，返回字符串 | 移除/@attr，先获取元素再用.attr() |
| BrowserConnectError | 浏览器未正确启动 | 检查ChromiumOptions配置 |
| 获取不到元素 | 页面未加载完成 | 添加wait.doc_loaded()或等待特定元素 |
| 获取不到文本/属性 | XPath不正确 | 用浏览器开发者工具验证XPath |
| page.eles(xp=xp)报错 | API用法错误 | 改为 page.eles(xp) |

## 10. 参考资源

- 官方文档: https://DrissionPage.cn
- GitHub: https://github.com/g1879/DrissionPage
- 当前安装版本: ******** (通过 `python -c "import DrissionPage; print(DrissionPage.__version__)"` 查看)
