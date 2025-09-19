from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import json


class Settings(BaseSettings):
    # Server Configuration
    port: int = Field(default=8000, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Supabase Configuration
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(..., env="SUPABASE_SERVICE_KEY")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_enabled: bool = Field(default=False, env="REDIS_ENABLED")
    
    # JWT Configuration (Optional - using Supabase auth instead)
    # jwt_secret_key: str = Field(default="", env="JWT_SECRET_KEY")
    # jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    # jwt_expiration_hours: int = Field(default=168, env="JWT_EXPIRATION_HOURS")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:8081", "exp://"],
        env="CORS_ORIGINS"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=900, env="RATE_LIMIT_PERIOD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "cors_origins":
                try:
                    return json.loads(raw_val)
                except:
                    return raw_val.split(",")
            return raw_val
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"


# Create global settings instance
settings = Settings()