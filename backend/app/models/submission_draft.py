from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Giả định Base được khởi tạo tại app.db.base
from app.db.base import Base

class SubmissionDraft(Base):
    """
    Bảng lưu trữ nháp (Autosave). 
    Tách biệt hoàn toàn với bảng Submission chính thức để tránh làm bẩn dữ liệu chấm điểm.
    """
    __tablename__ = "submission_drafts"

    id = Column(Integer, primary_key=True, index=True)
    
    # Sinh viên đang làm bài
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Đề thi đang làm
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    
    # Trạng thái bài làm hiện tại. 
    # Ví dụ: {"question_id_1": ["A"], "question_id_2": ["apple", "banana"]}
    answers = Column(JSONB, nullable=False, server_default='{}')

    # Thời gian lưu nháp cuối cùng
    last_saved_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ==========================================
    # RÀNG BUỘC (CONSTRAINTS)
    # ==========================================
    # Mỗi sinh viên chỉ có TỐI ĐA MỘT bản nháp cho một đề thi tại một thời điểm
    __table_args__ = (
        UniqueConstraint('student_id', 'exam_id', name='_student_exam_draft_uc'),
    )

    # ==========================================
    # RELATIONSHIPS
    # ==========================================

    # Trỏ ngược về bảng User
    student = relationship(
        "User", 
        # Không cần thiết phải back_populates ở User nếu không muốn làm rối bảng User
        foreign_keys=[student_id]
    )

    # Trỏ ngược về bảng Exam
    exam = relationship(
        "Exam", 
        # Tương tự, không cần back_populates ở Exam vì bảng này chỉ mang tính chất temporary (tạm thời)
        foreign_keys=[exam_id]
    )

    def __repr__(self):
        return f"<SubmissionDraft(id={self.id}, student_id={self.student_id}, exam_id={self.exam_id})>"