from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

# Import Database Dependencies
from app.api.deps import get_db, get_current_user, get_current_teacher

# Import Models
from app.models.user import User
from app.models.class_model import Class
from app.models.exam import Exam
from app.models.enrollment import ClassEnrollment
from app.models.submission import Submission

# Import Schemas
from app.schemas.exam import ExamOut, ExamConfig, ExamUpdate

# Import Exceptions
from app.core.exceptions import ResourceNotFoundError, PermissionDeniedError

router = APIRouter()

def _check_teacher_exam_permission(db: Session, exam_id: int, teacher_id: int) -> Exam:
    """Helper function: Kiểm tra xem đề thi có tồn tại và giáo viên có quyền quản lý không."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise ResourceNotFoundError("Không tìm thấy đề thi này.")
        
    target_class = db.query(Class).filter(Class.id == exam.class_id).first()
    if not target_class or target_class.teacher_id != teacher_id:
        raise PermissionDeniedError("Bạn không có quyền quản lý đề thi của lớp này.")
        
    return exam

# ==========================================
# 1. Lấy thông tin chi tiết Đề thi (GET /exams/{id})
# ==========================================
@router.get("/{exam_id}", response_model=ExamOut)
def get_exam_details(
    exam_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Lấy thông tin chi tiết cấu hình của một đề thi.
    Giáo viên quản lý lớp hoặc Học sinh thuộc lớp đó mới được xem.
    """
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise ResourceNotFoundError("Không tìm thấy đề thi.")

    if current_user.role == "student":
        # Kiểm tra học sinh có trong lớp không
        enrollment = db.query(ClassEnrollment).filter(
            ClassEnrollment.class_id == exam.class_id,
            ClassEnrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise PermissionDeniedError("Bạn không thuộc lớp học chứa đề thi này.")
    else:
        # Kiểm tra quyền giáo viên
        _check_teacher_exam_permission(db, exam_id, current_user.id)

    return exam

# ==========================================
# 2. Cấu hình Đề thi (PATCH /exams/{id}/config)
# ==========================================
@router.patch("/{exam_id}/config", response_model=ExamOut)
def config_exam(
    exam_id: int, 
    config_in: ExamConfig, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_teacher)
):
    """
    Cập nhật cấu hình đề thi (thời gian làm bài, đóng/mở, quyền xem kết quả).
    Yêu cầu quyền Giáo viên quản lý lớp.
    """
    exam = _check_teacher_exam_permission(db, exam_id, current_user.id)

    # Cập nhật các trường được gửi lên
    update_data = config_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exam, field, value)

    db.commit()
    db.refresh(exam)
    return exam

# ==========================================
# 3. Xuất bản Đề thi (POST /exams/{id}/publish)
# ==========================================
@router.post("/{exam_id}/publish", response_model=ExamOut)
def publish_exam(
    exam_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_teacher)
):
    """
    Đóng băng cấu hình và xuất bản đề thi ngay lập tức.
    Hành động này sẽ cập nhật `open_at` thành thời gian hiện tại nếu chưa được set.
    """
    exam = _check_teacher_exam_permission(db, exam_id, current_user.id)

    # Nếu chưa có thời gian mở, set thành ngay bây giờ
    if not exam.open_at:
        exam.open_at = datetime.utcnow()
    
    db.commit()
    db.refresh(exam)
    
    return exam

# ==========================================
# 4. Thống kê & Phổ điểm (GET /exams/{id}/stats)
# ==========================================
@router.get("/{exam_id}/stats")
def get_exam_statistics(
    exam_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """
    Lấy thống kê kết quả làm bài của lớp: Số lượng nộp bài, Điểm trung bình/cao nhất/thấp nhất, và Phổ điểm.
    Yêu cầu quyền Giáo viên quản lý lớp.
    """
    exam = _check_teacher_exam_permission(db, exam_id, current_user.id)

    # Lấy tất cả các bài nộp đã hoàn tất chấm điểm
    completed_submissions = db.query(Submission).filter(
        Submission.exam_id == exam_id,
        Submission.status == "completed",
        Submission.score.isnot(None)
    ).all()

    total_submissions = len(completed_submissions)
    if total_submissions == 0:
        return {
            "total_submissions": 0,
            "average_score": 0.0,
            "highest_score": 0.0,
            "lowest_score": 0.0,
            "score_distribution": []
        }

    scores = [sub.score for sub in completed_submissions]
    
    # Tính toán phổ điểm (Gom nhóm theo điểm số để vẽ biểu đồ)
    distribution_query = (
        db.query(Submission.score, func.count(Submission.id).label("student_count"))
        .filter(Submission.exam_id == exam_id, Submission.status == "completed")
        .group_by(Submission.score)
        .order_by(Submission.score)
        .all()
    )

    score_distribution = [
        {"score": float(row.score), "count": row.student_count}
        for row in distribution_query if row.score is not None
    ]

    return {
        "total_submissions": total_submissions,
        "average_score": round(sum(scores) / total_submissions, 2),
        "highest_score": float(max(scores)),
        "lowest_score": float(min(scores)),
        "score_distribution": score_distribution
    }

# ==========================================
# 5. Xóa Đề thi (DELETE /exams/{id})
# ==========================================
@router.delete("/{exam_id}", status_code=204)
def delete_exam(
    exam_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_teacher)
):
    """
    Xóa một đề thi khỏi hệ thống. Yêu cầu quyền Giáo viên quản lý lớp.
    """
    exam = _check_teacher_exam_permission(db, exam_id, current_user.id)
    
    db.delete(exam)
    db.commit()
    
    return None