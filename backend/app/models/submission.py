import enum
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Giả định Base được khởi tạo tại app.db.base
from app.db.base import Base

class SubmissionStatus(str, enum.Enum):
    """
    Trạng thái của bài nộp, rất quan trọng khi hệ thống có chấm điểm tự luận bằng AI.
    """
    submitted = "submitted"
    pending_grading = "pending_grading"
    completed = "completed"

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Khóa ngoại trỏ về bài kiểm tra
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    
    # Khóa ngoại trỏ về học sinh nộp bài
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # ==========================================
    # LƯU TRỮ ĐÁP ÁN BẰNG JSONB
    # ==========================================
    # Cấu trúc dự kiến: 
    # {
    #   "question_id_1": ["A"],                 // Trắc nghiệm
    #   "question_id_2": ["apple", "banana"],   // Điền từ
    #   "question_id_3": "Nội dung bài luận..." // Tự luận
    # }
    answers = Column(JSONB, nullable=False, server_default='{}')

    # Trạng thái hiện tại của bài nộp
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.submitted, nullable=False)
    
    # Tổng điểm đạt được (Sử dụng Float để hỗ trợ điểm lẻ như 8.5)
    # Có thể Null trong trường hợp bài thi có tự luận và đang chờ AI chấm (trạng thái 'grading')
    score = Column(Float, nullable=True)

    # Thời gian nộp bài (Dùng để kiểm tra xem có nộp muộn/quá giờ hay không)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    # ==========================================
    # RELATIONSHIPS
    # ==========================================

    # Trỏ ngược về bảng Exam
    # Biến 'submissions' đã được khai báo back_populates trong exam.py
    exam = relationship(
        "Exam", 
        back_populates="submissions"
    )

    # Trỏ ngược về bảng User (Học sinh)
    # Biến 'submissions' đã được khai báo back_populates trong user.py
    student = relationship(
        "User", 
        back_populates="submissions"
    )

    def __repr__(self):
        return f"<Submission(id={self.id}, exam_id={self.exam_id}, student_id={self.student_id}, status='{self.status}', score={self.score})>"