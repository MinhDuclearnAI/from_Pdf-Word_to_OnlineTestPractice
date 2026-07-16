import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Giả định bạn định nghĩa Base tại app.db.base
from app.db.base import Base

class UserRole(str, enum.Enum):
    """
    Định nghĩa các vai trò hợp lệ trong hệ thống.
    Kế thừa từ str giúp Enum có thể serialize trực tiếp thành JSON.
    """
    student = "student"
    teacher = "teacher"
    admin = "admin"  # Dự phòng cho hệ thống quản trị sau này

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True, nullable=True)
    
    # Thông tin bổ sung
    date_of_birth = Column(Date, nullable=True)
    school = Column(String, nullable=True)
    workplace = Column(String, nullable=True)
    
    # Sử dụng Enum cho role để đảm bảo tính toàn vẹn dữ liệu
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    
    # Cờ trạng thái để khóa/mở khóa tài khoản thay vì xóa cứng (hard delete)
    is_active = Column(Boolean, default=True)
    
    # Tự động ghi nhận thời gian tạo và cập nhật
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ==========================================
    # RELATIONSHIPS (Mối quan hệ với các bảng khác)
    # Lưu ý: Truyền tên Model dưới dạng string ("Class") để tránh lỗi Circular Import
    # ==========================================

    # Dành cho Giáo viên: Danh sách các lớp do giáo viên này tạo/quản lý
    classes_taught = relationship(
        "Class", 
        back_populates="teacher", 
        cascade="all, delete-orphan"
    )

    # Dành cho Học sinh: Danh sách các lớp học sinh này đã tham gia
    enrollments = relationship(
        "ClassEnrollment", 
        back_populates="student", 
        cascade="all, delete-orphan"
    )

    # Dành cho Học sinh: Danh sách các bài thi đã nộp
    submissions = relationship(
        "Submission", 
        back_populates="student", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"