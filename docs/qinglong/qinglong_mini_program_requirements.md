# 青龙面板运行微信小程序爬虫需求说明

## 1. 背景与目标

当前项目中已有 `demo.py`（微信小程序信息爬虫），通过 DrissionPage + Django ORM + Celery 任务，实现从微信官方/第三方平台采集小程序信息并入库。

目标：
- 在 **青龙面板** 中定时执行该爬虫逻辑；
- 继续使用 **ORM**（项目现有模型 `spiders.models.MiniProgramInfo` / `Mywechatmini.models.MyWechat` 等）；
- 保证 **Celery 依赖仍然存在且可用**，兼容当前后端任务体系；
- 明确并妥善处理 **浏览器（Chromium/Chrome）依赖问题**，避免隐性失败。

## 2. 使用场景

- 由青龙面板定时触发任务，执行命令（示例）：
  - `python /path/to/demo.py`  或
  - `python /path/to/demo.py`（在青龙脚本目录中）。
- 每次执行时：
  - 从环境变量读取数据源（微信官方 / 第三方 / 全部）；
  - 从环境变量读取单次抓取数量；
  - 初始化 DrissionPage 浏览器，按配置选择：
    - 浏览器不可用时是否允许使用模拟数据继续执行；
  - 使用 ORM 读写数据库，无硬编码连接信息。

## 3. 功能性需求

1. **爬虫逻辑复用**
   - 直接复用 `WechatMiniProgramSpider` 的现有逻辑：
     - `crawl_from_wechat_official()`
     - `crawl_from_third_party()`
     - `save_to_database()`
     - `crawl()`
   - 不改变原有 Celery 任务接口：
     - `crawl_mini_program_info()`
     - `sync_mini_program_to_mywechat()`

2. **脚本入口**
   - 在 `demo.py` 中新增脚本入口函数，例如 `run_from_env()`，满足：
     - 从环境变量读取任务参数；
     - 初始化爬虫并执行 `crawl()`；
     - 记录关键日志并返回结果；
     - 在 `__main__` 中调用，便于青龙通过 `python demo.py` 直接运行。

3. **参数化控制**

   通过环境变量控制以下参数：

   - `MINI_PROGRAM_SOURCE`
     - 描述：数据源选择。
     - 取值：`all` / `wechat_official` / `third_party`。
     - 默认：`all`。

   - `MINI_PROGRAM_LIMIT`
     - 描述：单次抓取最大数量。
     - 类型：整数；非法值时使用默认值并记录告警日志。
     - 默认：`100`。

   - `USE_MOCK_ON_BROWSER_FAIL`
     - 描述：浏览器初始化失败时，是否允许回退到模拟数据模式。
     - 取值：`true` / `false`（大小写不敏感）。
     - 默认：`true`（保持当前行为，兼容无浏览器环境）；
     - 在青龙面板中，如希望**强制检测浏览器依赖**，可设置为 `false`，使脚本在浏览器失败时直接抛出异常并终止，便于定位环境问题。

4. **数据库访问**

   - 必须通过 **ORM 或配置化** 的方式访问数据库，不允许在 `demo.py` 中硬编码数据库连接字符串。
   - 推荐方式：
     - 在青龙容器中配置 `DJANGO_SETTINGS_MODULE` 和相关数据库环境变量；
     - 通过 Django 项目统一管理数据库连接。
   - 要求：在青龙环境中执行 `python demo.py` 时：
     - 能成功导入 `spiders.models.MiniProgramInfo`；
     - 能成功导入 `Mywechatmini.models.MyWechat`；
     - ORM 操作能够连接到与当前项目一致的数据库实例。

## 4. 非功能性需求

1. **对现有项目影响最小**
   - 保持原有 Celery 任务装饰器和函数不变；
   - 不修改现有模型定义；
   - 仅在 `demo.py` 中：
     - 新增环境变量驱动的脚本入口；
     - 增加浏览器失败行为的可配置开关；
     - 补充必要的日志输出。

2. **可运维性**
   - 青龙面板运维人员只需：
     - 确保容器中安装所需依赖（Python 包 + 浏览器）；
     - 在面板中配置环境变量；
     - 添加定时任务命令；
   - 出现错误时，可通过日志快速判断：
     - 浏览器未安装 / 无法启动；
     - ORM 连接失败（数据库不可达、账号密码错误等）；
     - 参数配置错误（如 `MINI_PROGRAM_LIMIT` 非法）。

3. **浏览器依赖处理要求**

   - 文档中需要明确：
     - DrissionPage 对浏览器的要求（需要可用的 Chrome/Chromium）；
     - 青龙容器中安装浏览器的建议方式（如使用自定义镜像或在容器启动后安装）；
     - 推荐的启动参数：`--headless`、`--disable-gpu`、`--no-sandbox`、`--disable-dev-shm-usage` 等；
   - 代码层面需要：
     - 在浏览器初始化失败时，记录清晰的错误日志；
     - 允许通过 `USE_MOCK_ON_BROWSER_FAIL` 环境变量控制是否回退到模拟数据。

## 5. 依赖与前置条件

1. **运行环境**
   - Python 版本：与当前项目一致（建议与项目 README 中版本保持一致）。
   - 需要安装的 Python 包（示例）：
     - `DrissionPage`
     - `Django`（或当前项目所用 Web 框架）
     - `celery`
     - 项目本身的其他依赖（建议复用项目已有的 `requirements.txt`）。

2. **浏览器依赖**
   - 必须在青龙容器中安装可用的 Chrome/Chromium 及其依赖；
   - 建议：
     - 自定义青龙镜像，在构建阶段安装浏览器及依赖；
     - 或在容器启动后执行一段初始化脚本安装浏览器；
   - 需要保证浏览器可被当前用户调用，并与 DrissionPage 兼容。

3. **项目与数据库**
   - 在青龙容器中挂载当前项目代码目录；
   - 设置 `PYTHONPATH` 或在启动命令中添加项目根目录，保证能导入项目模块；
   - 设置数据库相关环境变量（由 Django 或 ORM 统一读取），确保与当前生产/测试环境一致。

## 6. 成功判定标准

- 在青龙面板中配置定时任务，通过 `python demo.py` 能成功执行；
- 日志中输出：
  - 浏览器初始化成功或失败原因；
  - 实际抓取数据源、数量；
  - 成功写入/更新数据库的条数；
- 在数据库中能看到对应的新小程序数据；
- 当浏览器依赖缺失且 `USE_MOCK_ON_BROWSER_FAIL=false` 时，任务应失败并输出清晰错误日志，便于快速排查环境问题。
