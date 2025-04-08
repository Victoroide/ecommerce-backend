from pydantic_settings  import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    BACKEND_URL: str
    AUTH_SECRET_KEY: str

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_STORAGE_BUCKET_NAME: str
    AWS_S3_REGION_NAME: str

    PINECONE_INDEX_NAME: str
    PINECONE_API_KEY: str

    OPENAI_BASE_MODEL: str
    OPENAI_THINKING_MODEL: str
    OPENAI_EMBEDDING_MODEL: str
    OPENAI_AZURE_API_KEY: str
    OPENAI_AZURE_API_BASE: str
    OPENAI_AZURE_API_VERSION: str
    AWS_S3_ENABLE_ACL: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
