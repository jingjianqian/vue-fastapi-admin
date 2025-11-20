# 青龙面板运行微信小程序爬虫技术方案

## 1. 设计原则

- **最小改动**：尽量不改变现有业务逻辑和 Celery 任务接口，仅在 `demo.py` 中增加青龙运行入口与少量配置。
- **复用现有 ORM**：继续使用项目现有的 ORM（如 Django ORM）和模型，不在 `demo.py` 中硬编码数据库连接信息。
- **保留 Celery**：不移除或替换 `@shared_task`，保证现有 Celery 任务在原环境中继续可用。
- **明确浏览器依赖**：通过文档和代码配置，显式管理 DrissionPage 所需浏览器依赖，避免默默降级导致排错困难。

## 2. 目录与路径规划

- 项目根目录（示例）：`E:/code/my/vue-fastapi-admin`
- 爬虫脚本：当前 `demo.py` 位于项目根目录（实际按项目为准）。
- 新增文档目录：`docs/qinglong/`
  - 需求文档：`docs/qinglong/qinglong_mini_program_requirements.md`
  - 技术方案：`docs/qinglong/qinglong_mini_program_tech_solution.md`

在青龙容器中：
- 挂载当前项目目录到容器内部某个路径，例如：`/ql/vue-fastapi-admin`；
- 在青龙任务命令中使用该路径，例如：
  - `cd /ql/vue-fastapi-admin && python demo.py`

## 3. 代码改造方案（demo.py）

### 3.1 新增依赖与环境变量

1. 在 `demo.py` 顶部增加：

   - `import os`：用于读取环境变量；

2. 环境变量约定：

   - `MINI_PROGRAM_SOURCE`：数据源选择，默认 `all`；
   - `MINI_PROGRAM_LIMIT`：单次抓取数量，默认 `100`，非法值时回退并记录日志；
   - `USE_MOCK_ON_BROWSER_FAIL`：浏览器初始化失败时是否允许回退到模拟数据，默认 `true`；

### 3.2 浏览器依赖处理

在 `WechatMiniProgramSpider.__init__` 中：

- 新增实例属性：
  - `self.use_mock_on_browser_fail`：根据 `USE_MOCK_ON_BROWSER_FAIL` 环境变量计算得出；

在 `setup_browser()` 的 `except` 分支中：

- 当前逻辑：
  - 记录错误日志；
  - 将 `self.browser` 置为 `None`；
  - 输出“将使用模拟数据”的警告日志；

- 改造后逻辑：
  - 保持以上行为不变；
  - 但在 `self.use_mock_on_browser_fail` 为 `False` 时，直接 `raise` 异常中断初始化：
    - 这样在青龙环境中设置 `USE_MOCK_ON_BROWSER_FAIL=false` 时，如果浏览器依赖缺失，任务会**直接失败**，而不会静默使用模拟数据；
    - 日志中会有明确的异常信息，便于运维排查浏览器安装问题。

> 说明：浏览器路径等更细节配置（如显式指定 Chrome/Chromium 路径），建议通过项目统一配置或 DrissionPage 的配置文件实现，此方案主要在“是否允许降级为模拟数据”层面做可配置化处理。

### 3.3 新增脚本入口（供青龙调用）

在文件末尾新增：

- 函数 `run_from_env()`：
  - 职责：
    - 从环境变量读取 `MINI_PROGRAM_SOURCE` 和 `MINI_PROGRAM_LIMIT`；
    - 创建 `WechatMiniProgramSpider` 实例并调用其 `crawl()` 方法；
    - 输出关键日志并返回结果；
    - 在 `finally` 中调用 `spider.cleanup()` 确保浏览器资源被正确释放；

- 主入口：
  - 在文件底部增加：
    - `if __name__ == "__main__":` 中调用 `run_from_env()`；
  - 这样可以在青龙中通过 `python demo.py` 直接触发完整爬虫流程。

### 3.4 保留 Celery 任务

- 不修改现有的：
  - `@shared_task` 装饰器；
  - `crawl_mini_program_info()` 与 `sync_mini_program_to_mywechat()` 的定义与实现；
- 在原有项目环境中：
  - Celery worker 继续以原方式导入并执行这些任务；
- 在青龙环境中：
  - 默认并不通过 Celery 触发，而是直接运行 `demo.py`；
  - 如有需要，可以在将来扩展为青龙通过命令行调用 Celery 任务接口（本方案暂不改造，保持简单）。

## 4. 环境与部署方案

### 4.1 容器与项目挂载

1. 在部署青龙时，将当前项目目录挂载到容器内某路径，例如：
   - 宿主机：`E:/code/my/vue-fastapi-admin`
   - 容器内：`/ql/vue-fastapi-admin`

2. 在青龙面板中配置任务命令时，推荐使用：
   - `cd /ql/vue-fastapi-admin && python demo.py`

### 4.2 Python 依赖安装

在青龙容器中：

1. 安装项目依赖（示例）：
   - `pip install -r /ql/vue-fastapi-admin/requirements.txt`

2. 确保包含：
   - `DrissionPage`
   - `Django`（或项目所用 Web 框架）
   - `celery`
   - 其他项目依赖包。

### 4.3 浏览器安装与配置

1. 在青龙容器镜像中或容器启动初始化过程中，安装可用的 Chrome/Chromium 及其依赖库；
2. 确保：
   - 当前运行用户有权限执行浏览器；
   - 浏览器版本与 DrissionPage 所支持的版本兼容；
3. 建议在 DrissionPage 配置中或系统环境中设置默认浏览器路径（如有需要），以减少运行时不确定性。

### 4.4 ORM / 配置化数据库

1. 继续使用项目原有 ORM（如 Django ORM）：
   - 在青龙容器中设置：
     - `DJANGO_SETTINGS_MODULE` 指向项目的 settings 模块；
     - 与数据库连接相关的环境变量（如数据库地址、账号密码等）；
   - 保持与项目其他服务一致的数据库配置。

2. 如未来希望将数据库连接完全配置化（脱离 Django），可以在独立脚本或配置模块中实现，本方案暂不重构此部分，只要求 `demo.py` 不出现硬编码连接字符串。

## 5. 青龙面板配置示例

### 5.1 环境变量示例

在青龙面板中新增环境变量（名称仅供参考）：

- `DJANGO_SETTINGS_MODULE=your_project.settings`
- `MINI_PROGRAM_SOURCE=all`
- `MINI_PROGRAM_LIMIT=100`
- `USE_MOCK_ON_BROWSER_FAIL=false`  （如希望浏览器失败时直接报错）

> 注意：数据库相关环境变量按项目现有标准配置，这里不重复展开。

### 5.2 定时任务示例

- 命令：
  - `cd /ql/vue-fastapi-admin && python demo.py`

- 时间表达式：
  - 例如：`0 0 * * *` 表示每天 0 点执行一次（具体按你需求配置）。

## 6. 演进与扩展方向

- 如需更细粒度控制：
  - 可以在 `run_from_env()` 中新增更多参数（如日志级别、是否仅测试浏览器可用性等）；
- 如需在青龙中直接触发 Celery 任务而不是本地执行：
  - 可以在将来新增一个命令行入口，调用 Celery 的 `delay()` 或 `apply_async()` 方法；
- 如需支持多环境（开发/测试/生产）：
  - 可以通过额外的环境变量指明当前环境，并在项目配置层面加载不同的 settings 或数据库配置。
