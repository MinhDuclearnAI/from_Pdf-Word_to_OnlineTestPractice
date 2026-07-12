from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Giả định Base được khởi tạo tại app.db.base
from app.db.base import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Tên lớp học (VD: "Toán 12A1", "IELTS Reading K45")
    name = Column(String, index=True, nullable=False)
    
    # Môn học để tiện phân loại và lọc sau này
    subject = Column(String, index=True, nullable=True) 
    
    # Khóa ngoại liên kết với bảng users (chỉ định định danh của giáo viên)
    # Sử dụng ondelete="CASCADE" ở mức DB: Nếu tài khoản giáo viên bị xóa, các lớp của họ cũng tự động bị xóa
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Tracking thời gian
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ==========================================
    # RELATIONSHIPS
    # ==========================================

    # Liên kết ngược lại với Giáo viên (User)
    teacher = relationship(
        "User", 
        back_populates="classes_taught"
    )

    # Liên kết 1-N với bảng trung gian ClassEnrollment để lấy danh sách học sinh
    # Tên biến back_populates thường dùng "class_" vì "class" là từ khóa (keyword) mặc định của Python
    enrollments = relationship(
        "ClassEnrollment", 
        back_populates="class_", 
        cascade="all, delete-orphan"
    )

    # Liên kết 1-N với bảng Exam (Một lớp có thể có nhiều bài kiểm tra)
    exams = relationship(
        "Exam", 
        back_populates="class_", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Class(id={self.id}, name='{self.name}', subject='{self.subject}', teacher_id={self.teacher_id})>"