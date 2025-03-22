import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import ClassVar


load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Honeypot Orchestrator"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/honeypot_db"
    )
    
    # Clerk Authentication
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")
    CLERK_PUBLISHABLE_KEY: str = os.getenv("CLERK_PUBLISHABLE_KEY", "")
    CLERK_WEBHOOK_SECRET: str = os.getenv("CLERK_WEBHOOK_SECRET", "")
    
    # CORS
    ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:4000",
        "https://yourdomain.com"
    ]
    
    # Docker settings
    DOCKER_HOST: str = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
    DOCKER_NETWORK: str = os.getenv("DOCKER_NETWORK", "honeypot-network")
    
    # Honeypot images
    HONEYPOT_IMAGES: ClassVar[dict] = {
        'SSH': 'cowrie/cowrie:latest',
        'FTP': 'honeynet/honeypot-ftp:latest',
        'Web': 'honeynet/snare:latest'
    }
    
    class Config:
        env_file = ".env"

settings = Settings()