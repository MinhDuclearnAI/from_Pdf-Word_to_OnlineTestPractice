import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

# Giả định Base được khởi tạo tại app.db.base
from app.db.base import Base

class ExamType(str, enum.Enum):
    """Phân loại đề thi để phục vụ logic UI và thống kê"""
    practice = "practice"  # Luyện tập (Học sinh tự up hoặc giáo viên giao làm tự do)
    test = "test"          # Kiểm tra chính thức (Tính điểm vào bảng điểm của lớp)

class ResultVisibility(str, enum.Enum):
    """Cấu hình quyền xem kết quả sau khi thi xong (hoặc sau khi đóng đề)"""
    hidden = "hidden"          # Không hiển thị gì cả (Chờ giáo viên công bố)
    score_only = "score_only"  # Chỉ hiển thị điểm tổng (Ví dụ: 8.5/10)
    full = "full"              # Hiển thị điểm và chi tiết từng câu đúng/sai, đáp án

class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    
    # Tiêu đề bài kiểm tra (VD: "Kiểm tra 1 tiết Đại số chương 1")
    title = Column(String, nullable=False)
    
    # Môn học phục vụ phân loại (Toán, Tiếng Anh, IELTS, ...)
    subject = Column(String, index=True, nullable=True)
    
    # Trạng thái và Cấu hình thi
    exam_type = Column(Enum(ExamType), default=ExamType.test, nullable=False)
    result_visibility = Column(Enum(ResultVisibility), default=ResultVisibility.full, nullable=False)
    
    # Thời gian làm bài tính bằng phút (VD: 45, 90). Nếu Null nghĩa là không giới hạn thời gian (tự luyện)
    duration = Column(Integer, nullable=True) 
    
    # Thời gian mở/đóng cổng thi
    open_at = Column(DateTime(timezone=True), nullable=True)
    close_at = Column(DateTime(timezone=True), nullable=True)

    # ==========================================
    # KHÓA NGOẠI (FOREIGN KEYS)
    # ==========================================
    
    # Lớp học được giao đề. Có thể Null nếu đây là đề do học sinh tự upload ôn tập cá nhân.
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=True)
    
    # Người tải đề lên (Giáo viên hoặc Học sinh). Phải có để tính quota lưu trữ và phân quyền.
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ==========================================
    # RELATIONSHIPS
    # ==========================================

    # Liên kết với lớp học (N-1)
    class_ = relationship(
        "Class", 
        back_populates="exams"
    )

    # Liên kết với người tạo (N-1). 
    creator = relationship(
        "User", 
        foreign_keys=[creator_id]
        # Không nhất thiết phải có back_populates ở bảng User nếu không hay query từ User -> Exams
    )

    # Liên kết với bảng Question (1-N): Một đề thi có nhiều câu hỏi
    questions = relationship(
        "Question", 
        back_populates="exam", 
        cascade="all, delete-orphan"
    )

    # Liên kết với bảng Submission (1-N): Một đề thi có nhiều lượt nộp bài của nhiều học sinh
    submissions = relationship(
        "Submission", 
        back_populates="exam", 
        cascade="all, delete-orphan"
    )
    
    # Liên kết 1-1 với bảng AIProcessingJob (Tùy chọn)
    # Dùng để truy vết đề này được sinh ra từ tiến trình xử lý AI nào
    ai_job = relationship(
        "AIProcessingJob", 
        back_populates="result_exam", 
        uselist=False
    )

    def __repr__(self):
        return f"<Exam(id={self.id}, title='{self.title}', type='{self.exam_type}', class_id={self.class_id})>"