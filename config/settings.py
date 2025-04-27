import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mariadb+mariadbconnector://root:0000@127.0.0.1:3306/ndock")

    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b2d4f8a7c1e3g5j9k3p1z6o8q4w7y1r2")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:3000",
        "https://localhost",
        "https://localhost:8080",
        "https://localhost:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a global settings object
settings = Settings()
