import json
import logging
from typing import Optional, Dict
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from app.config import settings
from app.services.schema_validator import safe_json_parse
from app.core.exceptions import FileParsingError # Hoặc tạo thêm AIGradingError riêng

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Cấu trúc Schema đầu ra (có thể chuyển sang app/schemas/ai_processing.py)
# ---------------------------------------------------------
class GradingResult(BaseModel):
    explanation: str = Field(..., description="Phân tích chi tiết Chain-of-Thought so sánh bài làm với đáp án chuẩn.")
    criteria_breakdown: Optional[Dict[str, float]] = Field(
        default=None, 
        description="Điểm chi tiết cho từng phần nếu rubric có quy định (VD: {'logic': 1.0, 'ngu_phap': 0.5})."
    )
    score: float = Field(..., description="Điểm số tổng kết cuối cùng.")

# ---------------------------------------------------------
# System Prompt 
# ---------------------------------------------------------
GRADING_SYSTEM_PROMPT = """
Bạn là một giám khảo chấm thi AI vô tư, khách quan và nghiêm ngặt. 
Nhiệm vụ của bạn là chấm điểm bài làm tự luận của học sinh dựa trên Câu hỏi, Đáp án chuẩn (Model Answer), và Hướng dẫn chấm (Rubric).

Yêu cầu BẮT BUỘC:
1. Đọc kỹ câu hỏi và đáp án chuẩn.
2. Viết 'explanation' (lời giải thích) TRƯỚC khi đưa ra 'score' (điểm số). Đây là bước suy luận logic (Chain of Thought) để tránh chấm điểm cảm tính.
3. Nếu học sinh có ý đúng nhưng diễn đạt khác đáp án chuẩn, vẫn phải chấm điểm linh hoạt dựa trên ngữ nghĩa.
4. Tổng điểm ('score') TUYỆT ĐỐI KHÔNG ĐƯỢC VƯỢT QUÁ Điểm tối đa (Max Score).
5. KẾT QUẢ TRẢ VỀ PHẢI LÀ MỘT ĐỐI TƯỢNG JSON DUY NHẤT.
"""

class AIGradingService:
    """
    Service xử lý nghiệp vụ chấm điểm tự luận tự động bằng mô hình LLM.
    Được thiết kế để chạy bất đồng bộ trong Celery Worker.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.GEMINI_API_KEY, base_url=settings.GEMINI_BASE_URL)
        self.model = settings.DEFAULT_GRADING_MODEL
        self.max_retries = 3

    def grade_essay_answer(
        self, 
        question_text: str, 
        student_answer: str, 
        model_answer: str, 
        max_score: float, 
        rubric: Optional[str] = None
    ) -> GradingResult:
        """
        Thực hiện chấm điểm một câu hỏi tự luận.
        
        Args:
            question_text: Nội dung câu hỏi.
            student_answer: Câu trả lời thực tế của học sinh.
            model_answer: Đáp án chuẩn (Gợi ý).
            max_score: Điểm tối đa cho câu hỏi này.
            rubric: Tiêu chí chấm điểm chi tiết (nếu có).
            
        Returns:
            GradingResult: Đối tượng chứa điểm số và lời phê.
        """
        # Nếu học sinh bỏ trống, trả về 0 điểm ngay để tiết kiệm API call
        if not student_answer or not student_answer.strip():
            return GradingResult(
                explanation="Học sinh không có câu trả lời cho câu hỏi này.",
                score=0.0
            )

        # Build user prompt payload
        user_prompt = f"""
        Vui lòng chấm điểm bài làm sau:
        
        <question>
        {question_text}
        </question>
        
        <model_answer>
        {model_answer}
        </model_answer>
        
        <max_score>
        {max_score}
        </max_score>
        """
        
        if rubric:
            user_prompt += f"\n<rubric>\n{rubric}\n</rubric>\n"
            
        user_prompt += f"""
        <student_answer>
        {student_answer}
        </student_answer>
        """

        attempt = 0
        while attempt < self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": GRADING_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                
                raw_json = response.choices[0].message.content
                result = safe_json_parse(raw_json, GradingResult)
                
                # Hậu kiểm điểm số: Đảm bảo AI không sinh ra điểm lớn hơn max_score do lỗi logic
                if result.score > max_score:
                    logger.warning(f"AI chấm điểm vượt trần ({result.score} > {max_score}). Tự động điều chỉnh về {max_score}.")
                    result.score = max_score
                elif result.score < 0:
                    result.score = 0.0
                    
                logger.info(f"Đã chấm xong. Điểm: {result.score}/{max_score}")
                return result

            except Exception as e:
                if isinstance(e, ValidationError):
                    attempt += 1
                    logger.warning(f"Lần {attempt}: AI trả về sai format Pydantic khi chấm bài. Đang thử lại... Chi tiết lỗi: {e}")
                    if attempt >= self.max_retries:
                        logger.error("Đã hết số lần thử lại. Trả về điểm mặc định cần review.")
                        # Trong production, ta trả về 0 hoặc null kèm flag để giáo viên vào chấm tay
                        return GradingResult(
                            explanation="Hệ thống AI không thể chuẩn hóa kết quả chấm. Cần giáo viên chấm thủ công.",
                            score=0.0
                        )
                else:
                    logger.error(f"Lỗi API khi chấm bài: {str(e)}")
                    raise FileParsingError("Lỗi giao tiếp với máy chủ AI trong quá trình chấm tự luận.")

# Khởi tạo Singleton
ai_grader = AIGradingService()