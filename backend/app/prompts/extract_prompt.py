import re

# System Prompt thiết lập ranh giới cứng cho LLM, buộc nó phải hành xử như một Data Extractor.
EXTRACT_SYSTEM_PROMPT = """
Bạn là một chuyên gia xử lý dữ liệu giáo dục và bóc tách đề thi. 
Nhiệm vụ của bạn là đọc nội dung văn bản thô của một đề thi và trích xuất từng câu hỏi ra một cấu trúc JSON cực kỳ nghiêm ngặt.

QUY TẮC TỐI QUAN TRỌNG:
1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG MỘT CHUỖI JSON HỢP LỆ.
2. Tuyệt đối KHÔNG giải thích, KHÔNG phân tích, KHÔNG thêm bất kỳ văn bản nào ngoài block ```json.
3. Đảm bảo cấu trúc mảng và đối tượng được đóng mở ngoặc chuẩn xác.
4. Giữ nguyên định dạng toán học, hóa học (nếu có) dưới dạng ký hiệu LaTeX chuẩn (ví dụ sử dụng $ hoặc $$).
"""

# User Prompt chứa định nghĩa Schema chi tiết để Frontend có thể render động (Dynamic Rendering).
EXTRACT_USER_PROMPT_TEMPLATE = """
Dưới đây là nội dung đề thi (hoặc một phần của đề thi):

--- BẮT ĐẦU NỘI DUNG ---
{document_text}
--- KẾT THÚC NỘI DUNG ---

Hãy bóc tách tất cả các câu hỏi có trong nội dung trên. 
Trả về MỘT đối tượng JSON có duy nhất một key là "questions", giá trị của nó là một mảng chứa các đối tượng câu hỏi.

Mỗi đối tượng câu hỏi PHẢI tuân thủ chính xác Schema sau:

{{
    "questions": [
        {{
            "id": "Tạo một ID duy nhất cho câu hỏi (ví dụ: 'q1', 'q2').",
            "type": "Phân loại UI Component. BẮT BUỘC chọn 1 trong các giá trị: 'multiple_choice' (trắc nghiệm), 'essay' (tự luận), 'latex_formula' (câu hỏi chứa công thức toán/lý/hóa phức tạp), 'reading_passage' (câu hỏi đọc hiểu tiếng Anh/IELTS).",
            "question_text": "Nội dung đầy đủ của câu hỏi.",
            "options": ["A. Nội dung 1", "B. Nội dung 2", "C. Nội dung 3", "D. Nội dung 4"], // Chỉ dùng cho câu multiple_choice, nếu không có hãy để mảng rỗng []
            "correct_answer": "Trích xuất đáp án đúng nếu có trong tài liệu (ví dụ: 'A'). Nếu không tìm thấy, trả về null.",
            "score_weight": 1.0, // Điểm mặc định cho câu hỏi này (thường là 1.0)
            "passage_ref": "CHỈ DÙNG CHO 'reading_passage'. Trích xuất toàn bộ nội dung đoạn văn bài đọc vào đây. Các câu hỏi thuộc cùng một bài đọc sẽ có nội dung passage_ref giống nhau. Nếu không phải bài đọc hiểu, trả về null.",
            "answer_placeholder": "Gợi ý hiển thị trong ô nhập liệu đối với câu 'essay' (ví dụ: 'Nhập câu trả lời tự luận...'). Trắc nghiệm thì để null."
        }}
    ]
}}
"""

def get_extraction_prompt(document_text: str) -> str:
    """
    Hàm tiện ích để chuẩn bị prompt bóc tách đề thi.
    Thực hiện tiền xử lý text thô để giúp LLM nhận diện cấu trúc tốt hơn.
    """
    # Loại bỏ các khoảng trắng thừa quá mức nhưng vẫn giữ lại cấu trúc ngắt dòng ( \n )
    # vì các câu trắc nghiệm thường được phân tách bằng dấu xuống dòng.
    cleaned_text = re.sub(r'\n{3,}', '\n\n', document_text).strip()