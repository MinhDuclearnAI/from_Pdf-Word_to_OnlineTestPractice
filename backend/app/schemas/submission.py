from typing import Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# ==========================================
# 1. Schemas cho Input (Học sinh thao tác)
# ==========================================

class SubmissionCreate(BaseModel):
    """
    Schema nhận dữ liệu khi học sinh bấm nộp bài chính thức (POST /submissions).
    """
    exam_id: int = Field(
        ..., 
        description="ID của đề thi mà học sinh đang làm."
    )
    answers: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Từ điển (Dictionary) map giữa question_id (chuỗi) và đáp án của học sinh. Ví dụ: {'q1': 'A', 'q2': 'Nội dung tự luận...'}"
    )


class SubmissionDraftUpdate(BaseModel):
    """
    Schema nhận dữ liệu khi hệ thống tự động lưu nháp (PUT /submissions/{id}/autosave).
    Chỉ yêu cầu truyền lên cục answers hiện tại để ghi đè vào bảng submission_draft.
    """
    answers: Dict[str, Any] = Field(
        ..., 
        description="Trạng thái bài làm hiện tại trên giao diện để lưu tạm."
    )


# ==========================================
# 2. Schemas cho Output (API Trả về)
# ==========================================

class SubmissionBaseOut(BaseModel):
    """
    Schema gốc chứa các trường thông tin chung của một lượt nộp bài.
    """
    id: int
    exam_id: int
    student_id: int
    status: Literal["in_progress", "submitted", "pending_grading", "completed"] = Field(
        ..., 
        description="Trạng thái bài làm: đang làm, đã nộp, chờ AI chấm tự luận, hoặc đã hoàn tất."
    )
    score: Optional[float] = Field(
        None, 
        description="Tổng điểm bài thi (Có thể là điểm quy đổi hệ 10 hoặc điểm thô)."
    )
    submitted_at: Optional[datetime] = Field(
        None, 
        description="Thời điểm học sinh nộp bài."
    )

    model_config = ConfigDict(from_attributes=True)


class SubmissionResult(SubmissionBaseOut):
    """
    Schema chi tiết trả về kết quả làm bài của học sinh.
    Sẽ được backend xử lý ẩn đi trường 'answers' nếu cấu hình đề thi (result_visibility) 
    chỉ cho phép xem điểm (score_only).
    """
    answers: Optional[Dict[str, Any]] = Field(
        None, 
        description="Chi tiết từng câu: Đáp án học sinh chọn, đúng/sai, và nhận xét của AI (nếu là tự luận)."
    )
    
    # Có thể thêm các trường thống kê phụ trợ để Frontend dễ render biểu đồ
    correct_count: Optional[int] = Field(None, description="Số câu làm đúng")
    incorrect_count: Optional[int] = Field(None, description="Số câu làm sai")
    unanswered_count: Optional[int] = Field(None, description="Số câu bỏ trống")