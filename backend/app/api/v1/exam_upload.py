import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session

# Import Database Dependencies
from app.api.deps import get_db, get_current_teacher

# Import Models
from app.models.user import User
from app.models.class_model import Class
from app.models.ai_job import AIProcessingJob

# Import Schemas
from app.schemas.ai_processing import AIJobCreateResponse

# Import Services & Background Tasks
from app.services.storage_service import storage
from app.tasks.exam_processing import process_exam_upload_task

# Import Exceptions
from app.core.exceptions import FileParsingError, ResourceNotFoundError, PermissionDeniedError

router = APIRouter()

# Danh sách các định dạng file được hệ thống AI hỗ trợ bóc tách
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}

# ==========================================
# 1. API: Upload file đề thi (POST /exams/upload)
# ==========================================
@router.post("/upload", response_model=AIJobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_exam_file(
    # Sử dụng Form(...) để nhận class_id gửi kèm theo file dạng multipart/form-data
    class_id: int = Form(..., description="ID của lớp học mà đề thi này thuộc về"),
    file: UploadFile = File(..., description="File đề thi định dạng PDF hoặc DOCX"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Tải lên file đề thi vật lý để hệ thống AI tự động bóc tách thành đề trực tuyến.
    Yêu cầu quyền Giáo viên (Teacher) và Giáo viên phải là người quản lý của class_id.
    """
    # 1. Kiểm tra tính hợp lệ của Lớp học (Phân quyền)
    target_class = db.query(Class).filter(Class.id == class_id).first()
    if not target_class:
        raise ResourceNotFoundError("Không tìm thấy lớp học yêu cầu.")
        
    if target_class.teacher_id != current_user.id:
        raise PermissionDeniedError("Bạn không có quyền tải đề thi lên lớp học này.")

    # 2. Kiểm tra định dạng file
    # Tách phần mở rộng (extension) từ tên file để kiểm tra
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileParsingError(
            f"Định dạng file '{ext}' không được hỗ trợ. Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    try:
        # 3. Tải file lên hệ thống lưu trữ đám mây (MinIO / S3)
        # Sử dụng storage service đã được cấu hình để stream file trực tiếp
        object_key = storage.upload_file(
            file_obj=file.file, 
            original_filename=file.filename,
            folder=f"exams/{target_class.id}"
        )

        # 4. Khởi tạo một AI Processing Job trong Database
        # Job này dùng để lưu trữ trạng thái tiến độ (pending -> processing -> done/failed)
        new_job = AIProcessingJob(
            file_url=object_key,
            status="pending"
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        # 5. Kích hoạt Celery Worker xử lý file dưới nền (Background Task)
        # Hàm .delay() giúp request này kết thúc ngay lập tức mà không phải chờ AI chạy 
        process_exam_upload_task.delay(
            job_id=new_job.id, 
            class_id=class_id
        )

        # 6. Trả về Response
        # Frontend sẽ sử dụng job_id này để kết nối WebSocket lắng nghe thanh Progress Bar
        return AIJobCreateResponse(
            message="File đã được tiếp nhận. Hệ thống AI đang tiến hành bóc tách...",
            job_id=new_job.id
        )

    except Exception as e:
        db.rollback()
        # Bắt các lỗi không mong muốn trong quá trình ghi file hoặc lưu DB
        raise FileParsingError(f"Có lỗi xảy ra trong quá trình tải lên và khởi tạo luồng AI: {str(e)}")