import json
import logging
from typing import List, Optional
from openai import OpenAI
from pydantic import ValidationError

# Import từ các module khác trong kiến trúc hệ thống
from app.config import settings
from app.schemas.ai_processing import ClassificationResult
from app.prompts.classify_prompt import CLASSIFY_SYSTEM_PROMPT, get_classification_prompt
from app.prompts.extract_prompt import EXTRACT_SYSTEM_PROMPT, get_extraction_prompt
from app.schemas.question import QuestionSchema, ExamExtractionSchema
from app.services.schema_validator import safe_json_parse
from app.core.exceptions import FileParsingError

logger = logging.getLogger(__name__)

class AIParserService:
    """
    Service chịu trách nhiệm giao tiếp với LLM (Gemini/OpenAI) để bóc tách 
    và cấu trúc hóa dữ liệu văn bản thô từ đề thi.
    """
    
    def __init__(self):
        # Khởi tạo client OpenAI-compatible.
        self.client = OpenAI(api_key=settings.GEMINI_API_KEY, base_url=settings.GEMINI_BASE_URL)
        self.classifier_model = settings.DEFAULT_GRADING_MODEL
        self.extractor_model = settings.DEFAULT_EXTRACTION_MODEL
        self.max_retries = 3

    def classify_document(self, raw_text: str) -> ClassificationResult:
        """
        Phân tích đoạn text đầu tiên để xác định môn học, loại đề thi và thời gian làm bài dự kiến.
        """
        # Cắt lấy 1000 ký tự đầu tiên để tiết kiệm token
        preview_text = raw_text[:1000] 
        
        try:
            response = self.client.chat.completions.create(
                model=self.classifier_model,
                messages=[
                    {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                    {"role": "user", "content": get_classification_prompt(preview_text)}
                ],
                temperature=0.0,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            raw_json = response.choices[0].message.content
            result = safe_json_parse(raw_json, ClassificationResult)
            
            logger.info(f"Phân loại thành công: Môn {result.subject}, Thời gian {result.duration} phút.")
            return result

        except Exception as e:
            if isinstance(e, ValidationError):
                logger.error(f"AI trả về sai format Pydantic (ClassificationResult): {str(e)}")
                raise FileParsingError("Không thể nhận diện cấu trúc đề thi này.")
            else:
                logger.error(f"Lỗi kết nối API khi phân loại tài liệu: {str(e)}")
                raise FileParsingError("Hệ thống AI hiện đang bận, vui lòng thử lại sau.")


    def extract_batched_blocks(self, batched_text: str, visual_assets_context: str = "", subject: str = "") -> ExamExtractionSchema:
        """
        Tầng 3: Nhận vào chuỗi chứa nhiều blocks đã được thêm delimiter và yêu cầu AI bóc tách.
        """
        attempt = 0
        
        content_with_assets = batched_text
        if visual_assets_context:
            content_with_assets = f"THÔNG TIN HÌNH ẢNH:\n{visual_assets_context}\n\n{batched_text}"
        
        if subject and subject.upper() == "IELTS":
            from app.prompts.ielts_extract_prompt import IELTS_EXTRACT_SYSTEM_PROMPT, get_ielts_extraction_prompt
            sys_prompt = IELTS_EXTRACT_SYSTEM_PROMPT
            user_prompt = get_ielts_extraction_prompt(content_with_assets)
        else:
            sys_prompt = EXTRACT_SYSTEM_PROMPT
            user_prompt = get_extraction_prompt(content_with_assets)
            
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ]

        while attempt < self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.extractor_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=8192, # Đã tăng lên vì batch
                    response_format={"type": "json_object"}
                )
                
                raw_json = response.choices[0].message.content
                parsed_exam = safe_json_parse(raw_json, ExamExtractionSchema)
                
                logger.debug(f"Bóc tách thành công batched blocks (sau {attempt + 1} lần gọi).")
                return parsed_exam

            except ValidationError as e:
                attempt += 1
                logger.warning(f"Lần {attempt} (Batched Blocks): Sai format JSON. Lỗi:\n{e}")
                
                if attempt >= self.max_retries:
                    logger.error(f"Đã hết số lần thử lại cho Batched Blocks.")
                    return ExamExtractionSchema(questions=[])
                
                messages.append({"role": "assistant", "content": raw_json if raw_json else "{}"})
                error_feedback = (
                    f"Kết quả JSON vừa rồi bị lỗi Schema ValidationError:\n{str(e)}\n"
                    f"Hãy sửa lại JSON. CHỈ TRẢ VỀ JSON."
                )
                messages.append({"role": "user", "content": error_feedback})

            except Exception as e:
                logger.error(f"Lỗi API khi bóc tách batched blocks: {str(e)}", exc_info=True)
                return ExamExtractionSchema(questions=[])

    def extract_ielts_full_document(self, document_text: str) -> 'IELTSExamSchema':
        """
        Gửi toàn bộ Raw Text của PDF lên LLM để bóc tách toàn bộ cấu trúc 3 Passages và các Blocks (Range) câu hỏi.
        """
        from app.prompts.ielts_extract_prompt import IELTS_FULL_SYSTEM_PROMPT, get_ielts_full_prompt
        from app.schemas.question import IELTSExamSchema
        
        attempt = 0
        messages = [
            {"role": "system", "content": IELTS_FULL_SYSTEM_PROMPT},
            {"role": "user", "content": get_ielts_full_prompt(document_text)}
        ]

        while attempt < self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.extractor_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=8192, 
                    response_format={"type": "json_object"}
                )
                
                raw_json = response.choices[0].message.content
                parsed_exam = safe_json_parse(raw_json, IELTSExamSchema)
                
                logger.debug(f"Bóc tách thành công IELTS Full Document (sau {attempt + 1} lần gọi).")
                return parsed_exam

            except ValidationError as e:
                attempt += 1
                logger.warning(f"Lần {attempt} (IELTS Full): Sai format JSON. Lỗi:\n{e}")
                
                if attempt >= self.max_retries:
                    logger.error(f"Đã hết số lần thử lại cho IELTS Full Document.")
                    raise FileParsingError("Không thể bóc tách cấu trúc IELTS theo chuẩn.")
                
                messages.append({"role": "assistant", "content": raw_json if raw_json else "{}"})
                error_feedback = (
                    f"Kết quả JSON vừa rồi bị lỗi Schema ValidationError:\n{str(e)}\n"
                    f"Hãy sửa lại JSON. Nhớ ĐẢM BẢO đúng 3 passages, 40 câu hỏi, và đúng định dạng schema."
                )
                messages.append({"role": "user", "content": error_feedback})

            except Exception as e:
                logger.error(f"Lỗi API khi bóc tách IELTS Full Document: {str(e)}", exc_info=True)
                raise FileParsingError(f"Hệ thống AI lỗi: {str(e)}")

# Khởi tạo instance duy nhất (Singleton pattern) để import vào Celery Tasks
ai_parser = AIParserService()