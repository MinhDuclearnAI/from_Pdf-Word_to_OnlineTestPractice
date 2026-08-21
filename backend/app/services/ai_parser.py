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
        self.max_retries = 2

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
            
            if getattr(response, "choices", None) is None or len(response.choices) == 0:
                logger.error(f"API Error - Invalid choices received. Full response: {response}")
                raise Exception("Hệ thống AI không trả về kết quả hợp lệ (có thể do lỗi kết nối hoặc bộ lọc an toàn). Vui lòng thử lại.")
                
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
            raw_json = None
            try:
                response = self.client.chat.completions.create(
                    model=self.extractor_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=8192, # Đã tăng lên vì batch
                    response_format={"type": "json_object"}
                )
                
                if getattr(response, "choices", None) is None or len(response.choices) == 0:
                    logger.error(f"API Error - Invalid choices received in extraction. Full response: {response}")
                    raise ValueError("Lỗi proxy API trả về empty choices.")
                    
                raw_json = response.choices[0].message.content
                
                # --- DEBUG: Lưu raw json ra file để kiểm tra ---
                try:
                    import os, time
                    debug_dir = os.path.join(os.getcwd(), "debug_logs")
                    os.makedirs(debug_dir, exist_ok=True)
                    timestamp = int(time.time())
                    debug_file = os.path.join(debug_dir, f"llm_output_batch_{timestamp}_attempt_{attempt}.json")
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(raw_json)
                except Exception as debug_err:
                    logger.warning(f"Lỗi khi lưu debug raw json: {debug_err}")
                # -----------------------------------------------
                
                parsed_exam = safe_json_parse(raw_json, ExamExtractionSchema)
                
                logger.debug(f"Bóc tách thành công Batch (sau {attempt + 1} lần gọi).")
                return parsed_exam

            except (ValidationError, ValueError) as e:
                attempt += 1
                logger.warning(f"Lần {attempt} (Extraction): Lỗi AI/JSON. Lỗi:\n{e}")
                
                if attempt >= self.max_retries:
                    logger.error("Đã hết số lần thử lại cho Extraction.")
                    raise FileParsingError("Hệ thống AI không trả về kết quả hợp lệ (có thể do lỗi kết nối hoặc bộ lọc an toàn). Vui lòng thử lại.")
                
                messages.append({"role": "assistant", "content": raw_json if raw_json else "{}"})
                error_feedback = (
                    f"Kết quả JSON vừa rồi bị lỗi Schema ValidationError:\n{str(e)}\n"
                    f"Hãy sửa lại JSON. CHỈ TRẢ VỀ JSON."
                )
                messages.append({"role": "user", "content": error_feedback})

            except Exception as e:
                logger.error(f"Lỗi API khi bóc tách batched blocks: {str(e)}", exc_info=True)
                return ExamExtractionSchema(questions=[])

    def split_ielts_document(self, document_text: str) -> Optional[dict]:
        """
        Dùng Regex nhận diện các mỏ neo 'Questions X-Y' để tự động cắt văn bản 
        thành 3 phần Passage (lưu nguyên văn 100%) và 3 phần Questions (gửi cho LLM).
        """
        import re
        pattern = r'(?i)\bQuestions?\s+(\d+)\s*[-–to\s]+\s*(\d+)'
        matches = list(re.finditer(pattern, document_text))
        
        if not matches or len(matches) < 3:
            return None
            
        p1_matches = [m for m in matches if int(m.group(1)) <= 13]
        p2_matches = [m for m in matches if 14 <= int(m.group(1)) <= 26]
        p3_matches = [m for m in matches if int(m.group(1)) >= 27]
        
        if not p1_matches or not p2_matches or not p3_matches:
            return None
            
        # Helper: Chuẩn hóa mượt mà các đoạn văn (Xóa ngắt dòng cứng của PDF bên trong đoạn)
        def _clean_passage_paragraphs(raw_text: str) -> str:
            if not raw_text or not raw_text.strip():
                return ""
            paragraphs = re.split(r'\n\s*\n', raw_text)
            cleaned = []
            for p in paragraphs:
                # Nối các dòng bị ngắt cứng bởi lề PDF thành 1 dòng mượt mà
                clean_p = " ".join(p.split())
                if clean_p:
                    cleaned.append(clean_p)
            return "\n\n".join(cleaned)

        # --- 1. Tách Passage 1 (Nguyên văn) ---
        p1_slice = document_text[:p1_matches[0].start()].strip()
        p1_clean_head = re.sub(r'^(IELTS|READING|TEST|ACADEMIC|GENERAL|PRACTICE).*\n', '', p1_slice, flags=re.I).strip()
        p1_lines = [l.strip() for l in p1_clean_head.split('\n') if l.strip()]
        p1_title = p1_lines[0] if len(p1_lines) > 0 and len(p1_lines[0]) < 80 else 'Reading Passage 1'
        p1_raw_body = p1_clean_head[len(p1_title):].strip() if p1_clean_head.startswith(p1_title) else p1_clean_head
        p1_content = _clean_passage_paragraphs(p1_raw_body)
        
        # --- 2. Tách Questions 1 và Passage 2 (Nguyên văn) ---
        inter_1_2 = document_text[p1_matches[-1].start():p2_matches[0].start()]
        paras_1_2 = [p.strip() for p in re.split(r'\n\s*\n', inter_1_2) if p.strip()]
        p2_paras = []
        found_p2 = False
        for p in paras_1_2:
            is_q = bool(re.match(r'^(Questions?\s+\d+|\d+[\.\)]|[A-E][\.\s]|Choose|Complete|Write|TRUE|FALSE|NOT GIVEN|YES|NO)', p, re.I))
            if not is_q and (len(p) > 100 or found_p2 or (len(p) > 5 and not p.endswith(('.', ':', '?')))):
                found_p2 = True
            if found_p2:
                p2_paras.append(p)
                
        p2_start_idx = inter_1_2.find(p2_paras[0]) if p2_paras else len(inter_1_2)
        p1_q_text = document_text[p1_matches[0].start():p1_matches[-1].start()] + '\n\n' + inter_1_2[:p2_start_idx].strip()
        
        p2_slice = inter_1_2[p2_start_idx:].strip()
        p2_lines = [l.strip() for l in p2_slice.split('\n') if l.strip()]
        p2_title = p2_lines[0] if len(p2_lines) > 0 and len(p2_lines[0]) < 80 else 'Reading Passage 2'
        p2_raw_body = p2_slice[len(p2_title):].strip() if p2_slice.startswith(p2_title) else p2_slice
        p2_content = _clean_passage_paragraphs(p2_raw_body)

        # --- 3. Tách Questions 2 và Passage 3 (Nguyên văn) ---
        inter_2_3 = document_text[p2_matches[-1].start():p3_matches[0].start()]
        paras_2_3 = [p.strip() for p in re.split(r'\n\s*\n', inter_2_3) if p.strip()]
        p3_paras = []
        found_p3 = False
        for p in paras_2_3:
            is_q = bool(re.match(r'^(Questions?\s+\d+|\d+[\.\)]|[A-E][\.\s]|Choose|Complete|Write|TRUE|FALSE|NOT GIVEN|YES|NO)', p, re.I))
            if not is_q and (len(p) > 100 or found_p3 or (len(p) > 5 and not p.endswith(('.', ':', '?')))):
                found_p3 = True
            if found_p3:
                p3_paras.append(p)
                
        p3_start_idx = inter_2_3.find(p3_paras[0]) if p3_paras else len(inter_2_3)
        p2_q_text = document_text[p2_matches[0].start():p2_matches[-1].start()] + '\n\n' + inter_2_3[:p3_start_idx].strip()

        p3_slice = inter_2_3[p3_start_idx:].strip()
        p3_lines = [l.strip() for l in p3_slice.split('\n') if l.strip()]
        p3_title = p3_lines[0] if len(p3_lines) > 0 and len(p3_lines[0]) < 80 else 'Reading Passage 3'
        p3_raw_body = p3_slice[len(p3_title):].strip() if p3_slice.startswith(p3_title) else p3_slice
        p3_content = _clean_passage_paragraphs(p3_raw_body)
        
        # --- 4. Tách Questions 3 ---
        p3_q_text = document_text[p3_matches[0].start():].strip()
        task2_match = re.search(r'(?i)\n\s*(Task\s+2|Writing\s+Task)', p3_q_text)
        if task2_match:
            p3_q_text = p3_q_text[:task2_match.start()].strip()
            
        return {
            'p1': {'title': p1_title, 'content': p1_content, 'questions_text': p1_q_text.strip()},
            'p2': {'title': p2_title, 'content': p2_content, 'questions_text': p2_q_text.strip()},
            'p3': {'title': p3_title, 'content': p3_content, 'questions_text': p3_q_text.strip()},
        }

    def extract_ielts_full_document(self, document_text: str) -> 'IELTSExamSchema':
        """
        Tách trước 3 bài đọc (Passages) bằng Regex để giải phóng LLM, chỉ gửi câu hỏi
        cho LLM bóc tách JSON, sau đó tự động ghép nối lại Passage chính xác 100%.
        """
        from app.prompts.ielts_extract_prompt import IELTS_FULL_SYSTEM_PROMPT, get_ielts_full_prompt
        from app.schemas.question import IELTSExamSchema
        
        split_info = self.split_ielts_document(document_text)
        
        if split_info:
            logger.info("Đã tách thành công 3 Passages bằng Regex. Chỉ gửi Questions cho AI.")
            prompt_input_text = f"""[PASSAGE 1 QUESTIONS (Questions 1-13)]\n{split_info['p1']['questions_text']}\n\n[PASSAGE 2 QUESTIONS (Questions 14-26)]\n{split_info['p2']['questions_text']}\n\n[PASSAGE 3 QUESTIONS (Questions 27-40)]\n{split_info['p3']['questions_text']}"""
        else:
            logger.warning("Không thể tự động phân đoạn IELTS bằng Regex. Gửi toàn bộ văn bản cho AI.")
            prompt_input_text = document_text
            
        attempt = 0
        messages = [
            {"role": "system", "content": IELTS_FULL_SYSTEM_PROMPT},
            {"role": "user", "content": get_ielts_full_prompt(prompt_input_text)}
        ]

        while attempt < self.max_retries:
            raw_json = None
            try:
                response = self.client.chat.completions.create(
                    model=self.extractor_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=8192, 
                    response_format={"type": "json_object"}
                )
                
                if getattr(response, "choices", None) is None or len(response.choices) == 0:
                    logger.error(f"API Error - Invalid choices received. Full response: {response}")
                    raise ValueError("Lỗi proxy API trả về empty choices (Có thể do bộ lọc an toàn hoặc lag).")
                    
                raw_json = response.choices[0].message.content
                
                # --- DEBUG: Lưu raw json ra file để kiểm tra ---
                try:
                    import os, time
                    debug_dir = os.path.join(os.getcwd(), "debug_logs")
                    os.makedirs(debug_dir, exist_ok=True)
                    timestamp = int(time.time())
                    debug_file = os.path.join(debug_dir, f"llm_output_ielts_{timestamp}_attempt_{attempt}.json")
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(raw_json)
                except Exception as debug_err:
                    logger.warning(f"Lỗi khi lưu debug raw json: {debug_err}")
                # -----------------------------------------------
                
                parsed_exam = safe_json_parse(raw_json, IELTSExamSchema)
                
                # NẾU ĐÃ TÁCH PASSAGE TỪ TRƯỚC: Tự động gán lại Passage và Title chuẩn 100%
                if split_info and parsed_exam.passages:
                    if len(parsed_exam.passages) >= 1:
                        parsed_exam.passages[0].title = split_info['p1']['title']
                        parsed_exam.passages[0].content = split_info['p1']['content']
                    if len(parsed_exam.passages) >= 2:
                        parsed_exam.passages[1].title = split_info['p2']['title']
                        parsed_exam.passages[1].content = split_info['p2']['content']
                    if len(parsed_exam.passages) >= 3:
                        parsed_exam.passages[2].title = split_info['p3']['title']
                        parsed_exam.passages[2].content = split_info['p3']['content']
                        
                logger.debug(f"Bóc tách thành công IELTS Document (sau {attempt + 1} lần gọi).")
                return parsed_exam

            except (ValidationError, ValueError) as e:
                attempt += 1
                logger.warning(f"Lần {attempt} (IELTS Full): Lỗi AI/JSON. Chi tiết:\n{e}")
                
                if attempt >= self.max_retries:
                    logger.error(f"Đã hết số lần thử lại cho IELTS Full Document.")
                    raise FileParsingError("Hệ thống AI không trả về kết quả hợp lệ (có thể do lỗi kết nối hoặc bộ lọc an toàn). Vui lòng thử lại.")
                
                messages.append({"role": "assistant", "content": raw_json if raw_json else "{}"})
                error_feedback = (
                    f"Kết quả JSON vừa rồi bị lỗi Schema ValidationError:\n{str(e)}\n"
                    f"Hãy sửa lại JSON. Nhớ ĐẢM BẢO đúng các blocks, questions, và đúng định dạng schema."
                )
                messages.append({"role": "user", "content": error_feedback})

            except Exception as e:
                logger.error(f"Lỗi API khi bóc tách IELTS Full Document: {str(e)}", exc_info=True)
                raise FileParsingError(f"Hệ thống AI lỗi: {str(e)}")

# Khởi tạo instance duy nhất (Singleton pattern) để import vào Celery Tasks
ai_parser = AIParserService()