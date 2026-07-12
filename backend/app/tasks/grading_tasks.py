import logging
from typing import Dict, Any

# Import Celery instance đã được cấu hình
from app.core.celery_app import celery_app

# Import Database session manager chuyên biệt cho background task
from app.db.session import get_db_session

# Import Models
from app.models.submission import Submission
from app.models.question import Question

# Import Service
from app.services.notification_service import notification

# Giả định bạn đã có hàm wrapper gọi AI trong ai_grading.py
# Hàm này sẽ sử dụng file grading_prompt.py và schema_validator.py mà ta đã viết
from app.services import ai_grading

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def grade_essay_task(self, submission_id: int) -> None:
    """
    Celery task để chấm điểm tự động các câu hỏi tự luận (Essay) bằng AI.
    
    Args:
        submission_id: ID của bản ghi Submission cần được chấm.
    """
    with get_db_session() as db:
        # 1. Truy xuất thông tin bài nộp (Submission)
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"Không tìm thấy Submission ID {submission_id} để chấm điểm.")
            return

        # Bỏ qua nếu bài đã chấm xong (tránh tình trạng double-grading nếu task bị duplicate)
        if submission.status == "COMPLETED":
            logger.info(f"Submission {submission_id} đã hoàn tất chấm điểm. Bỏ qua.")
            return

        try:
            # Bắn tín hiệu WebSocket báo UI hiển thị trạng thái "Đang chấm..."
            job_channel_id = f"grading_{submission_id}"
            notification.publish_job_status(
                job_id=job_channel_id,
                status="processing",
                progress=10,
                message="AI đang phân tích và chấm điểm các câu tự luận..."
            )

            # 2. Lấy danh sách các câu hỏi tự luận của bài thi này
            essay_questions = db.query(Question).filter(
                Question.exam_id == submission.exam_id,
                Question.component_type.in_(["essay", "writing"])
            ).all()

            total_ai_score = 0.0
            ai_feedbacks: Dict[str, Any] = {}
            total_essays = len(essay_questions)

            # 3. Lặp qua từng câu tự luận và gọi AI chấm
            for idx, question in enumerate(essay_questions, start=1):
                q_id_str = str(question.id)
                # Lấy bài làm của học sinh từ cột JSONB answers
                # (Ví dụ: submission.answers = {"1": "A", "2": "B", "3": "Bài làm tự luận..."})
                student_ans = submission.answers.get(q_id_str)

                # Cập nhật tiến độ
                progress = int(10 + (idx / total_essays) * 80)
                notification.publish_job_status(
                    job_id=job_channel_id,
                    status="processing",
                    progress=progress,
                    message=f"Đang chấm câu tự luận {idx}/{total_essays}..."
                )

                # Nếu học sinh bỏ trống
                if not student_ans or not str(student_ans).strip():
                    ai_feedbacks[q_id_str] = {
                        "score_earned": 0.0,
                        "feedback": "Học sinh không cung cấp câu trả lời.",
                        "is_correct": False
                    }
                    continue

                # Gọi AI Grading Service (Pass qua model answer và thang điểm)
                # Hàm này sẽ trả về object (Pydantic model) chứa: score_earned, feedback, is_correct
                grading_result = ai_grading.grade_essay_answer(
                    question_text=question.question_text,
                    model_answer=question.correct_answer,
                    student_answer=student_ans,
                    max_score=question.score_weight
                )

                # Cộng dồn điểm và lưu nhận xét
                total_ai_score += grading_result.score_earned
                # Chuyển Pydantic model thành dict để lưu vào JSONB
                ai_feedbacks[q_id_str] = grading_result.model_dump() 

            # 4. Cập nhật kết quả cuối cùng vào Database
            # Giả định submission.score đang lưu điểm trắc nghiệm (được tính từ scoring_service)
            current_score = float(submission.score or 0.0)
            submission.score = current_score + total_ai_score
            submission.status = "COMPLETED"

            # Lưu trực tiếp feedback của AI vào lại cột answers JSONB (hoặc một cột ai_feedbacks riêng nếu bạn có)
            # Dùng dict clone để báo cho SQLAlchemy biết JSONB có sự thay đổi
            updated_answers = dict(submission.answers)
            updated_answers["ai_feedbacks"] = ai_feedbacks
            submission.answers = updated_answers

            db.commit()

            # 5. Hoàn tất chu trình
            notification.publish_job_status(
                job_id=job_channel_id,
                status="done",
                progress=100,
                message="Đã chấm xong bài tự luận!",
                result_data={
                    "submission_id": submission_id, 
                    "final_score": submission.score
                }
            )
            logger.info(f"Đã chấm xong tự luận cho Submission ID {submission_id}. Tổng điểm AI: {total_ai_score}")

        except Exception as e:
            db.rollback()
            logger.error(f"Lỗi khi AI chấm bài tự luận (Submission {submission_id}): {str(e)}", exc_info=True)
            
            notification.publish_job_status(
                job_id=job_channel_id,
                status="failed",
                progress=0,
                message="Hệ thống AI gặp sự cố khi chấm bài. Vui lòng liên hệ giáo viên."
            )
            
            # Thử lại nếu lỗi xuất phát từ timeout mạng hoặc API AI
            raise self.retry(exc=e)