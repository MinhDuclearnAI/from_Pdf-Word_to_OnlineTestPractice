from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel, ConfigDict

# Import Database Dependencies
from app.api.deps import get_db, get_current_user

# Import Models
from app.models.user import User
from app.models.class_model import Class
from app.models.enrollment import ClassEnrollment
from app.models.submission import Submission
from app.models.exam import Exam

# Import Exceptions
from app.core.exceptions import ResourceNotFoundError, PermissionDeniedError

router = APIRouter()

# ==========================================
# Schemas cho Response Bảng xếp hạng
# ==========================================
class LeaderboardEntry(BaseModel):
    """
    Schema định dạng một dòng (1 học sinh) trong Bảng xếp hạng.
    """
    rank: int
    student_id: int
    student_email: str
    exams_taken: int
    total_score: float
    average_score: float

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Lấy Bảng xếp hạng của Lớp học (GET /classes/{class_id}/leaderboard)
# ==========================================
@router.get("/{class_id}/leaderboard", response_model=List[LeaderboardEntry])
def get_class_leaderboard(
    class_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Tính toán và trả về bảng xếp hạng của tất cả học sinh trong một lớp học.
    Xếp hạng ưu tiên theo: Tổng điểm (Total Score) giảm dần.
    Quyền truy cập: Giáo viên quản lý lớp hoặc Học sinh đang học trong lớp này.
    """
    # 1. Kiểm tra Lớp học tồn tại
    target_class = db.query(Class).filter(Class.id == class_id).first()
    if not target_class:
        raise ResourceNotFoundError("Không tìm thấy lớp học này.")

    # 2. Kiểm tra quyền truy cập (Phân quyền)
    if current_user.role == "teacher":
        if target_class.teacher_id != current_user.id:
            raise PermissionDeniedError("Bạn không có quyền xem bảng xếp hạng của lớp này.")
    else:
        # Nếu là học sinh, phải đảm bảo đã được thêm vào lớp
        enrollment = db.query(ClassEnrollment).filter(
            ClassEnrollment.class_id == class_id,
            ClassEnrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise PermissionDeniedError("Bạn không thuộc lớp học này nên không thể xem bảng xếp hạng.")

    # 3. Truy vấn tổng hợp (Aggregation Query) từ CSDL
    # - Kết nối Học sinh (User) -> Lớp học (ClassEnrollment) -> Đề thi (Exam) -> Bài làm (Submission)
    # - Chỉ tính các bài thi có trạng thái 'completed' (đã chấm xong)
    leaderboard_query = (
        db.query(
            User.id.label("student_id"),
            User.email.label("student_email"),
            func.count(Submission.id).label("exams_taken"),
            func.coalesce(func.sum(Submission.score), 0).label("total_score"),
            func.coalesce(func.avg(Submission.score), 0).label("average_score")
        )
        .join(ClassEnrollment, User.id == ClassEnrollment.student_id)
        .outerjoin(Exam, Exam.class_id == ClassEnrollment.class_id)
        .outerjoin(
            Submission, 
            (Submission.student_id == User.id) & 
            (Submission.exam_id == Exam.id) & 
            (Submission.status == "completed")
        )
        .filter(ClassEnrollment.class_id == class_id)
        .group_by(User.id, User.email)
        .order_by(desc(func.coalesce(func.sum(Submission.score), 0))) # Sắp xếp giảm dần theo tổng điểm
        .all()
    )

    # 4. Xử lý kết quả và gán thứ hạng (Rank)
    leaderboard_results = []
    current_rank = 1
    
    for row in leaderboard_query:
        leaderboard_results.append(
            LeaderboardEntry(
                rank=current_rank,
                student_id=row.student_id,
                student_email=row.student_email,
                exams_taken=row.exams_taken,
                total_score=round(row.total_score, 2),
                average_score=round(row.average_score, 2)
            )
        )
        current_rank += 1

    return leaderboard_results