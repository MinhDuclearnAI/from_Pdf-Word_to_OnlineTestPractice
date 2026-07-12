import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Giả định Base được khởi tạo tại app.db.base
from app.db.base import Base

class JobStatus(str, enum.Enum):
    """
    Theo dõi vòng đời của một tiến trình xử lý AI.
    """
    pending = "pending"        # Đã nhận file vào queue (Redis), chờ Celery worker nhặt
    processing = "processing"  # Worker đang chạy extraction, gọi API LLM
    completed = "completed"    # Đã bóc tách thành công và lưu thành công vào bảng Exams
    failed = "failed"          # Xảy ra lỗi (file hỏng, API lỗi, parse JSON xịt...)

class AIProcessingJob(Base):
    __tablename__ = "ai_processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Đường dẫn file gốc đã upload lên MinIO/S3 (VD: "exams/toan_12_midterm.pdf")
    file_url = Column(String, nullable=False)
    
    # Trạng thái hiện tại của job
    status = Column(Enum(JobStatus), default=JobStatus.pending, nullable=False, index=True)
    
    # Lưu lại lỗi chi tiết (nếu có) để dễ dàng debug hệ thống
    error_message = Column(Text, nullable=True)

    # ==========================================
    # KHÓA NGOẠI (FOREIGN KEYS)
    # ==========================================
    
    # Người đã upload file và trigger job này
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # ID của bài kiểm tra được sinh ra sau khi AI hoàn tất.
    # Cho phép Null vì khi job mới tạo (pending) hoặc bị lỗi (failed), exam chưa tồn tại.
    result_exam_id = Column(Integer, ForeignKey("exams.id", ondelete="SET NULL"), nullable=True, unique=True)

    # ==========================================
    # TRACKING THỜI GIAN
    # ==========================================
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Thời gian chạy xong để đo lường hiệu năng/thời gian response của LLM API
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ==========================================
    # RELATIONSHIPS
    # ==========================================

    # Trỏ ngược về bảng User (người tạo job)
    creator = relationship(
        "User", 
        foreign_keys=[creator_id]
    )

    # Liên kết 1-1 với bảng Exam. 
    # Biến 'ai_job' đã được khai báo back_populates và uselist=False trong exam.py
    result_exam = relationship(
        "Exam", 
        back_populates="ai_job",
        foreign_keys=[result_exam_id]
    )

    def __repr__(self):
        return f"<AIProcessingJob(id={self.id}, status='{self.status}', file='{self.file_url}')>"