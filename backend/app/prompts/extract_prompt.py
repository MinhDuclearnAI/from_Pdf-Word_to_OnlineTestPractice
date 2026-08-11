import re

# System Prompt thiết lập ranh giới cứng cho LLM, buộc nó phải hành xử như một Data Extractor.
EXTRACT_SYSTEM_PROMPT = """
Bạn là một chuyên gia AI cao cấp về xử lý dữ liệu giáo dục và bóc tách cấu trúc đề thi.
Nhiệm vụ của bạn là đọc toàn bộ nội dung văn bản thô của đề thi và bóc tách ĐẦY ĐỦ 100% tất cả các câu hỏi vào một cấu trúc JSON hợp lệ và nghiêm ngặt.

QUY TẮC BẮT BUỘC:
1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG MỘT KHỐI JSON HỢP LỆ (bắt đầu bằng { và kết thúc bằng }).
2. Tuyệt đối KHÔNG giải thích, KHÔNG thêm lời mở đầu hay kết thúc ngoài JSON.
3. ĐẢM BẢO BÓC TÁCH ĐẦY ĐỦ TẤT CẢ CÁC CÂU HỎI CÓ TRONG ĐỀ (Ví dụ đề có 40 câu thì phải bóc tách đủ 40 câu, không được dừng giữa chừng).
4. Giữ nguyên định dạng công thức toán, lý, hóa dưới dạng ký hiệu LaTeX chuẩn ($...$ hoặc $$...$$).
5. ĐỐI VỚI ĐỀ ĐỌC HIỂU (IELTS, TOEFL, Đọc hiểu Tiếng Anh / Ngữ Văn):
   - Trích xuất toàn bộ bài đọc (Reading Passage) vào trường "passage_text" của phần hoặc "passage_ref" của câu hỏi.
   - Giữ nguyên toàn bộ nội dung bài đọc, không được tóm tắt hay cắt bớt.
"""

# User Prompt chứa định nghĩa Schema chi tiết hỗ trợ cả dạng phẳng và dạng Section/Passage
EXTRACT_USER_PROMPT_TEMPLATE = """
Dưới đây là nội dung đề thi (hoặc một phần của đề thi):

--- BẮT ĐẦU NỘI DUNG ---
{document_text}
--- KẾT THÚC NỘI DUNG ---

Hãy bóc tách TẤT CẢ các câu hỏi có trong tài liệu trên thành JSON chuẩn.

QUY TẮC CẤU TRÚC JSON:
1. Nếu đề có chia theo Bài đọc / Phần (ví dụ: READING PASSAGE 1, PASSAGE 2, PART 1, PHẦN 1...):
   Hãy trả về theo cấu trúc "sections":
{{
    "sections": [
        {{
            "section_title": "Tên bài đọc / Phần (ví dụ: 'READING PASSAGE 1' hoặc 'Đọc hiểu 1')",
            "passage_text": "Toàn bộ nội dung bài đọc văn bản dài của phần này. Tuyệt đối không cắt bớt.",
            "questions": [
                {{
                    "id": "q1",
                    "type": "Phân loại: 'multiple_choice' (trắc nghiệm), 'fill_in_the_blank' (điền từ), 'essay' (tự luận/trả lời ngắn), hoặc 'math_equation' (toán/công thức)",
                    "question_text": "Nội dung câu hỏi đầy đủ",
                    "options": ["A. Lựa chọn 1", "B. Lựa chọn 2", "C. Lựa chọn 3", "D. Lựa chọn 4"],
                    "correct_answer": "Đáp án đúng nếu có trong đề (ví dụ 'A', 'True', 'False', 'Not Given'), nếu không có thì null",
                    "score_weight": 1.0,
                    "answer_placeholder": null
                }}
            ]
        }}
    ]
}}

2. Nếu đề là các câu hỏi thông thường (Toán, Lý, Hóa, Sử, Địa...) hoặc không có bài đọc dài:
   Bạn có thể trả về cấu trúc "questions":
{{
    "questions": [
        {{
            "id": "q1",
            "type": "multiple_choice | math_equation | fill_in_the_blank | essay",
            "question_text": "Nội dung đầy đủ của câu hỏi",
            "options": ["A. Lựa chọn 1", "B. Lựa chọn 2", "C. Lựa chọn 3", "D. Lựa chọn 4"],
            "correct_answer": "Đáp án đúng nếu có, hoặc null",
            "score_weight": 1.0,
            "part_title": null,
            "passage_ref": null,
            "answer_placeholder": null
        }}
    ]
}}

LƯU Ý: Phải trích xuất ĐẦY ĐỦ TẤT CẢ các câu hỏi từ đầu đến cuối mà không bỏ sót bất kỳ câu nào!
"""

def get_extraction_prompt(document_text: str) -> str:
    """
    Hàm tiện ích để chuẩn bị prompt bóc tách đề thi.
    Thực hiện tiền xử lý text thô để giúp LLM nhận diện cấu trúc tốt hơn.
    """
    cleaned_text = re.sub(r'\n{3,}', '\n\n', document_text).strip()
    return EXTRACT_USER_PROMPT_TEMPLATE.format(document_text=cleaned_text)