from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Add any other configuration settings here if needed
    class Config:
        env_file = ".env"

settings = Settings() 