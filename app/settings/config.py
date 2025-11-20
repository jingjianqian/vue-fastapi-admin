import os
import typing

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VERSION: str = "0.1.0"
    APP_TITLE: str = "Vue FastAPI Admin"
    PROJECT_NAME: str = "Vue FastAPI Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = True

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    
    # Static files and upload configuration
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")

    UPLOAD_DIR: str = os.path.join(STATIC_DIR, "uploads", "wechat")
    # 静态URL前缀与公共域名（用于对外拼接可访问URL）
    # 例如：STATIC_URL_PREFIX="/static"，STATIC_PUBLIC_BASE_URL="https://admin.example.com"
    STATIC_URL_PREFIX: str = "/static"
    STATIC_PUBLIC_BASE_URL: str | None = None
    ALLOWED_IMAGE_EXTS: set = {"png", "jpg", "jpeg", "webp"}
    ALLOWED_IMAGE_CONTENT_TYPES: set = {"image/png", "image/jpeg", "image/webp"}
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"  # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 day
    TORTOISE_ORM: dict = {
        "connections": {
            # SQLite configuration（保留本地调试用，如不需要可删除）
            "sqlite": {
                "engine": "tortoise.backends.sqlite",
                "credentials": {"file_path": f"{BASE_DIR}/db.sqlite3"},  # Path to SQLite database file
            },
            # MySQL/MariaDB configuration（当前作为默认连接使用）
            # Install with: tortoise-orm[asyncmy]
            "mysql": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": "152.32.173.226",  # Database host address（请改成你的 MySQL 主机）
                    "port": 3306,  # Database port
                    "user": "root",  # Database username
                    "password": "Jing.jianqian2334",  # Database password
                    "database": "myweb_dev2",  # Database name
                },
            },
            # PostgreSQL configuration
            # Install with: tortoise-orm[asyncpg]
            # "postgres": {
            #     "engine": "tortoise.backends.asyncpg",
            #     "credentials": {
            #         "host": "localhost",  # Database host address
            #         "port": 5432,  # Database port
            #         "user": "yourusername",  # Database username
            #         "password": "yourpassword",  # Database password
            #         "database": "yourdatabase",  # Database name
            #     },
            # },
            # MSSQL/Oracle configuration
            # Install with: tortoise-orm[asyncodbc]
            # "oracle": {
            #     "engine": "tortoise.backends.asyncodbc",
            #     "credentials": {
            #         "host": "localhost",  # Database host address
            #         "port": 1433,  # Database port
            #         "user": "yourusername",  # Database username
            #         "password": "yourpassword",  # Database password
            #         "database": "yourdatabase",  # Database name
            #     },
            # },
            # SQLServer configuration
            # Install with: tortoise-orm[asyncodbc]
            # "sqlserver": {
            #     "engine": "tortoise.backends.asyncodbc",
            #     "credentials": {
            #         "host": "localhost",  # Database host address
            #         "port": 1433,  # Database port
            #         "user": "yourusername",  # Database username
            #         "password": "yourpassword",  # Database password
            #         "database": "yourdatabase",  # Database name
            #     },
            # },
        },
        "apps": {
            "models": {
                "models": ["app.models", "aerich.models"],
                # 将默认连接从 sqlite 换成 mysql
                "default_connection": "mysql",
            },
        },
        "use_tz": False,  # Whether to use timezone-aware datetimes
        "timezone": "Asia/Shanghai",  # Timezone setting
    }
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # 小程序配置（从环境变量读取）
    WXAPP_APPID: str = "wx94e9f4328118219a"
    WXAPP_SECRET: str = "69b9d30a74bb454805f6cacc2e2ed439"
    WXAPP_API_KEY: str = ""
    WXAPP_API_SECRET: str = ""
    
    # 微信API配置
    WX_CODE2SESSION_URL: str = "https://api.weixin.qq.com/sns/jscode2session"
    WX_API_TIMEOUT: int = 10  # 微信API超时时间（秒）
    
    # 频率限制配置
    WXAPP_RATE_LIMIT_PER_MINUTE: int = 60
    WXAPP_RATE_LIMIT_PER_HOUR: int = 1000
    
    # 爬虫API配置
    CRAWLER_API_KEY: str = "we123_crawler_secret_key"  # 爬虫提交数据的API密钥
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
