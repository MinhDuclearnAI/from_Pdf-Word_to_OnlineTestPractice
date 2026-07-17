# import json
# import logging
# from typing import List, Optional
# from openai import OpenAI
# from pydantic import ValidationError

# # Import từ các module khác trong kiến trúc hệ thống
# from app.config import settings
# from app.schemas.ai_processing import ClassificationResult
# from app.prompts.classify_prompt import CLASSIFY_SYSTEM_PROMPT, get_classification_prompt
# from app.prompts.extract_prompt import EXTRACT_SYSTEM_PROMPT, get_extraction_prompt
# from app.schemas.question import QuestionSchema, ExamExtractionSchema
# from app.services.schema_validator import safe_json_parse
# from app.core.exceptions import FileParsingError

# logger = logging.getLogger(__name__)

# class AIParserService:
#     """
#     Service chịu trách nhiệm giao tiếp với LLM (Gemini) để bóc tách 
#     và cấu trúc hóa dữ liệu văn bản thô từ đề thi.
#     """
    
#     def __init__(self):
#         # Khởi tạo client OpenAI-compatible.
#         self.client = OpenAI(api_key=settings.GEMINI_API_KEY, base_url=settings.GEMINI_BASE_URL)
#         # Sử dụng flash-lite cho cả việc phân loại và bóc tách
#         self.classifier_model = settings.DEFAULT_GRADING_MODEL
#         self.extractor_model = settings.DEFAULT_EXTRACTION_MODEL
#         self.max_retries = 3

#     def classify_document(self, raw_text: str) -> ClassificationResult:
#         """
#         Phân tích đoạn text đầu tiên (khoảng 2000 ký tự) để xác định môn học,
#         loại đề thi và thời gian làm bài dự kiến.
#         """
#         # Cắt bớt text để tiết kiệm token, chỉ cần phần đầu của đề thi là đủ để phân loại
#         preview_text = raw_text[:2000] 
        
#         try:
#             response = self.client.chat.completions.create(
#                 model=self.classifier_model,
#                 messages=[
#                     {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
#                     {"role": "user", "content": get_classification_prompt(preview_text)}
#                 ],
#                 temperature=0.0,
#                 max_tokens=500,
#                 response_format={"type": "json_object"}
#             )
            
#             raw_json = response.choices[0].message.content
#             # safe_json_parse là hàm helper bạn viết ở schema_validator.py để parse và validate với Pydantic
#             result = safe_json_parse(raw_json, ClassificationResult)
            
#             logger.info(f"Phân loại thành công: Môn {result.subject}, Thời gian {result.duration} phút.")
#             return result

#         except Exception as e:
#             if isinstance(e, ValidationError):
#                 logger.error(f"Gemini trả về sai format Pydantic (ClassificationResult): {str(e)}")
#                 raise FileParsingError("Không thể nhận diện cấu trúc đề thi này.")
#             else:
#                 logger.error(f"Lỗi kết nối Gemini API khi phân loại tài liệu: {str(e)}")
#                 raise FileParsingError("Hệ thống AI hiện đang bận, vui lòng thử lại sau.")

#     def extract_questions(self, raw_text: str) -> ExamExtractionSchema:
#         """
#         Quét toàn bộ text của tài liệu và bóc tách thành danh sách các câu hỏi 
#         chuẩn JSON (Trắc nghiệm, Tự luận, v.v.)
#         """
#         attempt = 0
#         while attempt < self.max_retries:
#             try:
#                 response = self.client.chat.completions.create(
#                     model=self.extractor_model,
#                     messages=[
#                         {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
#                         {"role": "user", "content": get_extraction_prompt(raw_text)}
#                     ],
#                     temperature=0.1,
#                     max_tokens=8192
#                 )
                
#                 raw_json = response.choices[0].message.content
                
