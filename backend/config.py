from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库连接（trust 认证，无需密码）
    database_url: str = "postgresql+psycopg://postgres@localhost:5432/diet"
    # DeepSeek（后面写接口时才用，先留空）
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    # 向量模型（已定稿）
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_query_prefix: str = "为这个句子生成表示以用于检索相关文章："
    # 相似度阈值（后面检索用）
    similarity_threshold: float = 0.65

    class Config:
        env_file = ".env"


settings = Settings()