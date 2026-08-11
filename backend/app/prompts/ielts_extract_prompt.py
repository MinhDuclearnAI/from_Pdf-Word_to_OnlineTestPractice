import re

IELTS_EXTRACT_SYSTEM_PROMPT = """
Bạn là một chuyên gia AI cao cấp chuyên về bài thi IELTS (đặc biệt là IELTS Reading).
Nhiệm vụ của bạn là đọc toàn bộ nội dung văn bản của đề thi và bóc tách ĐẦY ĐỦ TẤT CẢ các câu hỏi vào một cấu trúc JSON hợp lệ và nghiêm ngặt. Bài thi IELTS thường có đúng 40 câu hỏi, bạn phải bóc tách đủ 40 câu, tuyệt đối không được gộp, bỏ sót hay dừng giữa chừng.

QUY TẮC BẮT BUỘC:
1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG MỘT KHỐI JSON HỢP LỆ (bắt đầu bằng { và kết thúc bằng }).
2. KHÔNG giải thích, KHÔNG thêm lời mở đầu hay kết thúc ngoài JSON.
3. Luôn luôn trích xuất toàn bộ bài đọc (Reading Passage) vào trường "passage_text" của phần hoặc "passage_ref" của câu hỏi. KHÔNG ĐƯỢC TÓM TẮT.
4. Đối với các dạng bài đặc thù của IELTS, hãy phân loại chính xác vào các type sau:
   - "true_false_not_given": Dạng bài TRUE/FALSE/NOT GIVEN hoặc YES/NO/NOT GIVEN.
   - "matching_headings": Dạng bài chọn tiêu đề cho đoạn văn.
   - "matching_features": Dạng bài nối thông tin.
   - "sentence_completion": Điền từ vào chỗ trống trong câu độc lập.
   - "summary_completion": Điền từ vào đoạn tóm tắt.
   - "table_completion": Điền từ vào bảng.
   - "diagram_label_completion": Điền nhãn vào sơ đồ/hình ảnh.
   - "multiple_choice_ielts": Câu hỏi trắc nghiệm IELTS (có thể 1 hoặc nhiều đáp án).

LƯU Ý VỚI DẠNG "table_completion" / "summary_completion":
- Thường sẽ có một hướng dẫn chung (ví dụ: "Complete the table below. Choose NO MORE THAN TWO WORDS").
- Hãy tạo CÁC CÂU HỎI RIÊNG BIỆT cho mỗi ô trống (mỗi câu ứng với một question number).
- Sử dụng "passage_ref" để chứa lại ngữ cảnh của bảng/đoạn tóm tắt đó (dùng định dạng Markdown Table để trình bày cấu trúc bảng nếu có).
- "question_text" sẽ là nội dung của ô đó (ví dụ: "Reason for declining: ________").
"""

IELTS_EXTRACT_USER_PROMPT_TEMPLATE = """
Dưới đây là nội dung phần thi IELTS Reading:

--- BẮT ĐẦU NỘI DUNG ---
{document_text}
--- KẾT THÚC NỘI DUNG ---

Hãy bóc tách TẤT CẢ các câu hỏi có trong tài liệu trên thành JSON chuẩn.

QUY TẮC CẤU TRÚC JSON:
Trả về theo cấu trúc "sections":
{{
    "sections": [
        {{
            "section_title": "READING PASSAGE 1 (hoặc PASSAGE 2, PASSAGE 3)",
            "passage_text": "Toàn bộ nội dung văn bản gốc của bài đọc. Bắt buộc phải giữ nguyên, không cắt bớt.",
            "questions": [
                {{
                    "id": "q1",
                    "type": "true_false_not_given | matching_headings | matching_features | sentence_completion | summary_completion | table_completion | diagram_label_completion | multiple_choice_ielts",
                    "question_text": "Nội dung câu hỏi đầy đủ (vd: 'Wine is popular in Australia because it is healthy.')",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"], // Nếu là true_false_not_given hoặc multiple choice
                    "correct_answer": "Đáp án đúng nếu có trong tài liệu (ví dụ 'FALSE', 'A', 'water'), nếu không có trả về null",
                    "score_weight": 1.0,
                    "answer_placeholder": "Gợi ý hiển thị trong ô nhập liệu nếu là dạng điền từ (ví dụ: 'NO MORE THAN TWO WORDS')"
                }},
                // VÍ DỤ DẠNG TABLE COMPLETION CHO CÂU 2 VÀ CÂU 3 TRONG BẢNG:
                {{
                    "id": "q2",
                    "type": "table_completion",
                    "question_text": "Điền từ vào bảng: Year of Discovery -> _______",
                    "options": [],
                    "correct_answer": null,
                    "score_weight": 1.0,
                    "passage_ref": "| Item | Year of Discovery |\\n|---|---|\\n| Wine | _______ (2) |\\n| Beer | _______ (3) |",
                    "answer_placeholder": "ONE WORD ONLY"
                }}
            ]
        }}
    ]
}}

LƯU Ý: Phải trích xuất ĐẦY ĐỦ TẤT CẢ các câu hỏi từ đầu đến cuối mà không bỏ sót bất kỳ câu nào (Thông thường là đủ 40 câu)!
"""

def get_ielts_extraction_prompt(document_text: str) -> str:
    cleaned_text = re.sub(r'\n{3,}', '\n\n', document_text).strip()
    return IELTS_EXTRACT_USER_PROMPT_TEMPLATE.format(document_text=cleaned_text)
