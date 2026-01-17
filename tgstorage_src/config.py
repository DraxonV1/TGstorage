from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Required Settings
    API_ID: int = 0
    API_HASH: str = ""
    CHANNEL_ID: int = 0
    
    # Security
    ADMIN_API_KEY: str = "DEFAULT_INSECURE_KEY"
    
    # Server
    DATABASE_URL: str = "storage.db"
    BASE_URL: str = "http://localhost"
    
    # Proxy (Optional)
    PROXY_HOST: Optional[str] = None
    PROXY_PORT: Optional[int] = None
    PROXY_USER: Optional[str] = None
    PROXY_PASS: Optional[str] = None
    
    UPLOAD_DELAY: float = 0.5
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def bot_token_list(self) -> List[str]:
        token_file = os.path.join(os.path.dirname(__file__), "tokens.txt")
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                return [t.strip() for t in f.readlines() if t.strip()]
        return []

settings = Settings()