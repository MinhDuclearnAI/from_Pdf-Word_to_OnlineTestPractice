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

    def _call_llm(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        use_json_format: bool = True
    ) -> str:
        """
        Gọi LLM an toàn với cơ chế Graceful Fallback (tự động bỏ response_format nếu proxy bị lỗi 400 Bad Request)
        và Retry với Backoff cho các lỗi kết nối/rate limit/empty choices.
        """
        import time
        target_model = model or self.extractor_model
        last_error = None
        
        for retry in range(self.max_retries):
            # Thử lần lượt có response_format (nếu use_json_format=True) rồi fallback sang None nếu proxy trả về lỗi 400
            format_options = [{"type": "json_object"}, None] if use_json_format else [None]
            for format_opt in format_options:
                try:
                    kwargs = {
                        "model": target_model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                    if format_opt is not None:
                        kwargs["response_format"] = format_opt

                    response = self.client.chat.completions.create(**kwargs)
                    
                    if getattr(response, "choices", None) is None or len(response.choices) == 0:
                        err_obj = getattr(response, "error", None)
                        logger.warning(f"Proxy trả về choices rỗng (attempt {retry + 1}): {response}")
                        raise ValueError(f"Lỗi proxy API trả về empty choices: {err_obj or response}")
                        
                    content = response.choices[0].message.content
                    if not content or not content.strip():
                        raise ValueError("LLM trả về nội dung rỗng.")
                        
                    return content

                except Exception as api_err:
                    err_msg = str(api_err)
                    # Nếu lỗi 400 BAD_REQUEST do response_format, lập tức fallback sang format_opt=None không cần đợi
                    if format_opt is not None and ("400" in err_msg or "BAD_REQUEST" in err_msg or "invalid_request_error" in err_msg):
                        logger.warning(f"Proxy báo lỗi 400 với response_format. Tự động fallback sang text prompt thuần: {err_msg}")
                        continue
                    
                    last_error = api_err
                    logger.warning(f"Lỗi gọi API LLM (lần thử {retry + 1}/{self.max_retries}): {err_msg}")
                    break  # Chuyển sang lần retry tiếp theo sau khi sleep
            
            time.sleep(1.5 * (retry + 1))
            
        raise FileParsingError(f"Hệ thống AI lỗi: {str(last_error)}")

    def classify_document(self, raw_text: str) -> ClassificationResult:
        """
        Phân tích đoạn text đầu tiên để xác định môn học, loại đề thi và thời gian làm bài dự kiến.
        """
        # Cắt lấy 1000 ký tự đầu tiên để tiết kiệm token
        preview_text = raw_text[:1000] 
        
        try:
            messages = [
                {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": get_classification_prompt(preview_text)}
            ]
            raw_json = self._call_llm(
                model=self.classifier_model,
                messages=messages,
                temperature=0.0,
                max_tokens=500,
                use_json_format=True
            )
            result = safe_json_parse(raw_json, ClassificationResult)
            logger.info(f"Phân loại thành công: Môn {result.subject}, Thời gian {result.duration} phút.")
            return result

        except Exception as e:
            if isinstance(e, ValidationError):
                logger.error(f"AI trả về sai format Pydantic (ClassificationResult): {str(e)}")
                raise FileParsingError("Không thể nhận diện cấu trúc đề thi này.")
            elif isinstance(e, FileParsingError):
                raise e
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
                raw_json = self._call_llm(
                    model=self.extractor_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=8192,
                    use_json_format=True
                )
                
                # --- DEBUG: Lưu raw json ra file để kiểm tra ---
                try:
                    import os, time
                    from app.services.schema_validator import extract_json_from_markdown
                    debug_dir = os.path.join(os.getcwd(), "debug_logs")
                    os.makedirs(debug_dir, exist_ok=True)
                    timestamp = int(time.time())
                    debug_file = os.path.join(debug_dir, f"llm_output_batch_{timestamp}_attempt_{attempt}.json")
                    clean_json_str = extract_json_from_markdown(raw_json)
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(clean_json_str)
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
                logger.error(f"Lỗi khi bóc tách batched blocks: {str(e)}", exc_info=True)
                return ExamExtractionSchema(questions=[])

    def split_ielts_document(self, document_text: str) -> Optional[dict]:
        """
        Dùng Thuật toán Phân đoạn 2 lớp (Two-tier Partitioning) kết hợp Smart Question Anchor Filter
        để tự động tách 3 phần Passage (lưu nguyên văn 100%, trích xuất Title sạch) và 3 phần Questions (gửi cho LLM).
        Hoạt động hoàn hảo trên cả 2 dạng: File chuẩn Cambridge (có READING PASSAGE 1/2/3) và File không có nhãn.
        """
        import re

        # Helper: Chuẩn hóa mượt mà các đoạn văn (Xóa ngắt dòng cứng của PDF bên trong đoạn)
        def _clean_passage_paragraphs(raw_text: str) -> str:
            if not raw_text or not raw_text.strip():
                return ""
            # Nối các từ bị ngắt gạch nối ở cuối dòng trong PDF (vd: wine-\nmaking -> wine-making)
            raw_text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1-\2', raw_text)
            paragraphs = re.split(r'\n\s*\n+', raw_text)
            cleaned = []
            for p in paragraphs:
                clean_p = " ".join(p.split())
                if clean_p:
                    cleaned.append(clean_p)
            return "\n\n".join(cleaned)

        # Helper: Kiểm tra một chuỗi có thỏa mãn tiêu chuẩn Tiêu Đề Bài Đọc không
        def _is_valid_title(cand: str) -> bool:
            if not cand or len(cand) >= 80:
                return False
            cand = cand.strip()
            
            # Phải bắt đầu bằng chữ hoa (hoặc dấu ngoặc kép + chữ hoa)
            first_char_str = re.sub(r'^[\'\"“‘\s]+', '', cand)
            if not first_char_str or not first_char_str[0].isupper():
                return False
                
            # 1. Không phải là đoạn văn có nhãn A., B., C.
            if re.match(r'^[A-H]\.\s+', cand):
                return False
                
            # 2. Không kết thúc bằng dấu chấm, phẩy, chấm phẩy, hai chấm, gạch nối (chấp nhận ! hoặc ?)
            if cand.endswith(('.', ',', ';', ':', '-', '–')):
                return False
                
            # 3. Không kết thúc bằng giới từ hoặc liên từ (chứng tỏ bị ngắt dòng giữa câu)
            if re.search(r'\b(and|or|of|in|to|the|a|an|that|with|for|as|by|on|at|from|is|are|was|were)\s*$', cand, re.I):
                return False
                
            # 4. Không bắt đầu bằng các từ nối đoạn văn hoặc liên từ mở đầu
            if re.match(r'(?i)^(Although|According|When|In the|During|From|After|While|Because|However|Therefore|Moreover|Furthermore|Since|If|As a|It was|There is|They are)\b', cand):
                return False
                
            return True

        # Helper: Trích xuất Title và làm sạch phần đầu bài đọc mà không phá vỡ các đoạn văn
        def _extract_title_and_clean_passage(raw_text: str, default_title: str) -> tuple[str, str]:
            if not raw_text or not raw_text.strip():
                return default_title, ""
            
            t = raw_text.strip()
            
            # 1. Xóa câu hướng dẫn You should spend... kể cả khi ngắt dòng ở giữa
            t = re.sub(r'(?i)^\s*You\s+should\s+spend\s+about\s+\d+\s+minut[eo]s\s+on\s+Questions?.*?(?:pages?\s+\d+.*?\n|\.\s*\n)', '\n\n', t, flags=re.DOTALL)
            # 2. Xóa các header IELTS ở đầu
            t = re.sub(r'(?i)^\s*(?:IELTS|TEST|ACADEMIC|GENERAL|PRACTICE|READING\s+TEST).*\n', '\n', t)
            
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n+', t) if p.strip()]
            if not paragraphs:
                return default_title, ""
                
            title = default_title
            cleaned_paragraphs = []
            
            for p in paragraphs:
                p_single_line = " ".join(p.split())
                # Lọc bỏ đoạn rác meta
                if re.match(r'(?i)^\s*(?:READING\s+PASSAGE\s+\d+|PASSAGE\s+\d+)(?:\s+on\s+pages?.*)?$', p_single_line):
                    continue
                if re.match(r'(?i)^\s*You\s+should\s+spend\s+about', p_single_line):
                    continue
                if re.match(r'(?i)^\s*(?:which\s+are\s+based\s+on\s+)?(?:Reading\s+Passage\s+\d+\s+)?(?:on\s+pages?.*)?$', p_single_line):
                    continue

                # Nếu chưa tìm thấy title:
                if title == default_title:
                    lines = [l.strip() for l in p.split('\n') if l.strip()]
                    first_line = lines[0]
                    
                    # Nếu cả đoạn p là tiêu đề ngắn (ví dụ: Destination Mars)
                    if len(lines) == 1 and _is_valid_title(first_line):
                        title = first_line
                        continue
                        
                    # Nếu tiêu đề dính với dòng đầu của đoạn (ví dụ: Make That Wine!\nAustralia is a nation...)
                    if len(lines) > 1 and _is_valid_title(first_line):
                        title = first_line
                        # Giữ nguyên phần còn lại của đoạn văn
                        p_remaining = '\n'.join(lines[1:])
                        cleaned_paragraphs.append(p_remaining)
                        continue

                cleaned_paragraphs.append(p)
                
            final_body = _clean_passage_paragraphs('\n\n'.join(cleaned_paragraphs))
            return title, final_body

        # Step 1: Tìm tất cả các Question Anchors thực sự (Loại bỏ câu hướng dẫn spend about... on Questions X-Y)
        raw_matches = list(re.finditer(r'(?i)\bQuestions?\s+(\d+)\s*[-–to\s]+\s*(\d+)', document_text))
        valid_q_matches = []
        for m in raw_matches:
            pre_text = document_text[max(0, m.start() - 80):m.start()]
            if re.search(r'(?i)spend\s+about.*?minutes\s+on\s*$', pre_text) or re.search(r'(?i)spend\s+about.*?on\s*$', pre_text):
                continue
            valid_q_matches.append({
                "start_q": int(m.group(1)),
                "end_q": int(m.group(2)),
                "start_pos": m.start(),
                "end_pos": m.end(),
                "text": m.group(0)
            })

        if not valid_q_matches:
            return None

        # Phân loại anchors theo 3 phần thi IELTS (P1: 1-14, P2: 14-27, P3: >=27)
        p1_anchors = [m for m in valid_q_matches if m["start_q"] <= 14 and m["end_q"] <= 14]
        p2_anchors = [m for m in valid_q_matches if 14 <= m["start_q"] <= 27 and m["end_q"] <= 27]
        p3_anchors = [m for m in valid_q_matches if m["start_q"] >= 27]

        if not p1_anchors or not p2_anchors or not p3_anchors:
            return None

        # Dò tìm các nhãn READING PASSAGE 1/2/3 độc lập (không phải nằm trong câu "based on Reading Passage X on pages...")
        all_rp = list(re.finditer(r'(?i)\bREADING\s+PASSAGE\s+([123])\b', document_text))
        valid_rp = []
        for m in all_rp:
            context_before = document_text[max(0, m.start() - 100) : m.start()].lower()
            if "based on" in context_before or "spend about" in context_before:
                continue
            valid_rp.append(m)
        
        rp2 = next((m for m in valid_rp if m.group(1) == '2'), None)
        rp3 = next((m for m in valid_rp if m.group(1) == '3'), None)

        p1_passage_raw = document_text[: p1_anchors[0]["start_pos"]]

        if rp2 and rp3:
            # === CHIẾN LƯỢC A: File chuẩn Cambridge có nhãn READING PASSAGE rõ ràng ===
            p1_q_text = document_text[p1_anchors[0]["start_pos"] : rp2.start()].strip()
            p2_passage_raw = document_text[rp2.start() : p2_anchors[0]["start_pos"]]
            p2_q_text = document_text[p2_anchors[0]["start_pos"] : rp3.start()].strip()
            p3_passage_raw = document_text[rp3.start() : p3_anchors[0]["start_pos"]]
            p3_q_text = document_text[p3_anchors[0]["start_pos"] :].strip()
        else:
            # === CHIẾN LƯỢC B: File không có nhãn READING PASSAGE (Dò tìm điểm kết thúc câu 13 và câu 26) ===
            chunk1 = document_text[p1_anchors[-1]["start_pos"] : p2_anchors[0]["start_pos"]]
            q_items1 = list(re.finditer(r'(?m)^\s*(?:1[234]\.\s*.*?(?:\n\s*[A-D]\b[^\n]+)+|1[234]\.\s+[^\n]+)', chunk1))
            if q_items1:
                p2_start_pos = p1_anchors[-1]["start_pos"] + q_items1[-1].end()
            else:
                p2_start_pos = p1_anchors[-1]["end_pos"]

            p1_q_text = document_text[p1_anchors[0]["start_pos"] : p2_start_pos].strip()
            p2_passage_raw = document_text[p2_start_pos : p2_anchors[0]["start_pos"]]

            chunk2 = document_text[p2_anchors[-1]["start_pos"] : p3_anchors[0]["start_pos"]]
            q_items2 = list(re.finditer(r'(?m)^\s*(?:2[567]\.\s*.*?(?:\n\s*[A-D]\b[^\n]+)+|2[567]\.\s+[^\n]+)', chunk2))
            if q_items2:
                p3_start_pos = p2_anchors[-1]["start_pos"] + q_items2[-1].end()
            else:
                p3_start_pos = p2_anchors[-1]["end_pos"]

            p2_q_text = document_text[p2_anchors[0]["start_pos"] : p3_start_pos].strip()
            p3_passage_raw = document_text[p3_start_pos : p3_anchors[0]["start_pos"]]
            p3_q_text = document_text[p3_anchors[0]["start_pos"] :].strip()

        # Cắt bỏ phần Task 2 Writing nếu bị dính vào cuối P3
        task2_match = re.search(r'(?i)\n\s*(Task\s+2|Writing\s+Task)', p3_q_text)
        if task2_match:
            p3_q_text = p3_q_text[:task2_match.start()].strip()

        p1_title, p1_content = _extract_title_and_clean_passage(p1_passage_raw, "Reading Passage 1")
        p2_title, p2_content = _extract_title_and_clean_passage(p2_passage_raw, "Reading Passage 2")
        p3_title, p3_content = _extract_title_and_clean_passage(p3_passage_raw, "Reading Passage 3")

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
        from app.services.schema_validator import extract_json_from_markdown
        
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
                raw_json = self._call_llm(
                    model=self.extractor_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=8192,
                    use_json_format=True
                )
                
                # --- DEBUG: Lưu raw json thuần ra file để kiểm tra ---
                try:
                    import os, time
                    debug_dir = os.path.join(os.getcwd(), "debug_logs")
                    os.makedirs(debug_dir, exist_ok=True)
                    timestamp = int(time.time())
                    debug_file = os.path.join(debug_dir, f"llm_output_ielts_{timestamp}_attempt_{attempt}.json")
                    clean_json_str = extract_json_from_markdown(raw_json)
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(clean_json_str)
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
                if isinstance(e, FileParsingError):
                    raise e
                logger.error(f"Lỗi API khi bóc tách IELTS Full Document: {str(e)}", exc_info=True)
                raise FileParsingError(f"Hệ thống AI lỗi: {str(e)}")

# Khởi tạo instance duy nhất (Singleton pattern) để import vào Celery Tasks
ai_parser = AIParserService()