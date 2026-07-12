from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import Dependencies
from app.api.deps import get_db, get_current_teacher

# Import Models
from app.models.user import User
from app.models.submission import Submission
from app.models.exam import Exam
from app.models.class_model import Class

# Import Celery Task
from app.tasks.grading_tasks import grade_essay_task

# Import Exceptions
from app.core.exceptions import ResourceNotFoundError, PermissionDeniedError

router = APIRouter()

# ==========================================
# Schema nội bộ cho Response
# ==========================================
class GradeEssayResponse(BaseModel):
    message: str
    submission_id: int


# ==========================================
# Kích hoạt luồng chấm điểm tự luận bằng AI
# ==========================================
@router.post("/{submission_id}/grade-essay", response_model=GradeEssayResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_essay_grading(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Kích hoạt luồng chấm điểm tự luận (Essay/Writing) bằng AI cho một bài nộp cụ thể.
    Yêu cầu quyền Giáo viên quản lý lớp học chứa bài thi này.
    Tiến trình chấm sẽ diễn ra bất đồng bộ (Background Task).
    """
    # 1. Tìm bản ghi Submission trong Database
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise ResourceNotFoundError("Không tìm thấy bài nộp (Submission) này.")

    # 2. Kiểm tra quyền truy cập của Giáo viên
    # Phải đảm bảo Giáo viên này là người quản lý lớp học chứa bài thi
    exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
    if not exam:
        raise ResourceNotFoundError("Không tìm thấy đề thi liên kết với bài nộp này.")
        
    target_class = db.query(Class).filter(Class.id == exam.class_id).first()
    if not target_class or target_class.teacher_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền yêu cầu chấm bài của học sinh thuộc lớp này.")

    # 3. Cập nhật trạng thái bài nộp
    # Chuyển trạng thái về pending_grading để UI Frontend có thể hiển thị thanh trạng thái "Đang chờ chấm..."
    submission.status = "pending_grading"
    db.commit()

    # 4. Đẩy Task vào hàng đợi Celery (Redis)
    # Sử dụng .delay() để hàm chạy nền, không làm treo request của người dùng
    grade_essay_task.delay(submission_id)

    # 5. Trả về phản hồi ngay lập tức (HTTP 202 Accepted)
    return GradeEssayResponse(
        message="Đã đẩy yêu cầu chấm điểm tự luận vào hàng đợi AI thành công.",
        submission_id=submission_id
    )