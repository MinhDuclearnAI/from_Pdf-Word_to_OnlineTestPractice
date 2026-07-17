# import os
# import logging
# from typing import Any

# # Import Celery instance đã được cấu hình
# from app.core.celery_app import celery_app

# # Import Database session manager (Context manager chuyên cho background tasks)
# from app.db.session import get_db_session

# # Import Models
# from app.models.ai_job import AIProcessingJob
# from app.models.exam import Exam
# from app.models.question import Question

# # Import Services
# from app.services.storage_service import storage
# from app.services.notification_service import notification

# # Giả định bạn có các module sau trong services (Dựa trên cấu trúc Giai đoạn 2)
# from app.services import file_extractor
# from app.services.ai_parser import ai_parser

# logger = logging.getLogger(__name__)

# # Giá trị form UI không trùng hoàn toàn với enum ExamType trong database.
# # Giữ mapping tại ranh giới task để DB chỉ nhận các giá trị hợp lệ.
# EXAM_TYPE_MAP = {
#     "exam": "test",
#     "test": "test",
#     "homework": "practice",
#     "practice": "practice",
# }

# @celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
# def process_exam_upload_task(self, job_id: int, class_id: int, title: str, subject: str, duration: int, test_type: str) -> None:
#     """
#     Celery task xử lý toàn bộ vòng đời của việc bóc tách đề thi bằng AI.
    
#     Args:
#         job_id: ID của bản ghi AIProcessingJob trong database.
#         class_id: ID của lớp học mà đề thi này thuộc về.
#         title: Tiêu đề do giáo viên chỉ định.
#         subject: Môn học do giáo viên chỉ định.
#         duration: Thời gian làm bài do giáo viên chỉ định.
#         test_type: Dạng bài thi do giáo viên chỉ định.
#     """
#     # Mở một Database Session an toàn
#     with get_db_session() as db:
#         # 1. Lấy thông tin công việc từ DB
#         job = db.query(AIProcessingJob).filter(AIProcessingJob.id == job_id).first()
#         if not job:
#             logger.error(f"Không tìm thấy Job ID {job_id} trong database.")
#             return

#         try:
#             # 2. Cập nhật trạng thái bắt đầu xử lý
#             job.status = "processing"
#             db.commit()
#             notification.publish_job_status(job_id, "processing", 10, "Đang khởi tạo tiến trình xử lý...")

#             # 3. Tải file từ Storage (MinIO/S3) về môi trường local của Worker
#             notification.publish_job_status(job_id, "processing", 20, "Đang tải file vật lý về hệ thống...")
#             local_file_path = storage.download_file_to_local(job.file_url)

#             # 4. Trích xuất Text/Hình ảnh từ File (Sử dụng PyMuPDF/python-docx)
#             notification.publish_job_status(job_id, "processing", 40, "Đang đọc và trích xuất nội dung văn bản...")
            
#             # Xác định mime_type dựa trên đuôi file
#             import mimetypes
#             mime_type, _ = mimetypes.guess_type(local_file_path)
#             if not mime_type:
#                 if local_file_path.endswith('.pdf'):
#                     mime_type = "application/pdf"
#                 elif local_file_path.endswith('.docx'):
#                     mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
#                 else:
#                     mime_type = "application/octet-stream"

#             document_text = file_extractor.process_file(local_file_path, mime_type)
            
#             if not document_text or len(document_text.strip()) < 50:
#                 raise ValueError("Không thể trích xuất văn bản từ file hoặc file quá ngắn.")

#             # Bỏ qua bước 5 (AI phân loại) vì giáo viên đã thiết lập bắt buộc trên giao diện

#             # 6. Pass 2: Bóc tách từng câu hỏi (Gọi LLM qua ai_parser)
#             notification.publish_job_status(job_id, "processing", 60, "AI đang bóc tách từng câu hỏi và gán nhãn...")
#             # Trả về Pydantic schema: ExamExtractionSchema (chứa danh sách câu hỏi)
#             parsed_exam = ai_parser.extract_questions(document_text)

#             # 7. Lưu dữ liệu vào Database
#             notification.publish_job_status(job_id, "processing", 90, "Đang lưu cấu trúc bài thi vào Database...")
            
#             normalized_exam_type = EXAM_TYPE_MAP.get(test_type)
#             if not normalized_exam_type:
#                 raise ValueError(f"Dạng bài thi không hợp lệ: {test_type}")

#             # 7.1 Tạo bản ghi Exam mới
#             new_exam = Exam(
#                 class_id=class_id,
#                 title=title,
#                 subject=subject,
#                 exam_type=normalized_exam_type,
#                 duration=duration,
#                 result_visibility="full", # Note: DB ResultVisibility has full, score_only, hidden
#                 creator_id=job.creator_id
#             )
#             db.add(new_exam)
#             db.flush() # Lấy ID của exam ngay lập tức

