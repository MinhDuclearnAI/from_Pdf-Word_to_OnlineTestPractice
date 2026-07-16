import os
import logging
import fitz  # PyMuPDF
import docx
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class FileParsingError(Exception):
    """Custom exception khi không thể đọc hoặc parse file."""
    pass

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
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Sử dụng sort=True để PyMuPDF tự động phán đoán thứ tự đọc (Reading Order)
            # Rất hữu ích với các đề thi chia 2 cột
            page_text = page.get_text("text", sort=True)
            
            if page_text.strip():
                is_scanned = False  # Nếu trích xuất được text, đây là text-based PDF
                text_content.append(page_text)
            
            # Có thể chèn thêm logic trích xuất bảng (tables) của PyMuPDF nếu cần thiết tại đây

        doc.close()
        
        raw_text = "\n\n".join(text_content)
        normalized_text = clean_and_normalize_text(raw_text)
        
        return normalized_text, is_scanned

    except Exception as e:
        logger.error(f"Lỗi khi đọc file PDF {file_path}: {str(e)}")
        raise FileParsingError(f"Không thể trích xuất PDF: {str(e)}")

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