#                 # Gọi hàm helper để validate list các câu hỏi
#                 parsed_exam = safe_json_parse(raw_json, ExamExtractionSchema)
                
#                 logger.info(f"Bóc tách thành công {len(parsed_exam.questions)} câu hỏi.")
#                 return parsed_exam

#             except ValidationError as e:
#                 attempt += 1
#                 logger.warning(f"Lần {attempt}: AI trả về sai format JSON câu hỏi. Đang thử lại... Chi tiết lỗi: {e}")
#                 if attempt >= self.max_retries:
#                     logger.error("Đã hết số lần thử lại (retries) do sai format Schema.")
#                     raise FileParsingError("Không thể chuẩn hóa dữ liệu câu hỏi từ file tải lên.")
#             except Exception as e:
#                 logger.error(f"Lỗi API khi bóc tách câu hỏi: {str(e)}")
#                 raise FileParsingError("Lỗi giao tiếp với máy chủ AI.")

# # Khởi tạo instance duy nhất (Singleton pattern) để import vào Celery Tasks
# ai_parser = AIParserService()

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
        # Cắt lấy 2000 ký tự đầu tiên để tiết kiệm token
        preview_text = raw_text[:2000] 
        
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

    def extract_questions(self, raw_text: str) -> ExamExtractionSchema:
        """
        Quét toàn bộ text của tài liệu và bóc tách thành danh sách các câu hỏi chuẩn JSON.
        Áp dụng cơ chế Smart Retry: Feed lỗi Pydantic ngược lại LLM để tự sửa sai.
        """
        attempt = 0
        
        # Khởi tạo ngữ cảnh hội thoại linh hoạt cho phép đẩy thêm log lỗi vào sau này
        messages = [
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            {"role": "user", "content": get_extraction_prompt(raw_text)}
        ]

        while attempt < self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=self.extractor_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=8192,
                    response_format={"type": "json_object"}  # Đã BỔ SUNG ép kiểu JSON
                )
                
                raw_json = response.choices[0].message.content
                
                # Gọi hàm helper để validate list các câu hỏi
                parsed_exam = safe_json_parse(raw_json, ExamExtractionSchema)
                
                logger.info(f"Bóc tách thành công {len(parsed_exam.questions)} câu hỏi (sau {attempt + 1} lần gọi).")
                return parsed_exam

            except ValidationError as e:
                attempt += 1
                logger.warning(f"Lần {attempt}: Sai format JSON. Lỗi chi tiết:\n{e}")
                
                if attempt >= self.max_retries:
                    logger.error("Đã hết số lần thử lại (retries) do sai format Schema liên tục.")
                    raise FileParsingError("Không thể chuẩn hóa dữ liệu câu hỏi từ file tải lên.")
                
                # --- [FIX]: SMART RETRY LOGIC ---
                # Nạp JSON bị lỗi vào context đóng vai trò là "câu trả lời cũ của AI"
                messages.append({"role": "assistant", "content": raw_json if raw_json else "{}"})
                
                # Cung cấp log lỗi từ Pydantic và ép LLM sửa lại
                error_feedback = (
                    f"Kết quả JSON vừa rồi của bạn bị lỗi cấu trúc (Schema ValidationError):\n{str(e)}\n"
                    f"Dựa vào thông báo lỗi trên, hãy sửa lại JSON cho chuẩn xác. "
                    f"CHỈ TRẢ VỀ JSON, KHÔNG KÈM THEO BẤT KỲ VĂN BẢN GIẢI THÍCH NÀO KHÁC."
                )
                messages.append({"role": "user", "content": error_feedback})
                # ---------------------------------

            except Exception as e:
                logger.error(f"Lỗi API khi bóc tách câu hỏi: {str(e)}", exc_info=True)
                raise FileParsingError("Lỗi giao tiếp với máy chủ AI.")

# Khởi tạo instance duy nhất (Singleton pattern) để import vào Celery Tasks
ai_parser = AIParserService()