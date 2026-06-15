from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    
class Settings(BaseSettings):    
    DATABASE_URL: str
    ENV: Environment = Environment.DEVELOPMENT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SUPER_ADMIN_EMAIL: str
    SUPER_ADMIN_PASSWORD: str   

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")



settings = Settings()