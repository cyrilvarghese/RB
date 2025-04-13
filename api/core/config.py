from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    BUCKET_NAME: str = "property_html_files"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() 