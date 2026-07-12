import json
import logging
from typing import List, Optional
from anthropic import Anthropic, APIError, APITimeoutError
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
    Service chịu trách nhiệm giao tiếp với LLM (Claude) để bóc tách 
    và cấu trúc hóa dữ liệu văn bản thô từ đề thi.
    """
    
    def __init__(self):
        # Khởi tạo client Anthropic. Tham số api_key tự động lấy từ môi trường nếu cấu hình chuẩn.
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        # Sử dụng Haiku cho việc phân loại (nhanh, rẻ) và Sonnet cho bóc tách chính xác cao
        self.classifier_model = "claude-3-haiku-20240307"
        self.extractor_model = "claude-3-5-sonnet-20240620"
        self.max_retries = 3

    def classify_document(self, raw_text: str) -> ClassificationResult:
        """
        Phân tích đoạn text đầu tiên (khoảng 2000 ký tự) để xác định môn học,
        loại đề thi và thời gian làm bài dự kiến.
        """
        # Cắt bớt text để tiết kiệm token, chỉ cần phần đầu của đề thi là đủ để phân loại
        preview_text = raw_text[:2000] 
        
        try:
            response = self.client.messages.create(
                model=self.classifier_model,
                max_tokens=500,
                temperature=0.0, # Đặt temperature = 0 để kết quả luôn ổn định
                system=CLASSIFY_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": f"Hãy phân tích đề thi sau và trả về đúng chuẩn JSON được yêu cầu:\n\n{preview_text}"}
                ]
            )
            
            raw_json = response.content[0].text
            # safe_json_parse là hàm helper bạn viết ở schema_validator.py để parse và validate với Pydantic
            result = safe_json_parse(raw_json, ClassificationResult)
            
            logger.info(f"Phân loại thành công: Môn {result.subject}, Thời gian {result.duration} phút.")
            return result

        except (APIError, APITimeoutError) as e:
            logger.error(f"Lỗi kết nối Claude API khi phân loại tài liệu: {str(e)}")
            raise FileParsingError("Hệ thống AI hiện đang bận, vui lòng thử lại sau.")
        except ValidationError as e:
            logger.error(f"Claude trả về sai format Pydantic (ClassificationResult): {str(e)}")
            raise FileParsingError("Không thể nhận diện cấu trúc đề thi này.")

    def extract_questions(self, raw_text: str) -> List[QuestionSchema]:
        """
        Quét toàn bộ text của tài liệu và bóc tách thành danh sách các câu hỏi 
        chuẩn JSON (Trắc nghiệm, Tự luận, v.v.)
        """
        attempt = 0
        while attempt < self.max_retries:
            try:
                response = self.client.messages.create(
                    model=self.extractor_model,
                    max_tokens=4096, # Đặt max token lớn nhất có thể để chứa đủ mảng JSON
                    temperature=0.1, 
                    system=EXTRACT_SYSTEM_PROMPT,
                    messages=[
                        {
                            "role": "user", 
                            "content": f"Dưới đây là văn bản thô của một đề thi. Hãy bóc tách và trả về MỘT MẢNG JSON duy nhất chứa các câu hỏi:\n\n<document>\n{raw_text}\n</document>"
                        },
                        {
                            # Ép Claude bắt đầu bằng dấu ngoặc vuông để ép nó trả về JSON Array thuần túy, không có text chào hỏi.
                            "role": "assistant",
                            "content": "["
                        }
                    ]
                )
                
                # Nối lại dấu ngoặc vuông do ta đã mồi (pre-fill) ở trên
                raw_json = "[" + response.content[0].text
                
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
            except (APIError, APITimeoutError) as e:
                logger.error(f"Lỗi API Anthropic khi bóc tách câu hỏi: {str(e)}")
                raise FileParsingError("Lỗi giao tiếp với máy chủ AI.")
            except Exception as e:
                logger.exception("Lỗi không xác định trong quá trình bóc tách câu hỏi.")
                raise FileParsingError("Đã xảy ra lỗi hệ thống khi phân tích đề thi.")

# Khởi tạo instance duy nhất (Singleton pattern) để import vào Celery Tasks
ai_parser = AIParserService()