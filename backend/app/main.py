from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import Cấu hình tổng
from app.config import settings

# Import Router chính (đã gom toàn bộ các sub-router v1)
from app.api.v1.router import api_router

# Import Custom Exceptions
from app.core.exceptions import BaseAppException

# ==========================================
# 1. Quản lý vòng đời ứng dụng (Lifespan)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Quản lý các sự kiện startup và shutdown của ứng dụng.
    Thay thế cho @app.on_event("startup") đã bị deprecated.
    Lý tưởng để khởi tạo kết nối Redis pool hoặc load các AI Model nhỏ (nếu không dùng Celery).
    """
    # Xử lý khi khởi động server
    # Ví dụ: await redis_service.connect()
    print(f"🚀 Starting {settings.PROJECT_NAME}...")
    
    yield  # Ứng dụng đang chạy và nhận request tại đây
    
    # Xử lý khi tắt server (Graceful shutdown)
    # Ví dụ: await redis_service.disconnect()
    print("🛑 Shutting down gracefully...")

# ==========================================
# 2. Khởi tạo FastAPI Application
# ==========================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Lõi API xử lý nền tảng thi và bóc tách đề bằng AI",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# ==========================================
# 3. Cấu hình CORS (Cross-Origin Resource Sharing)
# ==========================================
# Cho phép Frontend (Next.js) giao tiếp với Backend mà không bị trình duyệt chặn
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],  # Cho phép mọi HTTP methods (GET, POST, PUT, DELETE...)
        allow_headers=["*"],  # Cho phép mọi Headers (bao gồm cả Authorization chứa JWT)
    )

# ==========================================
# 4. Global Exception Handler
# ==========================================
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    """
    Bắt toàn bộ các lỗi kế thừa từ BaseAppException (như PermissionDeniedError, FileParsingError...)
    Đảm bảo API luôn trả về cấu trúc JSON chuẩn mực, không làm crash ứng dụng.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "type": exc.__class__.__name__
        }
    )

# ==========================================
# 5. Gắn kết hệ thống Routers (Mount Routing)
# ==========================================
# Đưa toàn bộ các API v1 vào hoạt động với tiền tố được định nghĩa trong file config (thường là /api/v1)
app.include_router(api_router, prefix=settings.API_V1_STR)

# ==========================================
# 6. Health Check Endpoint
# ==========================================
@app.get("/health", tags=["System"])
def health_check():
    """
    Endpoint kiểm tra trạng thái sức khỏe của Server.
    Được sử dụng bởi Docker Healthcheck hoặc các hệ thống Load Balancer (Nginx, AWS ELB).
    """
    return {
        "status": "ok",
        "message": "Hệ thống đang hoạt động ổn định."
    }