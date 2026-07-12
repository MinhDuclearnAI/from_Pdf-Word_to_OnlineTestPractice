from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# ==========================================
# Khai báo các Type (Literal) đồng bộ với AI & DB
# ==========================================
SubjectType = Literal["Toán", "Vật Lý", "Hóa Học", "Sinh Học", "Tiếng Anh", "IELTS", "HSA", "Khác"]
TestType = Literal["practice", "exam"]
ResultVisibilityType = Literal["score_only", "detailed", "after_close"]


# ==========================================
# Base Schema (Chứa các trường chung nhất)
# ==========================================
class ExamBase(BaseModel):
    title: str = Field(..., description="Tên bài kiểm tra/đề thi (Ví dụ: Thi thử giữa kỳ 1)")
    subject: SubjectType = Field(..., description="Môn học của đề thi")
    test_type: TestType = Field(..., description="Phân loại: 'practice' (Luyện tập) hoặc 'exam' (Kiểm tra/Thi)")
    duration: int = Field(..., gt=0, description="Thời gian làm bài tính bằng phút")
    
    # Cấu hình thời gian mở/đóng thi
    open_at: Optional[datetime] = Field(None, description="Thời gian bắt đầu cho phép làm bài")
    close_at: Optional[datetime] = Field(None, description="Thời gian tự động đóng bài thi")
    
    # Cấu hình xem kết quả (Chỉ hiện điểm / Hiện chi tiết / Công bố sau khi đóng)
    result_visibility: ResultVisibilityType = Field(
        default="detailed", 
        description="Cấu hình quyền xem kết quả sau khi nộp bài"
    )


# ==========================================
# Schema cho Input (Tạo mới & Cập nhật)
# ==========================================
class ExamCreate(ExamBase):
    """
    Schema dùng khi Giáo viên hoặc Hệ thống (AI Worker) tạo một đề thi mới.
    Bắt buộc phải truyền vào class_id để biết đề thi thuộc lớp nào.
    """
    class_id: int = Field(..., description="ID của lớp học chứa đề thi này")


class ExamUpdate(BaseModel):
    """
    Schema dùng cho API PATCH/PUT khi Giáo viên muốn cấu hình lại bài thi.
    Tất cả các trường đều là Optional (chỉ cập nhật những trường được gửi lên).
    """
    title: Optional[str] = None
    duration: Optional[int] = Field(None, gt=0)
    open_at: Optional[datetime] = None
    close_at: Optional[datetime] = None
    result_visibility: Optional[ResultVisibilityType] = None


class ExamConfig(BaseModel):
    """
    Schema tối giản dành riêng cho chức năng Cấu hình kỳ thi (Exam Management).
    Giáo viên thường chỉ cần update thời gian và cấu hình xem kết quả.
    """
    duration: Optional[int] = Field(None, gt=0)
    open_at: Optional[datetime] = None
    close_at: Optional[datetime] = None
    result_visibility: Optional[ResultVisibilityType] = None


# ==========================================
# Schema cho Output (Trả về từ API)
# ==========================================
class ExamOut(ExamBase):
    """
    Schema đầy đủ để trả về chi tiết một đề thi (GET /exams/{id}).
    Đã được map từ SQLAlchemy Model sang Pydantic.
    """
    id: int
    class_id: int
    created_at: datetime
    updated_at: datetime

    # ConfigDict(from_attributes=True) thay thế cho orm_mode=True trong Pydantic V2
    # Giúp Pydantic có thể đọc trực tiếp dữ liệu từ object của SQLAlchemy
    model_config = ConfigDict(from_attributes=True)


class ExamSummary(BaseModel):
    """
    Schema rút gọn dùng cho các API danh sách (GET /classes/{id}/exams).
    Giảm tải dữ liệu thừa để tối ưu băng thông khi render Dashboard.
    """
    id: int
    title: str
    subject: SubjectType
    test_type: TestType
    duration: int
    
    # Ở Frontend, ta thường cần biết trạng thái mở/đóng dựa vào thời gian hiện tại
    # Tuy nhiên trong DB không lưu trường is_active này, mà backend sẽ tính toán
    # và gán vào khi query trước khi trả về.
    is_active: Optional[bool] = Field(
        None, 
        description="Trạng thái đề thi đang mở hay đã đóng (Tính toán runtime)"
    )

    model_config = ConfigDict(from_attributes=True)