import os
from typing import List

class Settings:
    PROJECT_NAME: str = "CuraAssist CareHub API"
    VERSION: str = "2.4.0"
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://ifwsijbkmuzqttwbvifp.supabase.co").strip().rstrip("/")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "").strip()
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./curaassist.db")
    
    # CORS Configuration
    CORS_ORIGINS_STR: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,"
        "https://ai-healthcare-system-eta.vercel.app,https://curaassist-carehub-backend-2.fastapicloud.dev"
    )
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS_STR.split(",") if o.strip()]
        
    @property
    def ALLOW_ALL_ORIGINS(self) -> bool:
        return "*" in self.CORS_ORIGINS

settings = Settings()