#             # 7.2 Tạo danh sách các câu hỏi thuộc về Exam này
#             for q_data in parsed_exam.questions:
#                 # Map component types from schema literals to DB model enum
#                 db_type = q_data.type
#                 if db_type == "latex_formula":
#                     db_type = "math_equation"
#                 elif db_type == "writing":
#                     db_type = "essay"
#                 elif db_type == "fill_blank":
#                     db_type = "fill_in_the_blank"

#                 new_question = Question(
#                     exam_id=new_exam.id,
#                     component_type=db_type,
#                     question_text=q_data.question_text,
#                     # Chuyển Pydantic list sang định dạng JSON mà PostgreSQL hỗ trợ (JSONB)
#                     options=q_data.options if q_data.options else [],
#                     correct_answer=q_data.correct_answer,
#                     score_weight=q_data.score_weight,
#                     passage_ref=q_data.passage_ref,
#                 )
#                 db.add(new_question)

#             # 8. Hoàn tất chu trình
#             job.status = "completed" # DB enum has completed, not done
#             job.result_exam_id = new_exam.id
#             db.commit() # Lưu toàn bộ (Exam + Questions + Job status)
            
#             # Xóa file rác ở local worker để giải phóng ổ cứng
#             if os.path.exists(local_file_path):
#                 os.remove(local_file_path)

#             # Bắn thông báo Done, kèm theo exam_id để Frontend tự động redirect sang trang xem đề
#             notification.publish_job_status(
#                 job_id, 
#                 "done", 
#                 100, 
#                 "Hoàn thành bóc tách đề thi!",
#                 result_data={"exam_id": new_exam.id}
#             )
#             logger.info(f"Đã xử lý xong Job ID {job_id}. Tạo thành công Exam ID {new_exam.id}.")

#         except Exception as e:
#             # Bắt lỗi, rollback và thông báo về Frontend
#             db.rollback()
#             job.status = "failed"
            
#             error_msg = str(e)
#             job.error_message = error_msg
#             db.commit()
#             logger.error(f"Lỗi khi xử lý Job {job_id}: {error_msg}", exc_info=True)
            
#             # Nếu là lỗi do mạng hoặc API AI quá tải, thử lại (retry)
#             if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
#                 try:
#                     logger.info(f"Đang thử lại Job {job_id} (Retries: {self.request.retries})")
#                     raise self.retry(exc=e)
#                 except self.MaxRetriesExceededError:
#                     error_msg = "Máy chủ AI đang quá tải. Đã thử lại nhiều lần nhưng thất bại."
            
#             notification.publish_job_status(job_id, "failed", 0, f"Lỗi xử lý: {error_msg}")
            
#             # Cố gắng xóa file rác (nếu tồn tại) khi gặp lỗi
#             if 'local_file_path' in locals() and os.path.exists(local_file_path):
#                 os.remove(local_file_path)

#             # Không che lỗi nghiệp vụ bằng trạng thái Celery "succeeded".
#             # Khi không phải một retry đang chờ, task phải được ghi nhận thất bại.
#             raise

import os
import logging
from typing import Any
import mimetypes

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
from app.services.ai_parser import ai_parser

logger = logging.getLogger(__name__)

