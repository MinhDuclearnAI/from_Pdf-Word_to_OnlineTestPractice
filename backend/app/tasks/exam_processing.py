import os
import logging
from typing import Any

# Import Celery instance đã được cấu hình
from app.core.celery_app import celery_app

# Import Database session manager (Context manager chuyên cho background tasks)
from app.db.session import get_db_session

# Import Models
from app.models.ai_job import AIProcessingJob
from app.models.exam import Exam
from app.models.question import Question

# Import Services
from app.services.storage_service import storage
from app.services.notification_service import notification

# Giả định bạn có các module sau trong services (Dựa trên cấu trúc Giai đoạn 2)
from app.services import file_extractor
from app.services import ai_parser

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_exam_upload_task(self, job_id: int, class_id: int) -> None:
    """
    Celery task xử lý toàn bộ vòng đời của việc bóc tách đề thi bằng AI.
    
    Args:
        job_id: ID của bản ghi AIProcessingJob trong database.
        class_id: ID của lớp học mà đề thi này thuộc về.
    """
    # Mở một Database Session an toàn
    with get_db_session() as db:
        # 1. Lấy thông tin công việc từ DB
        job = db.query(AIProcessingJob).filter(AIProcessingJob.id == job_id).first()
        if not job:
            logger.error(f"Không tìm thấy Job ID {job_id} trong database.")
            return

        try:
            # 2. Cập nhật trạng thái bắt đầu xử lý
            job.status = "processing"
            db.commit()
            notification.publish_job_status(job_id, "processing", 10, "Đang khởi tạo tiến trình xử lý...")

            # 3. Tải file từ Storage (MinIO/S3) về môi trường local của Worker
            notification.publish_job_status(job_id, "processing", 20, "Đang tải file vật lý về hệ thống...")
            local_file_path = storage.download_file_to_local(job.file_url)

            # 4. Trích xuất Text/Hình ảnh từ File (Sử dụng PyMuPDF/python-docx)
            notification.publish_job_status(job_id, "processing", 40, "Đang đọc và trích xuất nội dung văn bản...")
            document_text = file_extractor.extract_text(local_file_path)
            
            if not document_text or len(document_text.strip()) < 50:
                raise ValueError("Không thể trích xuất văn bản từ file hoặc file quá ngắn.")

            # 5. Pass 1: Phân loại tổng quan (Gọi LLM qua ai_parser)
            notification.publish_job_status(job_id, "processing", 50, "AI đang phân loại môn học và dạng đề...")
            # Trả về Pydantic schema: ClassificationResult
            classification = ai_parser.classify_document(document_text)

            # 6. Pass 2: Bóc tách từng câu hỏi (Gọi LLM qua ai_parser)
            notification.publish_job_status(job_id, "processing", 70, "AI đang bóc tách từng câu hỏi và gán nhãn...")
            # Trả về Pydantic schema: ExamExtractionSchema (chứa danh sách câu hỏi)
            parsed_exam = ai_parser.extract_questions(document_text)

            # 7. Lưu dữ liệu vào Database
            notification.publish_job_status(job_id, "processing", 90, "Đang lưu cấu trúc bài thi vào Database...")
            
            # 7.1 Tạo bản ghi Exam mới
            new_exam = Exam(
                class_id=class_id,
                title=classification.title or "Đề thi tự động (AI Generated)",
                subject=classification.subject,
                test_type=classification.test_type,
                duration=classification.duration or 60,  # Mặc định 60 phút nếu AI không tìm thấy
                result_visibility="detailed"
            )
            db.add(new_exam)
            db.flush() # Lấy ID của exam ngay lập tức

            # 7.2 Tạo danh sách các câu hỏi thuộc về Exam này
            for q_data in parsed_exam.questions:
                new_question = Question(
                    exam_id=new_exam.id,
                    component_type=q_data.type,
                    question_text=q_data.question_text,
                    # Chuyển Pydantic list sang định dạng JSON mà PostgreSQL hỗ trợ (JSONB)
                    options=q_data.options if q_data.options else [],
                    correct_answer=q_data.correct_answer,
                    score_weight=q_data.score_weight,
                    passage_ref=q_data.passage_ref,
                )
                db.add(new_question)

            # 8. Hoàn tất chu trình
            job.status = "done"
            job.result_exam_id = new_exam.id
            db.commit() # Lưu toàn bộ (Exam + Questions + Job status)
            
            # Xóa file rác ở local worker để giải phóng ổ cứng
            if os.path.exists(local_file_path):
                os.remove(local_file_path)

            # Bắn thông báo Done, kèm theo exam_id để Frontend tự động redirect sang trang xem đề
            notification.publish_job_status(
                job_id, 
                "done", 
                100, 
                "Hoàn thành bóc tách đề thi!",
                result_data={"exam_id": new_exam.id}
            )
            logger.info(f"Đã xử lý xong Job ID {job_id}. Tạo thành công Exam ID {new_exam.id}.")

        except Exception as e:
            # Bắt lỗi, rollback và thông báo về Frontend
            db.rollback()
            job.status = "failed"
            db.commit()
            
            error_msg = str(e)
            logger.error(f"Lỗi khi xử lý Job {job_id}: {error_msg}", exc_info=True)
            
            # Nếu là lỗi do mạng hoặc API AI quá tải, thử lại (retry)
            if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                try:
                    logger.info(f"Đang thử lại Job {job_id} (Retries: {self.request.retries})")
                    raise self.retry(exc=e)
                except self.MaxRetriesExceededError:
                    error_msg = "Máy chủ AI đang quá tải. Đã thử lại nhiều lần nhưng thất bại."
            
            notification.publish_job_status(job_id, "failed", 0, f"Lỗi xử lý: {error_msg}")
            
            # Cố gắng xóa file rác (nếu tồn tại) khi gặp lỗi
            if 'local_file_path' in locals() and os.path.exists(local_file_path):
                os.remove(local_file_path)