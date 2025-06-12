import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    alpha_vantage_api_key: str
    app_name: str = "GeoPark Data API"
    debug: bool = True

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "allow"
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Validar API key al inicio
if not get_settings().alpha_vantage_api_key:
    print("WARNING: ALPHA_VANTAGE_API_KEY no está configurada") 