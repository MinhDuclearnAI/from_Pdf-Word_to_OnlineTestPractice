from functools import lru_cache
from typing import Generator, AsyncGenerator
from fastapi import Request

# Import Cấu hình
from app.config import Settings, settings

# Giả định bạn sử dụng các thư viện SDK tiêu chuẩn
# import openai
# import redis.asyncio as aioredis
# import boto3

# ==========================================
# 1. Dependency cho App Settings (Cấu hình)
# ==========================================
@lru_cache()
def get_settings() -> Settings:
    """
    Sử dụng lru_cache để áp dụng pattern Singleton.
    File config chỉ được đọc và parse 1 lần duy nhất khi khởi động app,
    các lần gọi Depends(get_settings) sau sẽ trả về từ cache ngay lập tức.
    """
    return settings


# ==========================================
# 2. Dependency cho Caching & Rate Limiting (Redis)
# ==========================================
# async def get_redis_client(request: Request) -> AsyncGenerator:
#     """
#     Dependency tiêm Redis client vào các API cần caching hoặc Rate limit.
#     Thường trong FastAPI, Redis pool được khởi tạo ở sự kiện lifespan (startup) 
#     và gán vào request.app.state.redis
#     """
#     redis_client = getattr(request.app.state, "redis", None)
#     if not redis_client:
#         raise RuntimeError("Redis client chưa được khởi tạo trong hệ thống.")
#     
#     try:
#         yield redis_client
#     finally:
#         # Không đóng connection ở đây vì chúng ta dùng chung Connection Pool toàn cục
#         pass


# ==========================================
# 3. Dependency cho AI / LLM Clients
# ==========================================
# Tại sao cần inject LLM thay vì import trực tiếp? 
# -> Để dễ dàng Mock/Fake client khi viết Unit Test (Pytest) mà không tốn tiền API thật.

@lru_cache()
def get_openai_client():
    """
    Khởi tạo OpenAI Client. Lru_cache đảm bảo chỉ có 1 instance của HTTPX client
    được sinh ra, giúp tối ưu hóa TCP Connection (Keep-alive) khi gọi API liên tục.
    """
    # from openai import AsyncOpenAI
    # return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    pass

@lru_cache()
def get_anthropic_client():
    """
    Khởi tạo Anthropic Client (Claude) chuyên dùng cho việc chấm điểm tự luận.
    """
    # from anthropic import AsyncAnthropic
    # return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    pass


# ==========================================
# 4. Dependency cho Storage Service (MinIO / S3)
# ==========================================
@lru_cache()
def get_storage_client():
    """
    Khởi tạo Boto3 Client để tương tác với S3 hoặc MinIO.
    Việc sử dụng Depends(get_storage_client) trong endpoint upload_exam
    giúp logic linh hoạt hơn rất nhiều so với khởi tạo biến global.
    """
    # session = boto3.session.Session()
    # return session.client(
    #     service_name='s3',
    #     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    #     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    #     endpoint_url=settings.S3_ENDPOINT_URL,
    #     region_name=settings.AWS_REGION
    # )
    pass