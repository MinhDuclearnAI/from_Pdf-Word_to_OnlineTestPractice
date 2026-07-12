from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

# Import Database Dependencies
from app.api.deps import get_db, get_current_user, get_current_teacher

# Import Models
from app.models.user import User
from app.models.submission import Submission
from app.models.exam import Exam
from app.models.class_model import Class
from app.models.enrollment import ClassEnrollment

# Import Schemas
from app.schemas.submission import (
    SubmissionCreate, 
    SubmissionDraftUpdate, 
    SubmissionResult, 
    SubmissionBaseOut
)

# Import Services
# Giả định service này chứa logic đối chiếu answers với DB để tính điểm
from app.services import scoring_service 

# Import Exceptions
from app.core.exceptions import ResourceNotFoundError, PermissionDeniedError, BaseAppException

router = APIRouter()

# ==========================================
# 1. Nộp bài chính thức (POST /submissions)
# ==========================================
@router.post("/", response_model=SubmissionResult, status_code=status.HTTP_201_CREATED)
def submit_exam(
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Học sinh nộp bài thi. Hệ thống sẽ tự động chấm phần trắc nghiệm.
    Nếu có phần tự luận, trạng thái sẽ được chuyển thành 'pending_grading'.
    """
    # 1. Kiểm tra đề thi hợp lệ và còn hạn nộp
    exam = db.query(Exam).filter(Exam.id == submission_in.exam_id).first()
    if not exam:
        raise ResourceNotFoundError("Không tìm thấy đề thi này.")

    if exam.close_at and datetime.utcnow() > exam.close_at:
        raise BaseAppException("Đã quá thời gian nộp bài cho đề thi này.", status_code=400)

    # 2. Kiểm tra quyền truy cập của học sinh
    enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == exam.class_id,
        ClassEnrollment.student_id == current_user.id
    ).first()
    if not enrollment:
        raise PermissionDeniedError("Bạn không thuộc lớp học này.")

    # 3. Tính điểm phần trắc nghiệm và thống kê số câu
    # scoring_service sẽ trả về object chứa điểm, số câu đúng/sai và cờ báo có câu tự luận hay không
    score_result = scoring_service.calculate_exam_score(
        db=db, 
        exam_id=exam.id, 
        student_answers=submission_in.answers
    )

    # Xác định trạng thái cuối cùng
    final_status = "pending_grading" if score_result.has_essays else "completed"

    # 4. Lưu bài nộp vào DB
    new_submission = Submission(
        exam_id=exam.id,
        student_id=current_user.id,
        answers=submission_in.answers,
        status=final_status,
        score=score_result.total_score,
        submitted_at=datetime.utcnow()
    )
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    # 5. Kích hoạt luồng chấm AI tự luận ngầm nếu cần
    if final_status == "pending_grading":
        from app.tasks.grading_tasks import grade_essay_task
        grade_essay_task.delay(new_submission.id)

    # Convert object ORM sang Pydantic model để trả về
    result = SubmissionResult.model_validate(new_submission)
    result.correct_count = score_result.correct_count
    result.incorrect_count = score_result.incorrect_count
    result.unanswered_count = score_result.unanswered_count

    # Ẩn đáp án nếu cấu hình không cho phép xem chi tiết
    if exam.result_visibility == "score_only":
        result.answers = None

    return result


# ==========================================
# 2. Lưu nháp bài làm (PUT /submissions/{id}/autosave)
# ==========================================
@router.put("/{submission_id}/autosave", response_model=dict)
def autosave_submission(
    submission_id: int,
    draft_in: SubmissionDraftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tự động lưu trạng thái bài làm định kỳ từ Frontend để tránh mất dữ liệu.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise ResourceNotFoundError("Không tìm thấy phiên làm bài.")

    if submission.student_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền chỉnh sửa bài làm này.")

    if submission.status != "in_progress":
        raise BaseAppException("Bài thi đã được nộp, không thể lưu nháp thêm.", status_code=400)

    # Cập nhật cột JSONB
    submission.answers = draft_in.answers
    db.commit()

    return {"message": "Đã lưu nháp thành công."}


# ==========================================
# 3. Lấy chi tiết bài nộp của học sinh (GET /submissions/{id})
# ==========================================
@router.get("/{submission_id}", response_model=SubmissionResult)
def get_submission_details(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Xem chi tiết bài đã nộp, bao gồm điểm số và nhận xét của AI (nếu có).
    Áp dụng các rule bảo mật về hiển thị kết quả.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise ResourceNotFoundError("Không tìm thấy bài nộp.")

    exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()

    # Phân quyền: Học sinh tự xem bài mình HOẶC Giáo viên quản lý lớp xem bài học sinh
    is_owner = submission.student_id == current_user.id
    is_teacher = False

    if current_user.role == "teacher":
        target_class = db.query(Class).filter(Class.id == exam.class_id).first()
        is_teacher = target_class and target_class.teacher_id == current_user.id

    if not (is_owner or is_teacher):
        raise PermissionDeniedError("Bạn không có quyền xem chi tiết bài làm này.")

    result = SubmissionResult.model_validate(submission)

    # Xử lý luật ẩn/hiện kết quả (chỉ áp dụng chặn với học sinh, giáo viên luôn được xem đầy đủ)
    if not is_teacher:
        if exam.result_visibility == "score_only":
            result.answers = None
        elif exam.result_visibility == "after_close":
            if not exam.close_at or datetime.utcnow() <= exam.close_at:
                result.answers = None

    return result


# ==========================================
# 4. Giáo viên lấy danh sách nộp bài (GET /exams/{exam_id}/submissions)
# ==========================================
# Lưu ý: Tuy nằm trong prefix /submissions theo thiết kế của router.py, 
# nhưng để ngữ nghĩa chuẩn RESTful, ta thiết kế endpoint truyền thẳng exam_id ở query param.
@router.get("/", response_model=List[SubmissionBaseOut])
def get_exam_submissions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Lấy danh sách tất cả các bài nộp của một đề thi. Yêu cầu quyền Giáo viên quản lý.
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise ResourceNotFoundError("Không tìm thấy đề thi này.")

    target_class = db.query(Class).filter(Class.id == exam.class_id).first()
    if not target_class or target_class.teacher_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền truy cập dữ liệu của lớp này.")

    submissions = db.query(Submission).filter(Submission.exam_id == exam_id).all()
    return submissions