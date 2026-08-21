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
import fitz
import json
from io import BytesIO
# Import Celery instance đã được cấu hình
from app.core.celery_app import celery_app

# Import Database session manager (Context manager chuyên cho background tasks)
from app.db.session import get_db_session

# Import Models
from app.models.ai_job import AIProcessingJob
from app.models.exam import Exam
from app.models.question import Question
from app.schemas.question import QuestionSchema

# Import Services
from app.services.storage_service import storage
from app.services.notification_service import notification

from app.services import file_extractor
from app.services.ai_parser import ai_parser
# from app.services.passage_segmenter import segment_document
# from app.services.block_detector import detect_blocks

logger = logging.getLogger(__name__)

def crop_table_via_llm(pdf_path: str, block_content: str, instruction: str = "") -> str:
    """Helper function to find table bounds using LLM and crop it."""
    try:
        if not block_content or len(block_content.strip()) < 10:
            return None
            
        doc = fitz.open(pdf_path)
        page_num_hint = -1
        
        search_text = instruction if (instruction and len(instruction) > 10) else block_content
        words = [w for w in search_text.replace("|", " ").replace("-", " ").split() if len(w) > 4]
        
        if len(words) >= 2:
            for p_num in range(len(doc)):
                text = doc.load_page(p_num).get_text()
                matches = sum(1 for w in words[:5] if w in text)
                if matches >= 2:
                    page_num_hint = p_num
                    break
        
        if page_num_hint < 0 or page_num_hint >= len(doc):
            return None
            
        page = doc.load_page(page_num_hint)
        blocks = page.get_text("blocks", sort=True)
        
        # Build text map with coordinates
        lines = []
        for b in blocks:
            if b[6] == 0: # text
                lines.append(f"[Y0: {b[1]:.1f}, Y1: {b[3]:.1f}] {b[4].strip()}")
        coord_text = "\n".join(lines)
        
        # Call LLM
        prompt = f'''
Here is the text of a PDF page with Y-coordinates [Y0, Y1] for each text block:
{coord_text}

Here is the content of a table/diagram/flowchart we need to find on this page:
{block_content[:1000]}

Find the exact y0 (start) and y1 (end) coordinates of this table/diagram on the page.
Output ONLY valid JSON in this format: {{"y0": float, "y1": float}}
'''
        # Use ai_parser client
        from app.services.ai_parser import ai_parser
        response = ai_parser.client.chat.completions.create(
            model="gemini-1.5-pro",
            messages=[
                {"role": "system", "content": "You are a precise table bounding box locator. Output ONLY JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        res_json = json.loads(response.choices[0].message.content)
        y0 = float(res_json.get("y0", 0))
        y1 = float(res_json.get("y1", 0))
        
        if y1 > y0 > 0:
            rect = fitz.Rect(0, y0 - 15, page.rect.width, y1 + 15)
            pix = page.get_pixmap(clip=rect, dpi=150)
            file_obj = BytesIO(pix.tobytes("jpeg"))
            from app.services.storage_service import storage
            object_name = storage.upload_file(file_obj, f"llm_crop_{page_num_hint}_{y0}.jpg", content_type="image/jpeg", folder="exams/diagrams")
            return storage.get_presigned_url(object_name, expiration=7*24*3600)
    except Exception as e:
        logger.error(f"Lỗi khi dùng LLM cắt ảnh bảng biểu: {e}")
    return None

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
            
            # --- DEBUG: Lưu raw text ra file để kiểm tra ---
            try:
                debug_dir = os.path.join(os.getcwd(), "debug_logs")
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(debug_dir, f"raw_text_job_{job_id}.txt")
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(document_text)
                logger.info(f"Đã lưu raw text của Job {job_id} vào {debug_file}")
            except Exception as e:
                logger.warning(f"Lỗi khi lưu debug raw text: {e}")
            # -----------------------------------------------
            
            if not document_text or len(document_text.strip()) < 50:
                raise ValueError("Không thể trích xuất văn bản từ file hoặc file quá ngắn.")

            # Giai đoạn 0: Build page_assets map để dùng fallback map ảnh Raster chắc chắn hơn LLM
            page_assets: dict = {}  # {page_num: [image_url, ...]}
            if mime_type == "application/pdf":
                notification.publish_job_status(job_id, "processing", 42, "Đang trích xuất văn bản và hình ảnh inline...")
                try:
                    from app.services.file_extractor import inventory_page, extract_all_images_from_inventory
                    _inventory = inventory_page(local_file_path)
                    _assets = extract_all_images_from_inventory(local_file_path, _inventory)
                    for _a in _assets:
                        _p = _a["page"]
                        page_assets.setdefault(_p, []).append(_a["image_url"])
                    logger.info(f"[ImageMap] Đã build page_assets: {len(_assets)} ảnh trên {len(page_assets)} trang")
                except Exception as _img_err:
                    logger.warning(f"[ImageMap] Không thể build page_assets: {_img_err}")
            
            # 6. Pass 2: Bóc tách từng câu hỏi qua AI
            notification.publish_job_status(job_id, "processing", 60, "AI đang bóc tách từng câu hỏi và gán nhãn...")
            
            real_subject = subject
            # Theo yêu cầu của user: Phụ thuộc 100% vào loại mà user chọn trên UI.
            # Nếu user KHÔNG chọn IELTS, nhưng Regex/Heuristic nhận diện đây là đề IELTS -> Báo lỗi ngay lập tức.
            if subject.upper() != "IELTS":
                if "IELTS" in document_text[:1000].upper() or "IELTS" in title.upper():
                    raise Exception("Lỗi: Môn học bạn chọn trên hệ thống không khớp với nội dung file. Hệ thống nhận diện đây là đề thi IELTS, vui lòng chọn môn học/dạng đề là IELTS để đảm bảo bóc tách chuẩn 3 Passages.")

            master_questions = []
            passage_parents_data = [] # Data để tạo parent question

            if real_subject == "IELTS":
                # NHÁNH ĐẶC TRỊ IELTS: 1 Request duy nhất lấy toàn bộ cấu trúc
                notification.publish_job_status(job_id, "processing", 50, "AI đang đọc và bóc tách toàn bộ 3 bài đọc IELTS (1 Request)...")
                parsed_exam_ielts = ai_parser.extract_ielts_full_document(document_text)
                
                # Validation 1: Đúng 3 Passages
                if len(parsed_exam_ielts.passages) != 3:
                    raise Exception(f"Lỗi Bóc Tách: Đề thi IELTS bắt buộc phải nhận diện đúng 3 Bài Đọc (Passages). Hệ thống nhận diện ra {len(parsed_exam_ielts.passages)} đoạn. Vui lòng kiểm tra lại cấu trúc file PDF.")
                
                for passage_idx, passage in enumerate(parsed_exam_ielts.passages):
                    # Frontend expects tabs to be named "Passage 1", "Passage 2", etc.
                    p_tab_title = f"Passage {passage_idx + 1}"
                    p_content = f"**{passage.title}**\n\n{passage.content}" if passage.title else passage.content
                    p_ref_val = p_content
                    
                    passage_parents_data.append({
                        "p_ref": p_ref_val,
                        "title": p_tab_title
                    })

                    for block in passage.blocks:
                        q_count = (block.range_end - block.range_start + 1) if block.range_end and block.range_start else len(block.questions)
                        
                        img_url = getattr(block, 'image_url', None)
                        
                        is_grouped = block.range_start is not None and block.range_end is not None and block.range_start != block.range_end
                        groupable_types = ["table_completion", "summary_completion", "diagram_label_completion", "sentence_completion", "matching_features"]
                        
                        if is_grouped or block.instruction:
                            instruction = block.instruction if block.instruction else ""
                            b_content = block.block_content if block.block_content else ""
                            range_text = f"**Questions {block.range_start}-{block.range_end}**" if block.range_start and block.range_end else ""

                            # Strip [[IMAGE_REF: url]] from text fields — these are internal pipeline markers,
                            # must NEVER appear in the Red Badge or question text shown to students
                            import re as _re
                            _IMAGE_REF_PATTERN = _re.compile(r'\[\[IMAGE_REF:\s*[^\]]+\]\]', _re.IGNORECASE)
                            instruction = _IMAGE_REF_PATTERN.sub('', instruction).strip()
                            b_content = _IMAGE_REF_PATTERN.sub('', b_content).strip()
                            
                            # ===== DETERMINISTIC IMAGE MAPPING (ưu tiên tuyệt đối) =====
                            # Bước 1: Nếu LLM đã trích xuất được image_url từ [[IMAGE_REF:...]] → giữ nguyên
                            # Bước 2: Nếu LLM quên → dùng page_assets để map ảnh Raster theo trang chứa instruction
                            if not img_url and block.type in ["table_completion", "diagram_label_completion", "matching_features"]:
                                if page_assets:
                                    import fitz as _fitz
                                    try:
                                        _doc = _fitz.open(local_file_path)
                                        _found_page = None
                                        # Tìm trang đầu tiên chứa instruction text
                                        _search_text = instruction[:80] if instruction else (b_content[:80] if b_content else "")
                                        if _search_text:
                                            for _pn in range(len(_doc)):
                                                _pg = _doc.load_page(_pn)
                                                if _pg.search_for(_search_text):
                                                    _found_page = _pn
                                                    break
                                        _doc.close()
                                        # Nếu tìm thấy trang, lấy ảnh đầu tiên của trang đó
                                        if _found_page is not None and _found_page in page_assets:
                                            img_url = page_assets[_found_page][0]
                                            logger.info(f"[ImageMap] Gán ảnh Raster từ trang {_found_page} cho block '{block.block_id}'")
                                        elif _found_page is not None:
                                            # Thử trang kề (ảnh thường nằm trang sau instruction)
                                            if (_found_page + 1) in page_assets:
                                                img_url = page_assets[_found_page + 1][0]
                                                logger.info(f"[ImageMap] Gán ảnh Raster từ trang kề {_found_page+1} cho block '{block.block_id}'")
                                    except Exception as _map_err:
                                        logger.warning(f"[ImageMap] Lỗi khi map ảnh theo trang: {_map_err}")
                            
                            # Bước 3: Chỉ khi vẫn không có ảnh → fallback crop Vector bằng LLM
                            if not img_url and block.type in ["table_completion", "diagram_label_completion", "matching_features"]:
                                img_url = crop_table_via_llm(local_file_path, b_content, instruction)
                            
                            # Visual Override: Nếu có ảnh và là dạng bảng/sơ đồ, bỏ qua OCR text
                            if block.type in groupable_types:
                                if img_url and block.type in ["table_completion", "diagram_label_completion", "matching_features"]:
                                    # Có ảnh: chỉ giữ instruction, KHÔNG thêm [blank_N] vào question_text
                                    # Frontend sẽ dùng childQuestions để render Grid Inputs
                                    q_text = instruction.strip()
                                else:
                                    # Tránh bị đúp ô trống: chỉ thêm [blank] nếu trong text KHÔNG CÓ sẵn ___
                                    if "___" not in b_content and "[blank" not in b_content:
                                        blanks = "\n".join([f"[blank_{i}]" for i in range(1, q_count + 1)])
                                        q_text = f"{instruction}\n\n{b_content}\n\n{blanks}".strip()
                                    else:
                                        q_text = f"{instruction}\n\n{b_content}".strip()
                            else:
                                # Not groupable (e.g. TFNG, short_answer) -> show instruction + b_content
                                q_text = f"{instruction}\n\n{b_content}".strip()
                            
                            answers = [getattr(q, 'correct_answer', '') for q in block.questions]
                            import json
                            merged_answers = json.dumps(answers, ensure_ascii=False) if any(answers) else ""

                            parent_q = QuestionSchema(
                                id=block.block_id,
                                block_id=block.block_id,
                                type=block.type,
                                question_text=q_text,
                                options=[],
                                correct_answer=merged_answers,
                                image_url=img_url,
                                passage_ref=p_ref_val,
                                part_title=p_tab_title,
                                is_block_parent=True,
                                original_question_number=block.range_start
                            )
                            master_questions.append(parent_q)
                            
                            # TẠO CÁC CÂU HỎI CON VÀ TRỎ VỀ CHA
                            children_generated = 0
                            for idx, q in enumerate(block.questions):
                                # Kiểm tra Anchor ID chống câu hỏi rác
                                orig_num = getattr(q, 'original_question_number', None)
                                if orig_num is not None and block.range_start is not None and block.range_end is not None:
                                    if orig_num < block.range_start or orig_num > block.range_end:
                                        logger.warning(f"Drop câu rác do ảo giác: {orig_num} không nằm trong {block.range_start}-{block.range_end}")
                                        continue

                                child_q = QuestionSchema(
                                    id=q.id if getattr(q, 'id', None) else f"{block.block_id}_{idx}",
                                    original_question_number=orig_num,
                                    block_id=block.block_id,
                                    type=getattr(q, 'type', None) or block.type,
                                    question_text=q.question_text,
                                    options=getattr(q, 'options', []),
                                    correct_answer=getattr(q, 'correct_answer', ""),
                                    image_url=None, 
                                    passage_ref=p_ref_val,
                                    part_title=p_tab_title,
                                    parent_block_id=block.block_id
                                )
                                master_questions.append(child_q)
                                children_generated += 1
                                
                            # Fallback Auto-Recovery: Nếu LLM quên hoặc bị drop hết, tự sinh đủ câu
                            if children_generated == 0 and block.range_start and block.range_end:
                                for orig_num in range(block.range_start, block.range_end + 1):
                                    child_q = QuestionSchema(
                                        id=f"{block.block_id}_fallback_{orig_num}",
                                        original_question_number=orig_num,
                                        block_id=block.block_id,
                                        type="fill_in_the_blank",
                                        question_text=f"Question {orig_num}",
                                        options=[],
                                        correct_answer="",
                                        image_url=None,
                                        passage_ref=p_ref_val,
                                        part_title=p_tab_title,
                                        parent_block_id=block.block_id
                                    )
                                    master_questions.append(child_q)

                        else:
                            # Tạo các câu hỏi độc lập (hoặc block chứa 1 câu)
                            for idx, q in enumerate(block.questions):
                                orig_num = getattr(q, 'original_question_number', None)
                                if orig_num is not None and block.range_start is not None and block.range_end is not None:
                                    if orig_num < block.range_start or orig_num > block.range_end:
                                        logger.warning(f"Drop câu rác do ảo giác: {orig_num} không nằm trong {block.range_start}-{block.range_end}")
                                        continue

                                final_type = getattr(q, 'type', None) or block.type
                                final_options = getattr(q, 'options', [])
                                
                                # Xử lý UX cho True/False/Not Given
                                if final_type == "true_false_not_given" and not final_options:
                                    q_text_lower = (q.question_text or "").lower()
                                    if "yes" in q_text_lower or "no" in q_text_lower:
                                        final_options = ["Yes", "No", "Not Given"]
                                    else:
                                        final_options = ["True", "False", "Not Given"]

                                q_schema = QuestionSchema(
                                    id=q.id if getattr(q, 'id', None) else f"{block.block_id}_{idx}",
                                    original_question_number=orig_num,
                                    block_id=block.block_id,
                                    type=final_type,
                                    question_text=q.question_text,
                                    options=final_options,
                                    correct_answer=getattr(q, 'correct_answer', ""),
                                    image_url=img_url if idx == 0 else None,
                                    passage_ref=p_ref_val,
                                    part_title=p_tab_title
                                )
                                master_questions.append(q_schema)

                # Đếm tổng số câu hỏi thực tế sau khi tạo cấu trúc (chỉ đếm câu hỏi con/độc lập, bỏ qua parent block)
                total_parsed = 0
                for q in master_questions:
                    if not getattr(q, "is_block_parent", False):
                        total_parsed += 1

                # Validation 2: Số câu hỏi ~40
                if not (38 <= total_parsed <= 42):
                    raise Exception(f"Lỗi Bóc Tách: Đề thi IELTS chuẩn phải có khoảng 40 câu hỏi. Hệ thống hiện tại nhận diện được {total_parsed} câu. Vui lòng kiểm tra lại các đánh số câu hỏi trong file PDF.")
            
            else:
                # NHÁNH STANDARD (Generic)
                notification.publish_job_status(job_id, "processing", 50, "AI đang đọc và bóc tách toàn bộ đề thi (1 Request)...")
                parsed_exam_standard = ai_parser.extract_batched_blocks(document_text, subject=real_subject)
                
                if not parsed_exam_standard or not parsed_exam_standard.questions:
                    raise Exception("Lỗi Bóc Tách: AI không thể nhận diện được câu hỏi nào từ file này.")
                    
                import re as _re
                _IMAGE_REF_PATTERN = _re.compile(r'\[\[IMAGE_REF:\s*[^\]]+\]\]', _re.IGNORECASE)

                for q_idx, q in enumerate(parsed_exam_standard.questions):
                    orig_num = getattr(q, 'original_question_number', None)
                    if orig_num is None:
                        orig_num = q_idx + 1

                    final_type = getattr(q, 'type', "multiple_choice")
                    final_options = getattr(q, 'options', [])
                    
                    q_text_clean = _IMAGE_REF_PATTERN.sub('', q.question_text).strip() if q.question_text else ""

                    q_schema = QuestionSchema(
                        id=q.id if getattr(q, 'id', None) else f"q_{q_idx}",
                        original_question_number=orig_num,
                        type=final_type,
                        question_text=q_text_clean,
                        options=final_options,
                        correct_answer=getattr(q, 'correct_answer', ""),
                        image_url=getattr(q, 'image_url', None),
                        part_title=getattr(q, 'part_title', None)
                    )
                    master_questions.append(q_schema)


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
                    subject=real_subject, # Đã sửa thành real_subject
                    exam_type=normalized_exam_type,
                    duration=duration,
                    result_visibility="full",
                    creator_id=job.creator_id
                )
                db.add(new_exam)
                db.flush() 

                # Tạo Parent Questions cho các đoạn Passage để tiết kiệm bộ nhớ (Lỗi D)
                passage_db_map = {}
                for p_data in passage_parents_data:
                    p_ref = p_data["p_ref"]
                    if p_ref not in passage_db_map:
                        parent_q = Question(
                            exam_id=new_exam.id,
                            component_type="reading_passage",
                            question_text=p_data["title"],
                            passage_ref=p_ref
                        )
                        db.add(parent_q)
                        db.flush()
                        passage_db_map[p_ref] = parent_q.id

                # Tầng 2: Insert các Block Parents
                block_db_map = {}
                for q_data in master_questions:
                    if getattr(q_data, "is_block_parent", False):
                        db_type = q_data.type
                        if db_type == "latex_formula":
                            db_type = "math_equation"
                        elif db_type == "writing":
                            db_type = "essay"
                        elif db_type == "fill_blank":
                            db_type = "fill_in_the_blank"

                        parent_id = None
                        final_passage_ref = getattr(q_data, "passage_ref", None)
                        if final_passage_ref in passage_db_map:
                            parent_id = passage_db_map[final_passage_ref]
                            final_passage_ref = None

                        new_block_q = Question(
                            exam_id=new_exam.id,
                            parent_id=parent_id,
                            component_type=db_type,
                            question_text=q_data.question_text,
                            options=q_data.options if q_data.options else [],
                            correct_answer=q_data.correct_answer,
                            score_weight=getattr(q_data, "score_weight", 1.0),
                            passage_ref=final_passage_ref,
                            answer_placeholder=getattr(q_data, "answer_placeholder", None),
                            image_url=getattr(q_data, "image_url", None),
                            original_question_number=getattr(q_data, "original_question_number", None)
                        )
                        db.add(new_block_q)
                        db.flush()
                        if q_data.block_id:
                            block_db_map[q_data.block_id] = new_block_q.id

                # Tầng 3: Insert các câu hỏi con (Sub-questions) và câu hỏi độc lập
                for q_data in master_questions:
                    if getattr(q_data, "is_block_parent", False):
                        continue # Đã insert ở trên

                    db_type = q_data.type
                    if db_type == "latex_formula":
                        db_type = "math_equation"
                    elif db_type == "writing":
                        db_type = "essay"
                    elif db_type == "fill_blank":
                        db_type = "fill_in_the_blank"

                    parent_id = None
                    final_passage_ref = getattr(q_data, "passage_ref", None)
                    
                    # Nếu là câu hỏi con của một block, trỏ parent_id về block đó
                    if getattr(q_data, "parent_block_id", None) and q_data.parent_block_id in block_db_map:
                        parent_id = block_db_map[q_data.parent_block_id]
                        final_passage_ref = None
                    # Nếu là câu độc lập, trỏ về passage
                    elif final_passage_ref in passage_db_map:
                        parent_id = passage_db_map[final_passage_ref]
                        final_passage_ref = None

                    new_question = Question(
                        exam_id=new_exam.id,
                        parent_id=parent_id,
                        component_type=db_type,
                        question_text=q_data.question_text,
                        options=q_data.options if q_data.options else [],
                        correct_answer=q_data.correct_answer,
                        score_weight=getattr(q_data, "score_weight", 1.0),
                        passage_ref=final_passage_ref,
                        answer_placeholder=getattr(q_data, "answer_placeholder", None),
                        image_url=getattr(q_data, "image_url", None),
                        original_question_number=getattr(q_data, "original_question_number", None)
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