import os
import logging
import fitz  # PyMuPDF
import docx
from typing import Tuple
from io import BytesIO

logger = logging.getLogger(__name__)

class FileParsingError(Exception):
    """Custom exception khi không thể đọc hoặc parse file."""
    pass

BOLD_MARKER_START = "[[BOLD_START]]"
BOLD_MARKER_END = "[[BOLD_END]]"

def strip_structure_markers(text: str) -> str:
    """Loại bỏ các marker cấu trúc khỏi text trước khi lưu hoặc hiển thị."""
    if not text:
        return ""
    text = text.replace(BOLD_MARKER_START, "")
    text = text.replace(BOLD_MARKER_END, "")
    return text

def clean_and_normalize_text(raw_text: str) -> str:
    """
    Sử dụng spaCy để làm sạch các ký tự Unicode rác, chuẩn hóa khoảng trắng,
    giúp giảm thiểu token rác đẩy vào LLM, tiết kiệm chi phí và tăng độ chính xác.
    """
    if not raw_text or not raw_text.strip():
        return ""


    cleaned_lines = []
    for line in raw_text.splitlines():
        # Xóa khoảng trắng thừa ở đầu/cuối, chuẩn hóa multi-spaces thành 1 space
        cleaned_line = " ".join(line.split())
        if cleaned_line:
            cleaned_lines.append(cleaned_line)

    return "\n".join(cleaned_lines)

def extract_text_from_pdf(file_path: str) -> Tuple[str, bool]:
    """
    Trích xuất text từ file PDF sử dụng PyMuPDF.
    Trả về Tuple[text_đã_trích_xuất, is_scanned_pdf].
    """
    text_content = []
    is_scanned = True  # Giả định ban đầu là file scan

    try:
        from app.services.storage_service import storage
        
        # 1. Chạy pipeline inventory để tìm và crop ảnh chuẩn xác nhất (kể cả ảnh lẩn trong text)
        inventory = inventory_page(file_path)
        assets = extract_all_images_from_inventory(file_path, inventory)
        
        # Nhóm assets theo page
        page_assets = {}
        for asset in assets:
            p = asset["page"]
            if p not in page_assets:
                page_assets[p] = []
            page_assets[p].append(asset["image_url"])

        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Chèn thẻ IMAGE_REF của trang này vào trước nội dung text của trang
            if page_num in page_assets:
                for img_url in page_assets[page_num]:
                    text_content.append(f"\n[[IMAGE_REF: {img_url}]]\n")
            
            # Sử dụng sort=True để PyMuPDF tự động phán đoán thứ tự đọc (Reading Order)
            blocks = page.get_text("blocks", sort=True)
            for b in blocks:
                if b[6] == 0: # Text block
                    page_text = b[4]
                    if page_text.strip():
                        is_scanned = False
                        text_content.append(page_text)
                # Bỏ qua b[6] == 1 (Image block) ở đây vì đã xử lý qua inventory_page ở trên

        doc.close()
        
        raw_text = "\n\n".join(text_content)
        normalized_text = clean_and_normalize_text(raw_text)
        
        return normalized_text, is_scanned

    except Exception as e:
        logger.error(f"Lỗi khi đọc file PDF {file_path}: {str(e)}")
        raise FileParsingError(f"Không thể trích xuất PDF: {str(e)}")

def inventory_page(file_path: str) -> list:
    """
    Kiểm kê từng trang PDF: có ảnh nhúng không, có vùng vẽ vector không, độ dài text.
    """
    inventory = []
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            images = page.get_images()
            drawings = page.get_drawings()
            text = page.get_text("text")
            
            image_rects = []
            for img_info in images:
                xref = img_info[0]
                rects = page.get_image_rects(xref)
                for rect in rects:
                    image_rects.append({
                        "x0": rect.x0, "y0": rect.y0, "x1": rect.x1, "y1": rect.y1
                    })
            
            drawing_rects = []
            for d in drawings:
                rect = d["rect"]
                drawing_rects.append({
                    "x0": rect.x0, "y0": rect.y0, "x1": rect.x1, "y1": rect.y1
                })
            
            inventory.append({
                "page": page_num,
                "has_image": len(images) > 0,
                "has_vector": len(drawings) > 0,
                "text_len": len(text.strip()),
                "image_rects": image_rects,
                "drawing_rects": [] # Bỏ qua vector drawings vì PyMuPDF lấy cả các đường kẻ viền bảng, sinh ra rác
            })
        doc.close()
    except Exception as e:
        logger.error(f"Lỗi khi kiểm kê PDF {file_path}: {e}")
    return inventory

