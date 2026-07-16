import json
import logging
from typing import List, Optional
import google.generativeai as genai
from google.generativeai.types import generation_types
from pydantic import ValidationError

# Import từ các module khác trong kiến trúc hệ thống
from app.config import settings
from app.schemas.ai_processing import ClassificationResult
from app.schemas.question import QuestionSchema
from app.prompts.classify_prompt import CLASSIFY_SYSTEM_PROMPT
from app.prompts.extract_prompt import EXTRACT_SYSTEM_PROMPT
from app.services.schema_validator import safe_json_parse
from app.core.exceptions import FileParsingError

logger = logging.getLogger(__name__)

class AIParserService:
    """
    Service chịu trách nhiệm giao tiếp với LLM (Gemini) để bóc tách 
    và cấu trúc hóa dữ liệu văn bản thô từ đề thi.
    """
    
    def __init__(self):
        # Khởi tạo client Gemini. Tham số api_key lấy từ môi trường.
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Sử dụng flash-lite cho cả việc phân loại và bóc tách
        self.classifier_model = settings.DEFAULT_GRADING_MODEL
        self.extractor_model = settings.DEFAULT_EXTRACTION_MODEL
        self.max_retries = 3

    def classify_document(self, raw_text: str) -> ClassificationResult:
        """
        Phân tích đoạn text đầu tiên (khoảng 2000 ký tự) để xác định môn học,
        loại đề thi và thời gian làm bài dự kiến.
        """
        # Cắt bớt text để tiết kiệm token, chỉ cần phần đầu của đề thi là đủ để phân loại
        preview_text = raw_text[:2000] 
        
        try:
            model = genai.GenerativeModel(
                model_name=self.classifier_model,
                system_instruction=CLASSIFY_SYSTEM_PROMPT
            )
            
            response = model.generate_content(
                f"Hãy phân tích đề thi sau và trả về đúng chuẩn JSON được yêu cầu:\n\n{preview_text}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=500,
                    response_mime_type="application/json"
                )
            )
            
            raw_json = response.text
            # safe_json_parse là hàm helper bạn viết ở schema_validator.py để parse và validate với Pydantic
            result = safe_json_parse(raw_json, ClassificationResult)
            
            logger.info(f"Phân loại thành công: Môn {result.subject}, Thời gian {result.duration} phút.")
            return result

        except Exception as e:
            if isinstance(e, ValidationError):
                logger.error(f"Gemini trả về sai format Pydantic (ClassificationResult): {str(e)}")
                raise FileParsingError("Không thể nhận diện cấu trúc đề thi này.")
            else:
                logger.error(f"Lỗi kết nối Gemini API khi phân loại tài liệu: {str(e)}")
                raise FileParsingError("Hệ thống AI hiện đang bận, vui lòng thử lại sau.")

    def extract_questions(self, raw_text: str) -> List[QuestionSchema]:
        """
        Quét toàn bộ text của tài liệu và bóc tách thành danh sách các câu hỏi 
        chuẩn JSON (Trắc nghiệm, Tự luận, v.v.)
        """
        attempt = 0
        while attempt < self.max_retries:
            try:
                model = genai.GenerativeModel(
                    model_name=self.extractor_model,
                    system_instruction=EXTRACT_SYSTEM_PROMPT
                )
                
                response = model.generate_content(
                    f"Dưới đây là văn bản thô của một đề thi. Hãy bóc tách và trả về MỘT MẢNG JSON duy nhất chứa các câu hỏi:\n\n<document>\n{raw_text}\n</document>",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=8192,
                        response_mime_type="application/json"
                    )
                )
                
                raw_json = response.text
                
                # Gọi hàm helper để validate list các câu hỏi
                questions = safe_json_parse(raw_json, List[QuestionSchema])
                
                logger.info(f"Bóc tách thành công {len(questions)} câu hỏi.")
                return questions

            except ValidationError as e:
                attempt += 1
                logger.warning(f"Lần {attempt}: AI trả về sai format JSON câu hỏi. Đang thử lại... Chi tiết lỗi: {e}")
                if attempt >= self.max_retries:
                    logger.error("Đã hết số lần thử lại (retries) do sai format Schema.")
                    raise FileParsingError("Không thể chuẩn hóa dữ liệu câu hỏi từ file tải lên.")
            except Exception as e:
                logger.error(f"Lỗi API Google Generative AI khi bóc tách câu hỏi: {str(e)}")
                raise FileParsingError("Lỗi giao tiếp với máy chủ AI.")

# Khởi tạo instance duy nhất (Singleton pattern) để import vào Celery Tasks
ai_parser = AIParserService()