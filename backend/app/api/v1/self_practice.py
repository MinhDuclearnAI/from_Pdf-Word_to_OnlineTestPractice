import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

# Import Database Dependencies
from app.api.deps import get_db, get_current_user

# Import Models
from app.models.user import User
from app.models.class_model import Class
from app.models.ai_job import AIProcessingJob
from app.models.enrollment import ClassEnrollment

# Import Schemas
from app.schemas.ai_processing import AIJobCreateResponse

# Import Services & Tasks
from app.services.storage_service import storage
from app.tasks.exam_processing import process_exam_upload_task

# Import Exceptions
from app.core.exceptions import FileParsingError

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}

def _get_or_create_personal_workspace(db: Session, student: User) -> int:
    """
    Hàm helper: Tìm hoặc tạo một 'Lớp học cá nhân' cho học sinh để chứa các đề tự luyện.
    Vì bảng Exam bắt buộc phải có class_id, ta tạo một Workspace riêng biệt.
    """
    workspace_name = f"Góc Luyện Tập - {student.email}"
    
    # 1. Tìm xem học sinh đã có workspace chưa
    personal_class = db.query(Class).filter(
        Class.name == workspace_name,
        # Giả sử subject đặc biệt để dễ filter sau này
        Class.subject == "Self-Practice" 
    ).first()

    # 2. Nếu chưa có, tiến hành tạo mới
    if not personal_class:
        personal_class = Class(
            name=workspace_name,
            subject="Self-Practice",
            # Với lớp tự luyện, học sinh đóng vai trò như 'người quản lý' của chính không gian đó.
            # Tùy thuộc vào thiết kế DB, bạn có thể để teacher_id = student.id hoặc nullable.
            teacher_id=student.id 
        )
        db.add(personal_class)
        db.commit()
        db.refresh(personal_class)
        
        # Tự động ghi danh học sinh vào lớp học này
        enrollment = ClassEnrollment(
            class_id=personal_class.id,
            student_id=student.id
        )
        db.add(enrollment)
        db.commit()

    return personal_class.id

# ==========================================
# API: Học sinh tự upload đề (POST /practice/upload-quick)
# ==========================================
@router.post("/upload-quick", response_model=AIJobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_self_practice_exam(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Chấp nhận cả role 'student'
):
    """
    API dành cho Học sinh tự tải file đề thi (PDF/DOCX) lên để hệ thống AI 
    bóc tách và tạo thành bài kiểm tra trực tuyến.
    """
    # 1. Kiểm tra định dạng file hợp lệ
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileParsingError(f"Định dạng file không được hỗ trợ. Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}")

    try:
        # 2. Lấy không gian làm việc cá nhân của học sinh
        personal_class_id = _get_or_create_personal_workspace(db, current_user)

        # 3. Upload file lên Storage (S3/MinIO)
        # Sử dụng thuộc tính .file của UploadFile (kiểu SpooledTemporaryFile) để đẩy thẳng lên S3
        object_key = storage.upload_file(
            file_obj=file.file, 
            original_filename=file.filename,
            folder=f"self_practice/{current_user.id}"
        )

        # 4. Tạo bản ghi Job để theo dõi trạng thái
        new_job = AIProcessingJob(
            file_url=object_key,
            status="pending",
            creator_id=current_user.id
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        # 5. Đẩy Task xử lý nền vào Celery Worker
        # Tái sử dụng hoàn toàn pipeline bóc tách đề của Giáo viên
        process_exam_upload_task.delay(
            job_id=new_job.id, 
            class_id=personal_class_id
        )

        # 6. Trả về Response chứa job_id để Frontend mở WebSocket
        return AIJobCreateResponse(
            message="Đề thi tự luyện đã được tiếp nhận. AI đang tiến hành bóc tách...",
            job_id=new_job.id
        )

    except Exception as e:
        db.rollback()
        raise FileParsingError(f"Có lỗi xảy ra trong quá trình upload đề tự luyện: {str(e)}")