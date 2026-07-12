import os
import re
from datetime import datetime

from sqlalchemy import create_engine, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

# Lấy DATABASE_URL từ biến môi trường.
# Bạn có thể thay đổi giá trị default phù hợp với file docker-compose.yml của bạn
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/exam_platform"
)

# 1. Thiết lập Engine
# pool_pre_ping=True: Tự động kiểm tra kết nối trước khi thực thi query, tránh lỗi kết nối bị rớt.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,        # Giới hạn số lượng connection trong pool
    max_overflow=20      # Số lượng connection vượt mức cho phép khi hệ thống tải nặng
)

# 2. Thiết lập Session Factory
# autocommit=False, autoflush=False giúp chúng ta kiểm soát giao dịch (transaction) thủ công
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Định nghĩa Base Class cho SQLAlchemy 2.0
class Base(DeclarativeBase):
    """
    Lớp cơ sở cho toàn bộ Database Models.
    Cung cấp cơ chế tự động tạo tên bảng và các trường thời gian mặc định.
    """
    
    # Tự động tạo tên bảng (__tablename__) dựa trên tên Class
    # Ví dụ: Class 'User' -> bảng 'users', 'SubmissionDraft' -> 'submission_drafts'
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Thuật toán chuyển đổi CamelCase sang snake_case
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Thêm 's' vào cuối nếu chưa có để tuân thủ chuẩn đặt tên bảng số nhiều
        if not name.endswith('s'):
            return f"{name}s"
        return name

    # Trường thời gian tạo bản ghi (tự động lấy giờ server DB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="Thời gian tạo"
    )
    
    # Trường thời gian cập nhật bản ghi (tự động cập nhật mỗi khi có thay đổi)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        comment="Thời gian cập nhật gần nhất"
    )