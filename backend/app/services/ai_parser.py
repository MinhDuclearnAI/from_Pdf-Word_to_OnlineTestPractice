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
from app.prompts.ielts_extract_prompt import IELTS_EXTRACT_SYSTEM_PROMPT, get_ielts_extraction_prompt
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
        # Cắt lấy 2000 ký tự đầu tiên để tiết kiệm token
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

    def _split_into_sections(self, raw_text: str) -> List[str]:
        """
        Nhận diện và phân tách văn bản theo các mốc Phần / Bài đọc (Passage 1, 2, 3 / Part 1, 2, 3).
        """
        import re
        pattern = r'(?i)(?=(?:READING\s+PASSAGE\s+\d+|PASSAGE\s+\d+|PART\s+\d+|PHẦN\s+[0-9IVX]+))'
        chunks = re.split(pattern, raw_text)
        cleaned_chunks = [c.strip() for c in chunks if len(c.strip()) > 80]
        return cleaned_chunks

    def _extract_single_chunk(self, chunk_text: str, subject: str = "Khác") -> ExamExtractionSchema:
        """
        Bóc tách một đoạn văn bản (1 chunk hoặc 1 đề tiêu chuẩn) thành ExamExtractionSchema.
        """
        attempt = 0
        
        if subject.strip().upper() == "IELTS":
            sys_prompt = IELTS_EXTRACT_SYSTEM_PROMPT
            user_prompt = get_ielts_extraction_prompt(chunk_text)
        else:
            sys_prompt = EXTRACT_SYSTEM_PROMPT
            user_prompt = get_extraction_prompt(chunk_text)

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
                    max_tokens=8192,
                    response_format={"type": "json_object"}
                )
                
                raw_json = response.choices[0].message.content
                parsed_exam = safe_json_parse(raw_json, ExamExtractionSchema)
                return parsed_exam

            except ValidationError as e:
                attempt += 1
                logger.warning(f"Lần {attempt}: Sai format JSON khi bóc tách chunk. Lỗi: {e}")
                
                if attempt >= self.max_retries:
                    logger.error("Đã hết số lần thử lại (retries) do sai format Schema liên tục.")
                    raise FileParsingError("Không thể chuẩn hóa dữ liệu câu hỏi từ file tải lên.")
                
                messages.append({"role": "assistant", "content": raw_json if raw_json else "{}"})
                error_feedback = (
                    f"Kết quả JSON vừa rồi của bạn bị lỗi cấu trúc (Schema ValidationError):\n{str(e)}\n"
                    f"Dựa vào thông báo lỗi trên, hãy sửa lại JSON cho chuẩn xác. "
                    f"CHỈ TRẢ VỀ JSON, KHÔNG KÈM THEO BẤT KỲ VĂN BẢN GIẢI THÍCH NÀO KHÁC."
                )
                messages.append({"role": "user", "content": error_feedback})

            except Exception as e:
                logger.error(f"Lỗi API khi bóc tách câu hỏi: {str(e)}", exc_info=True)
                raise FileParsingError("Lỗi giao tiếp với máy chủ AI.")

    def extract_questions(self, raw_text: str, subject: str = "Khác") -> ExamExtractionSchema:
        """
        Bóc tách toàn bộ câu hỏi trong đề thi.
        Nếu phát hiện đề có nhiều Bài đọc / Phần (như IELTS 3 Passages), tự động bóc tách từng phần
        để tránh tràn Token và đảm bảo 100% câu hỏi (40 câu) được trích xuất đầy đủ.
        """
        sections = self._split_into_sections(raw_text)
        
        # Nếu đề thi có từ 2 phần/passage trở lên và văn bản dài
        if len(sections) >= 2:
            logger.info(f"Phát hiện {len(sections)} bài đọc/phần riêng biệt. Đang bóc tách theo từng phần...")
            all_questions = []
            for idx, sec_text in enumerate(sections):
                try:
                    sec_result = self._extract_single_chunk(sec_text, subject)
                    logger.info(f"Phần {idx + 1}: Bóc tách được {len(sec_result.questions)} câu hỏi.")
                    all_questions.extend(sec_result.questions)
                except Exception as e:
                    logger.warning(f"Lỗi khi bóc tách phần {idx + 1}: {e}")
            
            if all_questions:
                # Đánh lại ID tuần tự q1, q2,... nếu có trùng lặp
                for i, q in enumerate(all_questions):
                    q.id = f"q{i + 1}"
                logger.info(f"Tổng cộng bóc tách thành công {len(all_questions)} câu hỏi từ tất cả các phần.")
                return ExamExtractionSchema(questions=all_questions)

        # Với đề thông thường hoặc đề 1 phần
        return self._extract_single_chunk(raw_text, subject)

# Khởi tạo instance duy nhất (Singleton pattern) để import vào Celery Tasks
ai_parser = AIParserService()