def process_image_blocks(file_path: str, image_blocks: list) -> list:
    """
    (Deprecated) Dùng extract_all_images_from_inventory thay thế.
    """
    pass

def extract_all_images_from_inventory(file_path: str, inventory: list) -> list:
    """
    Tự động crop tất cả ảnh từ inventory (tránh mất ảnh), upload và trả về list URL.
    """
    assets_found = []
    try:
        from app.services.storage_service import storage
        doc = fitz.open(file_path)
        
        img_counter = 1
        for page_data in inventory:
            page_num = page_data.get("page", 0)
            rects = page_data.get("image_rects", []) + page_data.get("drawing_rects", [])
            
            if not rects:
                continue
                
            page = doc.load_page(page_num)
            for rect_dict in rects:
                rect = fitz.Rect(rect_dict["x0"], rect_dict["y0"], rect_dict["x1"], rect_dict["y1"])
                try:
                    cropped_pix = page.get_pixmap(clip=rect, dpi=150)
                    cropped_bytes = cropped_pix.tobytes("jpeg")
                    
                    file_obj = BytesIO(cropped_bytes)
                    original_name = f"auto_crop_p{page_num}_{img_counter}.jpg"
                    object_name = storage.upload_file(file_obj, original_name, content_type="image/jpeg", folder="exams/diagrams")
                    
                    image_url = storage.get_presigned_url(object_name, expiration=7*24*3600)
                    
                    if image_url:
                        assets_found.append({
                            "page": page_num,
                            "image_url": image_url
                        })
                    img_counter += 1
                except Exception as crop_err:
                    logger.error(f"Lỗi khi crop ảnh tại trang {page_num}: {crop_err}")
                    
        doc.close()
    except Exception as e:
        logger.error(f"Lỗi khi trích xuất toàn bộ ảnh từ {file_path}: {e}")
        
    return assets_found

def extract_text_from_docx(file_path: str) -> str:
    """
    Trích xuất text từ file Word (.docx), bao gồm cả các đoạn văn thông thường
    và dữ liệu nằm trong các bảng biểu (Tables).
    """
    text_content = []

    try:
        doc = docx.Document(file_path)
        
        # 1. Đọc các đoạn văn bản (Paragraphs)
        for para in doc.paragraphs:
            if para.text.strip():
                text_content.append(para.text)

        # 2. Đọc dữ liệu trong các bảng biểu (rất phổ biến trong đề thi Tiếng Anh/Văn)
        for table in doc.tables:
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    if cell.text.strip():
                        # Thay thế \n trong cell thành khoảng trắng để không làm vỡ format
                        row_data.append(cell.text.strip().replace("\n", " "))
                if row_data:
                    text_content.append(" | ".join(row_data))
                    
        raw_text = "\n".join(text_content)
        return clean_and_normalize_text(raw_text)

    except Exception as e:
        logger.error(f"Lỗi khi đọc file DOCX {file_path}: {str(e)}")
        raise FileParsingError(f"Không thể trích xuất DOCX: {str(e)}")

def process_file(file_path: str, mime_type: str) -> str:
    """
    Hàm main entry point để gọi từ Celery Worker.
    Dựa vào MIME type để điều hướng sang hàm trích xuất tương ứng.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File không tồn tại trên hệ thống: {file_path}")

    logger.info(f"Bắt đầu trích xuất file: {file_path} (MIME: {mime_type})")

    if mime_type == "application/pdf":
        extracted_text, is_scanned = extract_text_from_pdf(file_path)
        
        if is_scanned:
            logger.warning(f"File {file_path} là định dạng PDF Scan/Ảnh.")
            # TODO: Implement trigger OCR flow tại đây (ví dụ gọi ocr_service.py)
            # return ocr_service.process_scanned_pdf(file_path)
            
        return extracted_text

    elif mime_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
        "application/msword"
    ]:
        return extract_text_from_docx(file_path)
    
    else:
        raise FileParsingError(f"Định dạng file không được hỗ trợ: {mime_type}")