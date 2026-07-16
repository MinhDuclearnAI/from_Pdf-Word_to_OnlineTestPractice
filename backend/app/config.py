from typing import List, Optional, Any
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ==========================================
    # 1. Cấu hình Core Application
    # ==========================================
    PROJECT_NAME: str = "AI Exam Platform API"
    API_V1_STR: str = "/api/v1"
    
    # Cấu hình CORS để Next.js (Frontend) có thể gọi API mà không bị chặn
    BACKEND_CORS_ORIGINS: Any = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    # ==========================================
    # 2. Cấu hình Database (PostgreSQL)
    # ==========================================
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "exam_platform_db"
    
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> Any:
        """
        Tự động lấy chuỗi kết nối từ biến DATABASE_URL trong .env trước.
        """
        import os
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return db_url
        if isinstance(v, str) and v.strip():
            return v
        
        # Lấy các giá trị đã được Pydantic parse trước đó
        values = info.data
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}"
            f"@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}"
            f"/{values.get('POSTGRES_DB')}"
        )

    # ==========================================
    # 3. Cấu hình Background Task (Redis & Celery)
    # ==========================================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ==========================================
    # 4. Cấu hình Security (JWT & Password Hashing)
    # ==========================================
    # Khóa bí mật dùng để ký JWT - BẮT BUỘC PHẢI KHAI BÁO TRONG .env Ở MÔI TRƯỜNG PROD
    JWT_SECRET: str = "super-secret-key-for-dev-only-change-it-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 ngày
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7          # 7 ngày

    # ==========================================
    # 5. Cấu hình LLM & AI Services
    # ==========================================
    # Để Optional vì có thể dev local chưa cần dùng đến model của Anthropic/OpenAI
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # Model mặc định để bóc tách và chấm điểm
    DEFAULT_EXTRACTION_MODEL: str = "gemini-2.5-flash-lite"
    DEFAULT_GRADING_MODEL: str = "gemini-2.5-flash-lite"

    # ==========================================
    # 6. Cấu hình Storage (AWS S3 / MinIO Local)
    # ==========================================
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_BUCKET_NAME: str = "exam-platform-storage"
    AWS_REGION: str = "ap-southeast-1"
    
    # Rất quan trọng nếu bạn dùng MinIO thay vì AWS S3 thực tế
    S3_ENDPOINT_URL: Optional[str] = None 

    # ==========================================
    # Cấu hình Pydantic đọc biến môi trường
    # ==========================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # Bỏ qua các biến môi trường thừa trong hệ thống không thuộc class này
        extra="ignore" 
    )


# Khởi tạo instance Singleton (Chỉ tạo 1 lần và dùng chung trên toàn bộ dự án)
settings = Settings()