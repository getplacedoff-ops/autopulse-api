from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, HttpUrl, PostgresDsn, RedisDsn, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class RateLimitCfg(BaseModel): rpm: int; burst: int = 0
class AIProviderCfg(BaseModel): name: Literal["cloudflare", "nvidia"]; base_url: HttpUrl; api_keys: List[str] = []; account_id: Optional[str] = None; models: Dict[str, str] = {}; rate_limit: RateLimitCfg
class DomainCfg(BaseModel): delay_ms: int = 1500; max_concurrent: int = 10; timeout: float = 30.0; headers: Dict[str, str] = {}; requires_browser: bool = False; api_endpoint: Optional[str] = None

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", nested_model_default_partial_update=True)
    APP_ENV: Literal["development", "production"] = "production"
    INSTANCE_ID: str = "autopulse-oracle-01"
    LOG_LEVEL: str = "INFO"
    DATA_DIR: Path = Path("/var/lib/autopulse")
    DATABASE_URL: PostgresDsn = "postgresql://autopulse:pass@localhost:5432/autopulse"
    DB_POOL_SIZE: int = 15; DB_MAX_OVERFLOW: int = 5
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    AI_PROVIDERS: Dict[str, AIProviderCfg] = {}
    
    @field_validator("AI_PROVIDERS", mode="before")
    @classmethod
    def _parse_ai(cls, v):
        return json.loads(v) if isinstance(v, str) else v
        
    SCRAPER_DOMAINS: Dict[str, DomainCfg] = {}
    
    @field_validator("SCRAPER_DOMAINS", mode="before")
    @classmethod
    def _parse_domains(cls, v):
        return json.loads(v) if isinstance(v, str) else v
        
    USER_AGENT: str = "AutoPulseBot/1.0 (+https://autopulse.ai/bot; support@autopulse.ai)"
    CACHE_TTL_HOURS: int = 6
    PIPELINE_STAGES_ENABLED: List[str] = []
    
    @field_validator("PIPELINE_STAGES_ENABLED", mode="before")
    @classmethod
    def _parse_stages(cls, v):
        return json.loads(v) if isinstance(v, str) else v
        
    MAX_CONCURRENT_STAGES: int = 3
    STAGE_TIMEOUT_SEC: int = 3600
    CHECKPOINT_INTERVAL_SEC: int = 30

    HTTP_MAX_CONN: int = 100
    HTTP_MAX_KEEPALIVE: int = 20
    PARSE_WORKERS: int = 4
    AI_WORKERS: int = 8
    SUPABASE_URL: HttpUrl
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    R2_BUCKET_NAME: str = "autopulse-assets"
    R2_PUBLIC_URL: str = "https://assets.autopulse.pages.dev"
    TARGETS_OEMS: List[Dict] = []
    TARGETS_AGGREGATORS: List[Dict] = []
    
    @field_validator("TARGETS_OEMS", "TARGETS_AGGREGATORS", mode="before")
    @classmethod
    def _parse_targets(cls, v):
        return json.loads(v) if isinstance(v, str) else v
        
    @computed_field
    @property
    def cloudflare_cfg(self) -> Optional[AIProviderCfg]:
        return self.AI_PROVIDERS.get("cloudflare")
        
    @computed_field
    @property
    def nvidia_cfg(self) -> Optional[AIProviderCfg]:
        return self.AI_PROVIDERS.get("nvidia")

    # Vision / PDF
    GEMINI_API_KEY: str = ""
    VISION_MODEL_PATH: str = "/opt/autopulse/models/siglip-base-patch16-224.onnx" # Local ONNX
    
    # Rate Limits (Per Domain, RPM)
    RATE_LIMITS: Dict[str, int] = Field(default_factory=lambda: {
        "carwale.com": 5,      # Very strict
        "cardekho.com": 3,     # Very strict
        "cdn.carwale.com": 20, # Images
        "cdn.cardekho.com": 20,
        "pdf.cdn.oem.com": 10, # Brochures
    })
    
    # Validation Thresholds
    SPEC_CONSENSUS_THRESHOLD: float = 0.95 # 95% field match required
    IMAGE_CONFIDENCE_THRESHOLD: float = 0.92
    MIN_REQUIRED_VIEWS: List[str] = ["exterior_front", "exterior_rear", "exterior_side", "interior_dashboard", "interior_seats"]
    
    # Admin
    ADMIN_SSE_RETRY_MS: int = 3000

settings = Settings() # type: ignore