# Giá trị form UI không trùng hoàn toàn với enum ExamType trong database.
EXAM_TYPE_MAP = {
    "exam": "test",
    "test": "test",
    "homework": "practice",
    "practice": "practice",
}

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_exam_upload_task(self, job_id: int, class_id: int, title: str, subject: str, duration: int, test_type: str) -> None:
    """
    Celery task xử lý toàn bộ vòng đời của việc bóc tách đề thi bằng AI.
    """
    # Khởi tạo biến lưu đường dẫn file để luôn được dọn dẹp trong block `finally`
    local_file_path = None

    with get_db_session() as db:
        # 1. Lấy thông tin công việc từ DB
        job = db.query(AIProcessingJob).filter(AIProcessingJob.id == job_id).first()
        if not job:
            logger.error(f"Không tìm thấy Job ID {job_id} trong database.")
            return

        # [FIX]: Tính lũy đẳng (Idempotency). Đảm bảo task retry không tạo data trùng lặp.
        if job.status == "completed":
            logger.info(f"Job ID {job_id} đã hoàn thành trước đó. Bỏ qua.")
            return

        try:
            # 2. Cập nhật trạng thái bắt đầu xử lý
            job.status = "processing"
            db.commit()
            notification.publish_job_status(job_id, "processing", 10, "Đang khởi tạo tiến trình xử lý...")

            # 3. Tải file từ Storage về môi trường local của Worker
            notification.publish_job_status(job_id, "processing", 20, "Đang tải file vật lý về hệ thống...")
            local_file_path = storage.download_file_to_local(job.file_url)

            # 4. Trích xuất Text/Hình ảnh từ File
            notification.publish_job_status(job_id, "processing", 40, "Đang đọc và trích xuất nội dung văn bản...")
            
            mime_type, _ = mimetypes.guess_type(local_file_path)
            if not mime_type:
                if local_file_path.endswith('.pdf'):
                    mime_type = "application/pdf"
                elif local_file_path.endswith('.docx'):
                    mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                else:
                    mime_type = "application/octet-stream"

            document_text = file_extractor.process_file(local_file_path, mime_type)
            
            if not document_text or len(document_text.strip()) < 50:
                raise ValueError("Không thể trích xuất văn bản từ file hoặc file quá ngắn.")

            # 6. Pass 2: Bóc tách từng câu hỏi qua AI
            notification.publish_job_status(job_id, "processing", 60, "AI đang bóc tách từng câu hỏi và gán nhãn...")
            parsed_exam = ai_parser.extract_questions(document_text)

            # 7. Lưu dữ liệu vào Database
            notification.publish_job_status(job_id, "processing", 90, "Đang lưu cấu trúc bài thi vào Database...")
            
            normalized_exam_type = EXAM_TYPE_MAP.get(test_type)
            if not normalized_exam_type:
                raise ValueError(f"Dạng bài thi không hợp lệ: {test_type}")

            # [FIX]: Dùng nested try-except để cô lập lỗi Insert Data với lỗi Job Tracking
            try:
                new_exam = Exam(
                    class_id=class_id,
                    title=title,
                    subject=subject,
                    exam_type=normalized_exam_type,
                    duration=duration,
                    result_visibility="full",
                    creator_id=job.creator_id
                )
                db.add(new_exam)
                db.flush() 

                for q_data in parsed_exam.questions:
                    db_type = q_data.type
                    if db_type == "latex_formula":
                        db_type = "math_equation"
                    elif db_type == "writing":
                        db_type = "essay"
                    elif db_type == "fill_blank":
                        db_type = "fill_in_the_blank"

                    new_question = Question(
                        exam_id=new_exam.id,
                        component_type=db_type,
                        question_text=q_data.question_text,
                        options=q_data.options if q_data.options else [],
                        correct_answer=q_data.correct_answer,
                        score_weight=q_data.score_weight,
                        passage_ref=q_data.passage_ref,
                    )
                    db.add(new_question)

                # 8. Hoàn tất chu trình
                job.status = "completed"
                job.result_exam_id = new_exam.id
                db.commit()
            except Exception as db_err:
                db.rollback()
                raise Exception(f"Lỗi khi lưu dữ liệu bài thi vào DB: {str(db_err)}")

            # 9. Bắn thông báo Done
            notification.publish_job_status(
                job_id, "done", 100, "Hoàn thành bóc tách đề thi!",
                result_data={"exam_id": new_exam.id}
            )
            logger.info(f"Đã xử lý xong Job ID {job_id}. Tạo thành công Exam ID {new_exam.id}.")

        except Exception as e:
            # Revert các state chưa được commit ở block nghiệp vụ (nếu có)
            db.rollback()
            error_msg = str(e)
            
            # [FIX]: Kiểm tra điều kiện retry TRƯỚC KHI lưu trạng thái "failed"
            if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                try:
                    logger.warning(f"Lỗi mạng/AI tải, đang thử lại Job {job_id} (Retries: {self.request.retries})")
                    # Celery bắt exception này, tạm dừng và sẽ chạy lại task. Block `finally` vẫn được gọi.
                    raise self.retry(exc=e) 
                except self.MaxRetriesExceededError:
                    error_msg = "Máy chủ AI đang quá tải. Đã thử lại nhiều lần nhưng thất bại."

            # [FIX]: Nếu chạy đến đây tức là Hết lượt Retry HOẶC Lỗi không thể Retry (Logic, Validate)
            logger.error(f"Lỗi khi xử lý Job {job_id} (Failed vĩnh viễn): {error_msg}", exc_info=True)
            
            try:
                job.status = "failed"
                job.error_message = error_msg
                db.commit()
            except Exception:
                db.rollback()
                logger.error("Không thể cập nhật trạng thái failed vào DB cho Job.", exc_info=True)

            notification.publish_job_status(job_id, "failed", 0, f"Lỗi xử lý: {error_msg}")
            
            # Raise để Celery UI/Flower ghi nhận task là Thất bại hoàn toàn (Màu đỏ)
            raise 

        finally:
            # [FIX]: Luôn luôn dọn dẹp file rác dù task thành công, bị lỗi vĩnh viễn, hay đang chờ retry
            if local_file_path and os.path.exists(local_file_path):
                try:
                    os.remove(local_file_path)
                    logger.debug(f"Đã xóa file tạm thời: {local_file_path}")
                except Exception as cleanup_err:
                    logger.error(f"Lỗi khi xóa file tạm {local_file_path}: {cleanup_err}")