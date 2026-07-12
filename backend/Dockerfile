# ==========================================
# STAGE 1: Builder (Môi trường build độc lập)
# ==========================================
# Sử dụng bản slim để giảm kích thước, nhưng vẫn đủ thư viện nền tảng
FROM python:3.10-slim AS builder

# Thiết lập các biến môi trường tối ưu cho Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Cài đặt các system dependencies cần thiết để compile các package C/C++ (như psycopg2, asyncpg, v.v.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements trước để tận dụng Docker Cache Layer cho thư viện
COPY requirements.txt .

# Khởi tạo Virtual Environment và cài đặt thư viện vào đó
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && pip install -r requirements.txt

# ==========================================
# STAGE 2: Runner (Môi trường chạy thực tế)
# ==========================================
FROM python:3.10-slim

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

WORKDIR /app

# Cài đặt các thư viện system runtime (Chỉ cài những gì thực sự cần để CHẠY app)
# poppler-utils thường cần thiết nếu ứng dụng AI của bạn bóc tách file PDF phức tạp
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    poppler-utils \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    # Thiết lập múi giờ chuẩn cho logging và cronjobs (nếu có)
    && ln -fs /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata

# Copy toàn bộ Virtual Environment từ stage builder sang (Đảm bảo image cực nhẹ)
COPY --from=builder /opt/venv /opt/venv

# Copy mã nguồn dự án vào container
COPY ./app /app/app

# ==========================================
# Cấu hình Bảo mật (Non-root User)
# ==========================================
# Không bao giờ chạy container ở quyền root trên Production
RUN addgroup --system fastapi_group && adduser --system --group fastapi_user \
    && chown -R fastapi_user:fastapi_group /app

USER fastapi_user

# Mở cổng giao tiếp cho FastAPI
EXPOSE 8000

# Lệnh mặc định khi container khởi chạy (Dành cho FastAPI Server)
# Số lượng workers (4) có thể điều chỉnh linh hoạt tùy số core CPU của server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]