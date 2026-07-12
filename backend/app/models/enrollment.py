from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Giả định Base được khởi tạo tại app.db.base
from app.db.base import Base

class ClassEnrollment(Base):
    __tablename__ = "class_enrollments"

    # Sử dụng Surrogate Primary Key (id độc lập) để dễ dàng thao tác CRUD qua API
    id = Column(Integer, primary_key=True, index=True)
    
    # Khóa ngoại liên kết với bảng users (chỉ định học sinh)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Khóa ngoại liên kết với bảng classes (chỉ định lớp học)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    
    # Tracking thời gian học sinh gia nhập lớp
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    # ==========================================
    # RÀNG BUỘC (CONSTRAINTS)
    # ==========================================
    # Đảm bảo một học sinh không thể gia nhập cùng một lớp học nhiều lần
    __table_args__ = (
        UniqueConstraint('student_id', 'class_id', name='_student_class_uc'),
    )

    # ==========================================
    # RELATIONSHIPS
    # ==========================================

    # Trỏ ngược lại bảng User (Học sinh)
    student = relationship(
        "User", 
        back_populates="enrollments"
    )

    # Trỏ ngược lại bảng Class (Lớp học)
    # Lưu ý: Biến này tên là `class_` khớp với `back_populates` đã khai báo trong file class_model.py
    class_ = relationship(
        "Class", 
        back_populates="enrollments"
    )

    def __repr__(self):
        return f"<ClassEnrollment(id={self.id}, student_id={self.student_id}, class_id={self.class_id})>"