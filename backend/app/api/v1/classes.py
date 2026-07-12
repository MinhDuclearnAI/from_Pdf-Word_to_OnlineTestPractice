from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

# Import Database Dependencies
from app.api.deps import get_db, get_current_user, get_current_teacher

# Import Models
from app.models.user import User
from app.models.class_model import Class
from app.models.enrollment import ClassEnrollment

# Import Schemas (Giả định bạn có app/schemas/class_schema.py tương tự user.py)
# Nếu chưa có, bạn có thể tạo schema tương tự như phần dưới cùng của block code này.
from app.schemas.class_schema import ClassCreate, ClassOut
from app.schemas.user import UserOut

# Import Exceptions
from app.core.exceptions import ResourceNotFoundError, PermissionDeniedError, DuplicateResourceError, BaseAppException

router = APIRouter()

# ==========================================
# Schema nội bộ cho Payload thêm học sinh
# ==========================================
class AddStudentPayload(BaseModel):
    email: EmailStr


# ==========================================
# 1. Lấy danh sách Lớp học (GET /classes)
# ==========================================
@router.get("/", response_model=List[ClassOut])
def get_classes(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách các môn học/lớp học.
    - Nếu là Giáo viên: Trả về các lớp do giáo viên này giảng dạy.
    - Nếu là Học sinh: Trả về các lớp mà học sinh này đang tham gia.
    """
    if current_user.role == "teacher":
        classes = db.query(Class).filter(Class.teacher_id == current_user.id).all()
        return classes
    
    # Đối với vai trò 'student'
    enrolled_class_ids = (
        db.query(ClassEnrollment.class_id)
        .filter(ClassEnrollment.student_id == current_user.id)
        .subquery()
    )
    classes = db.query(Class).filter(Class.id.in_(enrolled_class_ids)).all()
    return classes


# ==========================================
# 2. Tạo Lớp học mới (POST /classes)
# ==========================================
@router.post("/", response_model=ClassOut, status_code=201)
def create_class(
    class_in: ClassCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_teacher)
):
    """
    Tạo một lớp học mới. Yêu cầu quyền Giáo viên (Teacher).
    """
    new_class = Class(
        name=class_in.name,
        subject=class_in.subject,
        teacher_id=current_user.id
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return new_class


# ==========================================
# 3. Lấy thông tin chi tiết một Lớp học (GET /classes/{id})
# ==========================================
@router.get("/{class_id}", response_model=ClassOut)
def get_class_details(
    class_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Lấy chi tiết lớp học. Phải là giáo viên quản lý lớp hoặc học sinh trong lớp mới xem được.
    """
    target_class = db.query(Class).filter(Class.id == class_id).first()
    if not target_class:
        raise ResourceNotFoundError("Không tìm thấy lớp học này.")

    # Phân quyền truy cập
    if current_user.role == "teacher" and target_class.teacher_id != current_user.id:
        raise PermissionDeniedError("Bạn không phải là giáo viên của lớp học này.")
        
    if current_user.role == "student":
        enrollment = db.query(ClassEnrollment).filter(
            ClassEnrollment.class_id == class_id,
            ClassEnrollment.student_id == current_user.id
        ).first()
        if not enrollment:
            raise PermissionDeniedError("Bạn chưa được thêm vào lớp học này.")

    return target_class


# ==========================================
# 4. Thêm học sinh vào lớp (POST /classes/{id}/students)
# ==========================================
@router.post("/{class_id}/students", status_code=201)
def add_student_to_class(
    class_id: int, 
    payload: AddStudentPayload, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_teacher)
):
    """
    Thêm học sinh vào lớp thông qua Email. Yêu cầu quyền Giáo viên quản lý lớp.
    """
    # 1. Kiểm tra lớp có tồn tại và thuộc quyền sở hữu không
    target_class = db.query(Class).filter(Class.id == class_id).first()
    if not target_class:
        raise ResourceNotFoundError("Không tìm thấy lớp học này.")
    if target_class.teacher_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền thêm học sinh vào lớp này.")

    # 2. Kiểm tra học sinh có tồn tại trong hệ thống không
    student = db.query(User).filter(User.email == payload.email, User.role == "student").first()
    if not student:
        raise ResourceNotFoundError("Không tìm thấy tài khoản học sinh với email này.")

    # 3. Kiểm tra xem học sinh đã ở trong lớp chưa
    existing_enrollment = db.query(ClassEnrollment).filter(
        ClassEnrollment.class_id == class_id,
        ClassEnrollment.student_id == student.id
    ).first()
    if existing_enrollment:
        raise DuplicateResourceError("Học sinh này đã nằm trong lớp.")

    # 4. Thêm vào bảng trung gian
    new_enrollment = ClassEnrollment(class_id=class_id, student_id=student.id)
    db.add(new_enrollment)
    db.commit()

    return {"message": f"Đã thêm học sinh {student.email} vào lớp thành công."}


# ==========================================
# 5. Lấy danh sách học sinh trong lớp (GET /classes/{id}/students)
# ==========================================
@router.get("/{class_id}/students", response_model=List[UserOut])
def get_students_in_class(
    class_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_teacher)
):
    """
    Xem danh sách học sinh trong một lớp. Yêu cầu quyền Giáo viên quản lý lớp.
    """
    target_class = db.query(Class).filter(Class.id == class_id).first()
    if not target_class or target_class.teacher_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền xem dữ liệu của lớp này.")

    # Join bảng User và ClassEnrollment
    students = (
        db.query(User)
        .join(ClassEnrollment, User.id == ClassEnrollment.student_id)
        .filter(ClassEnrollment.class_id == class_id)
        .all()
    )
    
    return students