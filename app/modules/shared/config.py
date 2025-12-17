from pydantic import BaseModel


class AppConfig(BaseModel):
    environment: str = "dev"
    default_model_name: str = "dashen-banking-assistant-v1"
    enable_voice_ai: bool = True


config = AppConfig()
