from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# 动态获取项目根目录，用于构建绝对路径
# 这里使用 Path 的好处是跨平台路径更稳定，避免了在不同操作系统上路径分隔符不同的问题
PROJECT_ROOT = Path(__file__).resolve().parents[3]


# pydantic-settings 的核心配置类
class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    database_url: str = ""
    jwt_secret_key: str = ""

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"

    # ChromaDB 持久化目录
    chroma_persist_dir: Path = PROJECT_ROOT / "others" / "chroma"
    # 上传目录
    upload_dir: Path = PROJECT_ROOT / "others" / "uploads"
    # Embedding 模型名称
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    model_config = SettingsConfigDict(
        # 读取指定目录下的环境变量文件
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        # 环境变量名不区分大小写
        case_sensitive=False,
        # .env 中如果存在当前 Settings 类没有定义的额外变量，就忽略它们，而不是启动失败
        extra="ignore",
    )

    # 这个函数用来列出缺失的必填配置项
    def missing_required(self) -> list[str]:
        required_settings = {
            "database_url": self.database_url,
            "jwt_secret_key": self.jwt_secret_key,
            "deepseek_api_key": self.deepseek_api_key,
        }

        return [
            name
            for name, value in required_settings.items()
            if not value.strip()
        ]

    # 表示可以传入任意数量的位置参数，每个参数都是一个字符串，表示要检查的配置项的名称
    def require(self, *names: str) -> None:
        # 用于保存缺少的字段名
        missing_names = []

        for name in names:
            value = getattr(self, name, "")

            if not isinstance(value, str) or not value.strip():
                missing_names.append(name)

        if missing_names:
            raise RuntimeError(
                "Missing required settings: "
                + ", ".join(missing_names)
            )

# 缓存装饰器，用于缓存 Settings 类的实例，避免每次请求都创建新的实例
@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()