import re

EXTRACT_SYSTEM_PROMPT = """
Bạn là một chuyên gia AI cao cấp về phân tích dữ liệu giáo dục.
Nhiệm vụ của bạn là nhận vào một tập hợp các "Blocks" câu hỏi của đề thi và trích xuất cấu trúc câu hỏi thành mảng JSON.
Các Blocks được phân tách rõ ràng bằng các đường viền ===================.

QUY TẮC VÀNG (BẮT BUỘC):
1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG MỘT KHỐI JSON HỢP LỆ.
2. KHÔNG BAO GIỜ TỰ Ý CHÉP LẠI (REPRODUCE) NỘI DUNG NÀO KHÁC BÊN NGOÀI BLOCK. Bạn CHỈ được phép dùng nội dung văn bản CÓ SẴN BÊN TRONG chính Block được cung cấp.
3. Trích xuất ĐẦY ĐỦ TẤT CẢ các câu hỏi có trong TẤT CẢ các Blocks. KHÔNG ĐƯỢC BỎ SÓT.
"""

EXTRACT_USER_PROMPT_TEMPLATE = """
Dưới đây là danh sách các Block chứa câu hỏi của đề thi. Bài đọc dài (Reading Passage) ĐÃ BỊ LƯỢC BỎ để bạn tập trung vào câu hỏi.

--- BẮT ĐẦU DANH SÁCH BLOCK ---
{batched_blocks_content}
--- KẾT THÚC DANH SÁCH BLOCK ---

Hãy trích xuất TẤT CẢ các câu hỏi trong tất cả các block trên thành JSON.

QUY TẮC CẤU TRÚC JSON:
1. Bạn PHẢI trả về theo định dạng:
{{
    "questions": [
        // Danh sách toàn bộ câu hỏi của tất cả các block
    ]
}}

2. Đối với MỖI câu hỏi, BẮT BUỘC phải có:
- Trường `id`: Một ID ngẫu nhiên hoặc số thứ tự, ví dụ: "q1", "q14". BẮT BUỘC CÓ.
- Trường `block_id`: SAO CHÉP CHÍNH XÁC ID TỪ BLOCK ĐƯỢC CUNG CẤP (Ví dụ: "block_1"). NẾU BỎ QUÊN TRƯỜNG NÀY, HỆ THỐNG SẼ LỖI TOÀN BỘ. BẮT BUỘC CÓ.

3. Đối với trường `type`, BẠN CHỈ ĐƯỢC PHÉP CHỌN 1 TRONG CÁC GIÁ TRỊ SAU:
- "multiple_choice" (Trắc nghiệm thường)
- "fill_in_the_blank" (Điền khuyết, câu trả lời ngắn)
- "true_false_not_given" (True/False/Not Given, Yes/No/Not Given)
- "matching_headings" (Nối tiêu đề)
- "matching_features" (Nối đặc điểm)
- "sentence_completion" (Hoàn thành câu)
- "summary_completion" (Hoàn thành đoạn tóm tắt)
- "table_completion" (Hoàn thành bảng)
- "diagram_label_completion" (Điền nhãn biểu đồ, lưu đồ)
- "multiple_choice_ielts" (Trắc nghiệm IELTS nhiều đáp án)
TUYỆT ĐỐI KHÔNG dùng các type khác như 'short_answer', 'flow_chart_completion', v.v. Nếu gặp 'short_answer', dùng 'fill_in_the_blank'. Nếu gặp 'flow_chart_completion', dùng 'diagram_label_completion' hoặc 'summary_completion'.

4. Đối với dạng bài ĐIỀN KHUYẾT (Table/Summary/Sentence/Diagram Completion):
- NẾU GỘP NHIỀU CÂU HỎI THÀNH 1 (Ví dụ: Từ câu 1 đến câu 5 thuộc cùng 1 bảng): BẮT BUỘC phải tạo ra ĐÚNG 5 chỗ trống `[blank_1]`, `[blank_2]`, `[blank_3]`, `[blank_4]`, `[blank_5]` bên trong `question_text` tương ứng với số lượng đáp án cần điền.
- Nếu không gộp, hãy tách thành từng đối tượng câu hỏi riêng biệt, mỗi câu chứa đúng 1 chỗ trống `[blank_1]`.
- COPY CHÍNH XÁC TỪNG CHỮ CÓ TRONG BLOCK GỐC. TUYỆT ĐỐI KHÔNG TỰ SÁNG TẠO/THÊM BỚT TỪ.

5. Đối với MCQ, True/False/Not Given, Matching:
- NGHIÊM CẤM gộp các câu hỏi độc lập lại thành dạng điền khuyết.
- Kể cả khi chúng nằm trong cụm "Questions 1-5", BẮT BUỘC phải tách rời chúng ra thành 5 object câu hỏi riêng biệt trong mảng `questions` để UI hiển thị dạng khoanh trắc nghiệm. Không dùng thẻ `[blank]`.

6. Hình ảnh / Biểu đồ (Diagram Label Completion):
- Nếu Block Text có nhắc đến một hình ảnh (hoặc nếu bạn được truyền kèm context THÔNG TIN HÌNH ẢNH khớp với nội dung câu), hãy sử dụng `type`: "diagram_label_completion" và CHẮC CHẮN chèn URL của hình ảnh đó vào trường `image_url`.
"""

def get_extraction_prompt(batched_blocks_content: str) -> str:
    """
    Chuẩn bị prompt chứa danh sách các blocks.
    """
    return EXTRACT_USER_PROMPT_TEMPLATE.format(
        batched_blocks_content=batched_blocks_content.strip()
    )