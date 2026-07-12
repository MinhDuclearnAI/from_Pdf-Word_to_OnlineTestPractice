# backend/app/prompts/classify_prompt.py

# System Prompt định hình vai trò của LLM và thiết lập quy tắc bắt buộc về định dạng đầu ra.
CLASSIFY_SYSTEM_PROMPT = """
Bạn là một chuyên gia phân tích dữ liệu giáo dục cho một nền tảng thi trực tuyến. 
Nhiệm vụ của bạn là đọc một phần nội dung (thường là trang đầu tiên) của một tài liệu tải lên và trích xuất các thông tin phân loại cốt lõi.

QUY TẮC TỐI QUAN TRỌNG:
1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ MỘT CHUỖI JSON HỢP LỆ.
2. Tuyệt đối KHÔNG giải thích, KHÔNG chào hỏi, KHÔNG sử dụng markdown format ngoài block ```json.
3. Nếu không tìm thấy thông tin cho một trường cụ thể, hãy trả về giá trị null.
"""

# User Prompt chứa dữ liệu thực tế và định nghĩa Schema mà LLM cần tuân thủ.
CLASSIFY_USER_PROMPT_TEMPLATE = """
Dưới đây là nội dung thô được trích xuất từ phần đầu của tài liệu người dùng tải lên:

--- BẮT ĐẦU TÀI LIỆU ---
{document_text}
--- KẾT THÚC TÀI LIỆU ---

Dựa vào nội dung trên, hãy phân tích và trả về đúng cấu trúc JSON sau:

{{
    "title": "Trích xuất tên đầy đủ của đề thi hoặc tiêu đề tài liệu (ví dụ: 'Đề thi thử THPT Quốc gia môn Toán lần 1', 'IELTS Reading Practice Test 1').",
    "subject": "Phân loại môn học. Bắt buộc chọn đúng 1 trong các giá trị sau: 'Toán', 'Vật Lý', 'Hóa Học', 'Sinh Học', 'Tiếng Anh', 'IELTS', 'HSA', hoặc 'Khác'.",
    "test_type": "Phân loại mục đích. Bắt buộc chọn 'practice' (nếu là bài tập, đề cương, tài liệu tự luyện) hoặc 'exam' (nếu là đề thi định kỳ, thi thử, kiểm tra 15p/1 tiết).",
    "duration": "Thời gian làm bài tính bằng phút (chỉ trả về số nguyên, ví dụ: 15, 45, 90, 120. Nếu không tìm thấy, trả về null)."
}}
"""

def get_classification_prompt(document_text: str) -> str:
    """
    Hàm tiện ích để chèn nội dung tài liệu vào template một cách an toàn.
    Chỉ nên truyền vào khoảng 2000 - 3000 ký tự đầu tiên của tài liệu để tiết kiệm token và tăng tốc độ,
    vì thông tin phân loại (tiêu đề, thời gian, môn học) hầu như luôn nằm ở trang 1.
    """
    # Xử lý text an toàn: loại bỏ các ký tự khoảng trắng thừa
    cleaned_text = " ".join(document_text.split())
    
    # Format template với text đã xử lý
    return CLASSIFY_USER_PROMPT_TEMPLATE.format(document_text=cleaned_text)