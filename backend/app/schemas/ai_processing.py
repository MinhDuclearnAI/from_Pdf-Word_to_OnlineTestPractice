from typing import Optional, Literal, List, Any
from pydantic import BaseModel, Field

# ==========================================
# 1. Schemas cho Output của LLM (AI Parsing)
# ==========================================

class ClassificationResult(BaseModel):
    """
    Schema kiểm soát dữ liệu trả về từ LLM khi phân loại tài liệu (Pass 1).
    Sử dụng Literal để ép LLM trả về chính xác các danh mục đã định trước, 
    tránh lỗi sinh ra dữ liệu ảo.
    """
    title: Optional[str] = Field(
        None, 
        description="Tên đầy đủ của đề thi hoặc tài liệu (Ví dụ: Đề thi thử THPT Quốc gia môn Toán)."
    )
    
    subject: Literal[
        "Toán", "Tiếng Anh", "Lý", "Hóa", "Sinh", "IELTS", "HSA", "Khác"
    ] = Field(
        ..., 
        description="Phân loại môn học bắt buộc. Chỉ được chọn các giá trị có sẵn."
    )
    
    test_type: Literal["practice", "exam"] = Field(
        ..., 
        description="Phân loại mục đích sử dụng. 'practice' cho tự luyện, 'exam' cho bài kiểm tra/thi."
    )
    
    duration: Optional[int] = Field(
        None, 
        description="Thời gian làm bài quy ra phút (chỉ lấy số nguyên, ví dụ: 15, 45, 90).",
        ge=0
    )


class AIParsingResult(BaseModel):
    """
    Schema tổng hợp kết quả của toàn bộ tiến trình phân tích AI.
    Được sử dụng làm cấu trúc truyền tải dữ liệu nội bộ trong các services.
    """
    classification: ClassificationResult
    
    # Dùng kiểu Any cho danh sách câu hỏi để tránh lỗi Circular Import với schemas/question.py
    # Dữ liệu này sẽ được validate lại qua QuestionSchema ở bước lưu vào Database.
    questions: List[Any] = Field(
        default_factory=list, 
        description="Danh sách các đối tượng câu hỏi thô đã được LLM bóc tách."
    )


# ==========================================
# 2. Schemas cho API Responses (Giao tiếp Frontend)
# ==========================================

class AIJobCreateResponse(BaseModel):
    """
    Schema trả về ngay lập tức (HTTP 202) khi người dùng upload file thành công.
    Frontend sẽ sử dụng job_id này để mở kết nối WebSocket/SSE.
    """
    message: str = Field(
        ..., 
        example="File đề thi đã được tải lên và đang chờ AI xử lý."
    )
    job_id: int = Field(
        ..., 
        example=1024
    )


class AIJobStatusResponse(BaseModel):
    """
    Schema báo cáo trạng thái chi tiết của một tác vụ xử lý nền.
    Dùng cho các API RESTful (ví dụ: GET /jobs/{job_id}) để kiểm tra tiến độ.
    """
    id: int = Field(..., description="ID của tác vụ xử lý AI.")
    file_url: str = Field(..., description="Đường dẫn file vật lý lưu trên Storage (MinIO/S3).")
    
    status: Literal["pending", "processing", "done", "failed"] = Field(
        ..., 
        description="Trạng thái hiện tại của tác vụ."
    )
    
    result_exam_id: Optional[int] = Field(
        None, 
        description="ID của Exam được sinh ra trong DB sau khi AI xử lý xong. Chỉ có giá trị khi status là 'done'."
    )