# import enum
# from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Text
# from sqlalchemy.dialects.postgresql import JSONB
# from sqlalchemy.orm import relationship

# # Giả định Base được khởi tạo tại app.db.base
# from app.db.base import Base

# class ComponentType(str, enum.Enum):
#     """
#     Định nghĩa loại giao diện (Component) để Frontend biết cách render.
#     Khớp chính xác với cấu trúc JSON Schema đã định nghĩa cho AI.
#     """
#     multiple_choice = "multiple_choice"       # Trắc nghiệm (4 đáp án)
#     math_equation = "math_equation"           # Công thức Toán (cần render LaTeX)
#     reading_passage = "reading_passage"       # Đoạn văn đọc hiểu (chứa các câu hỏi con)
#     fill_in_the_blank = "fill_in_the_blank"   # Điền vào chỗ trống
#     essay = "essay"                           # Tự luận (cần ô text lớn để gõ máy)

# class Question(Base):
#     __tablename__ = "questions"

#     id = Column(Integer, primary_key=True, index=True)
    
#     # Khóa ngoại trỏ về bảng exams
#     exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)

#     # Loại component UI
#     component_type = Column(Enum(ComponentType), nullable=False)

#     # Nội dung câu hỏi. Dùng Text thay vì String vì nội dung đề (đặc biệt bài Reading) có thể rất dài
#     question_text = Column(Text, nullable=False)

#     # ==========================================
#     # CÁC TRƯỜNG DỮ LIỆU ĐỘNG (JSONB)
#     # ==========================================
    
#     # Lưu trữ mảng các lựa chọn đáp án cho câu trắc nghiệm (VD: ["A. 10", "B. 20", "C. 30", "D. 40"])
#     # Nếu là câu tự luận hoặc đoạn văn Reading, trường này sẽ là Null
#     options = Column(JSONB, nullable=True)

#     # Đáp án đúng của hệ thống để chấm tự động. 
#     # Dùng JSONB để linh hoạt: 
#     # - Trắc nghiệm: lưu ["A"]
#     # - Điền từ nhiều ô: lưu ["is", "are"]
#     correct_answer = Column(JSONB, nullable=True)

#     # Điểm số của câu hỏi này (Mặc định 1 điểm/câu, dùng Float để cover trường hợp 0.25 điểm)
#     score_weight = Column(Float, default=1.0)

#     # ==========================================
#     # SELF-REFERENTIAL RELATIONSHIP (Đệ quy)
#     # Dành cho các bài Đọc hiểu (Reading) hoặc Câu hỏi Nhóm
#     # ==========================================
    
#     # Cột parent_id trỏ về chính bảng questions
#     parent_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=True)

#     # ==========================================
#     # RELATIONSHIPS
#     # ==========================================

#     # Trỏ ngược về bảng Exam (Khớp với exam.py đã tạo)
#     exam = relationship(
#         "Exam", 
#         back_populates="questions"
#     )

#     # Liên kết các câu hỏi con với câu hỏi cha (Reading Passage -> Multiple Choices)
#     parent = relationship(
#         "Question", 
#         remote_side=[id], 
#         back_populates="children"
#     )
    
#     children = relationship(
#         "Question", 
#         back_populates="parent", 
#         cascade="all, delete-orphan"
#     )

#     def __repr__(self):
#         return f"<Question(id={self.id}, exam_id={self.exam_id}, type='{self.component_type}')>"


import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

# Giả định Base được khởi tạo tại app.db.base
from app.db.base import Base

class ComponentType(str, enum.Enum):
    """
    Định nghĩa loại giao diện (Component) để Frontend biết cách render.
    Khớp chính xác với cấu trúc JSON Schema đã định nghĩa cho AI.
    """
    multiple_choice = "multiple_choice"       # Trắc nghiệm (4 đáp án)
    math_equation = "math_equation"           # Công thức Toán (cần render LaTeX)
    reading_passage = "reading_passage"       # Đoạn văn đọc hiểu (chứa các câu hỏi con)
    fill_in_the_blank = "fill_in_the_blank"   # Điền vào chỗ trống
    essay = "essay"                           # Tự luận (cần ô text lớn để gõ máy)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Khóa ngoại trỏ về bảng exams
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)

    # Loại component UI
    component_type = Column(Enum(ComponentType), nullable=False)

    # Nội dung câu hỏi.
    question_text = Column(Text, nullable=False)

    # ==========================================
    # CÁC TRƯỜNG DỮ LIỆU ĐỘNG & BỔ SUNG
    # ==========================================
    
    # Lưu trữ mảng các lựa chọn đáp án cho câu trắc nghiệm
    options = Column(JSONB, nullable=True)

    # [FIX]: Đổi từ JSONB sang String để khớp tuyệt đối với Pydantic Schema (Optional[str])
    # và dữ liệu LLM trả về.
    correct_answer = Column(String, nullable=True)

    # Điểm số của câu hỏi này
    score_weight = Column(Float, default=1.0)

    # [FIX]: Bổ sung 2 cột bị thiếu để Celery Task không bị crash lỗi AttributeError
    passage_ref = Column(Text, nullable=True)
    answer_placeholder = Column(String, nullable=True)

    # ==========================================
    # SELF-REFERENTIAL RELATIONSHIP (Đệ quy)
    # ==========================================
    
    # Giữ lại cột parent_id để làm bản lề cho việc nâng cấp cấu trúc Cây (Tree) sau này
    parent_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=True)

    # ==========================================
    # RELATIONSHIPS
    # ==========================================

    # Trỏ ngược về bảng Exam 
    exam = relationship(
        "Exam", 
        back_populates="questions"
    )

    # Liên kết các câu hỏi con với câu hỏi cha
    parent = relationship(
        "Question", 
        remote_side=[id], 
        back_populates="children"
    )
    
    children = relationship(
        "Question", 
        back_populates="parent", 
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Question(id={self.id}, exam_id={self.exam_id}, type='{self.component_type}')>"