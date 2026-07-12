import os
import logging
from typing import List, Optional
from PIL import Image

# Import thư viện xử lý ảnh và OCR
# Yêu cầu hệ thống cài đặt sẵn poppler-utils và tesseract-ocr
from pdf2image import convert_from_path
import pytesseract

# Tái sử dụng hàm chuẩn hóa text từ file extractor để đảm bảo tính đồng nhất
from app.services.file_extractor import clean_and_normalize_text

logger = logging.getLogger(__name__)

class OCRError(Exception):
    """Custom exception khi luồng xử lý OCR gặp sự cố."""
    pass

def convert_pdf_to_images(file_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Chuyển đổi file PDF scan thành danh sách các đối tượng hình ảnh (PIL Images).
    DPI = 300 là mức chuẩn tối thiểu để Tesseract có thể nhận diện chính xác các ký tự nhỏ.
    """
    logger.info(f"Đang chuyển đổi PDF sang ảnh (DPI={dpi}): {file_path}")
    try:
        # Cần cài đặt poppler trên HĐH server (VD: apt-get install poppler-utils)
        images = convert_from_path(file_path, dpi=dpi)
        return images
    except Exception as e:
        logger.error(f"Lỗi khi dùng pdf2image cho file {file_path}: {str(e)}")
        raise OCRError(f"Không thể render PDF thành ảnh: {str(e)}")

def extract_text_from_image(image: Image.Image, lang: str = 'vie+eng') -> str:
    """
    Sử dụng Tesseract để bóc tách chữ từ một trang ảnh đơn lẻ.
    Mặc định nhận diện song ngữ Việt - Anh để xử lý tốt các đề thi đa môn.
    """
    try:
        # Cấu hình --psm 6 (Assume a single uniform block of text) thường hoạt động tốt 
        # với cấu trúc đề thi nếu không bị chia cột quá phức tạp.
        custom_config = r'--oem 3 --psm 6'
        
        # Nhận diện chữ. Yêu cầu server đã tải gói ngôn ngữ tesseract-ocr-vie
        text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
        return text
    except Exception as e:
        logger.error(f"Lỗi khi chạy Tesseract OCR trên trang ảnh: {str(e)}")
        # Không throw exception ngay để tránh chết toàn bộ luồng nếu chỉ 1 trang bị lỗi
        return ""

def process_scanned_pdf(file_path: str, lang: str = 'vie+eng') -> str:
    """
    Hàm entry point chính cho luồng OCR fallback.
    Nhận file PDF scan, chuyển thành ảnh, chạy OCR từng trang, làm sạch và nối lại.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File không tồn tại để chạy OCR: {file_path}")

    logger.info(f"Bắt đầu quy trình OCR toàn bộ cho file: {file_path}")
    
    extracted_text_blocks = []
    
    try:
        # 1. Chuyển PDF thành danh sách ảnh
        pages = convert_pdf_to_images(file_path)
        logger.info(f"File PDF có {len(pages)} trang. Bắt đầu nhận diện OCR...")

        # 2. Lặp qua từng trang để bóc chữ
        for page_num, page_image in enumerate(pages, start=1):
            logger.debug(f"Đang xử lý OCR trang {page_num}/{len(pages)}...")
            page_text = extract_text_from_image(page_image, lang=lang)
            
            if page_text.strip():
                extracted_text_blocks.append(page_text)
            else:
                logger.warning(f"Trang {page_num} không nhận diện được chữ nào.")

        # 3. Gộp toàn bộ text thô lại
        raw_combined_text = "\n\n".join(extracted_text_blocks)
        
        if not raw_combined_text.strip():
            raise OCRError("Hoàn thành OCR nhưng không thu được bất kỳ dữ liệu text nào.")

        # 4. Đẩy qua pipeline chuẩn hóa (spaCy) để làm sạch nhiễu, gộp câu đứt gãy
        final_cleaned_text = clean_and_normalize_text(raw_combined_text)
        
        logger.info(f"Quy trình OCR hoàn tất thành công cho file: {file_path}")
        return final_cleaned_text

    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng trong luồng xử lý OCR: {str(e)}")
        raise OCRError(f"OCR Pipeline thất bại: {str(e)}")

# ==============================================================================
# TÍNH NĂNG NÂNG CAO (OPTIONAL MỞ RỘNG CHO TƯƠNG LAI)
# ==============================================================================
def process_scanned_pdf_with_vision_llm(file_path: str) -> str:
    """
    (Mở rộng) Nếu Tesseract OCR thất bại với các đề thi có chứa nhiều công thức Toán học
    phức tạp (Integrals, Matrices), kiến trúc của chúng ta có thể chuyển hướng gọi trực tiếp
    các API Vision (Claude 3.5 Sonnet, GPT-4o Vision).
    
    Luồng:
    1. Chuyển PDF thành các file ảnh Base64.
    2. Đóng gói Base64 gửi kèm prompt "Hãy trích xuất toàn bộ chữ và công thức LaTeX".
    3. Trả về text đã được parse cực chuẩn.
    """
    pass