import re

IELTS_EXTRACT_SYSTEM_PROMPT = """
Bạn là một chuyên gia AI cao cấp về phân tích dữ liệu giáo dục chuyên ngành IELTS.
Nhiệm vụ của bạn là nhận vào một tập hợp các "Blocks" câu hỏi của đề thi IELTS Reading/Listening và trích xuất cấu trúc câu hỏi thành mảng JSON.
Các Blocks được phân tách rõ ràng bằng các đường viền ===================.

QUY TẮC VÀNG (BẮT BUỘC):
1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG MỘT KHỐI JSON HỢP LỆ.
2. KHÔNG BAO GIỜ TỰ Ý CHÉP LẠI (REPRODUCE) NỘI DUNG NÀO KHÁC BÊN NGOÀI BLOCK. Bạn CHỈ được phép dùng nội dung văn bản CÓ SẴN BÊN TRONG chính Block được cung cấp.
3. Trích xuất ĐẦY ĐỦ TẤT CẢ các câu hỏi có trong TẤT CẢ các Blocks. KHÔNG ĐƯỢC BỎ SÓT.
4. [MỚI] TUYỆT ĐỐI KHÔNG RÚT GỌN, TÓM TẮT, hay thay bằng placeholder kiểu "..." / "[nội dung đầy đủ]"
   cho BẤT KỲ nội dung nào bên trong block — kể cả khi bảng dài, danh sách heading nhiều mục,
   hay đoạn tóm tắt dài. Copy nguyên văn từng ký tự.
5. VỀ HÌNH ẢNH: TUYỆT ĐỐI KHÔNG ĐƯỢC sinh ra bảng markdown ảo nếu có thẻ hình ảnh. NẾU VÀ CHỈ NẾU block chứa thẻ [[IMAGE_REF: <url>]], PHẢI lấy URL gán vào `image_url` và ĐỂ TRỐNG `block_content` (không tự chuyển đổi ảnh thành bảng chữ).
"""

IELTS_EXTRACT_USER_PROMPT_TEMPLATE = """
Dưới đây là danh sách các Block chứa câu hỏi của đề thi IELTS. Bài đọc dài (Reading Passage) ĐÃ BỊ LƯỢC BỎ để bạn tập trung vào câu hỏi.
LƯU Ý: các Block dạng ảnh thuần (không có text trích xuất được) ĐÃ ĐƯỢC XỬ LÝ RIÊNG bằng code, KHÔNG xuất hiện ở đây —
bạn chỉ nhận các Block có nội dung text thật để trích xuất cấu trúc.

--- BẮT ĐẦU DANH SÁCH BLOCK ---
{batched_blocks_content}
--- KẾT THÚC DANH SÁCH BLOCK ---

Hãy trích xuất TẤT CẢ các câu hỏi trong tất cả các block trên thành JSON.

QUY TẮC CẤU TRÚC JSON (CHUYÊN BIỆT CHO IELTS):
1. Bạn PHẢI trả về theo định dạng:
{{
    "questions": [
        // Danh sách toàn bộ câu hỏi/nhóm câu hỏi của tất cả các block
    ]
}}

2. Đối với MỖI phần tử, BẮT BUỘC phải có ĐẦY ĐỦ các trường sau (không được thiếu trường nào,
   điền null nếu không áp dụng cho loại câu hỏi đó):
- `id`: định danh duy nhất trong response này, ví dụ "g1", "g2".
- `block_id`: SAO CHÉP CHÍNH XÁC ID TỪ BLOCK ĐƯỢC CUNG CẤP (ví dụ "block_1"). BẮT BUỘC.
- `type`: 1 trong danh sách cố định ở mục 3.
- `instruction`: câu hướng dẫn của khối (ví dụ "Complete the table. Choose NO MORE THAN TWO WORDS...").
  KHÔNG lẫn vào `question_text`.
- `question_text`: nội dung câu hỏi. Với câu hỏi đơn lẻ (MCQ, TRUE/FALSE...), đây là nội dung câu đó.
  Với nhóm điền khuyết (table/summary/sentence completion), đây là đoạn văn/mô tả có chứa các vị trí
  cần điền, ĐÁNH DẤU BẰNG ĐÚNG SỐ THỨ TỰ CÂU HỎI THẬT đã in sẵn trong văn bản gốc — xem QUY TẮC 4.
- `options`: mảng các đáp án lựa chọn, CHỈ áp dụng cho `type` là "multiple_choice" hoặc
  "multiple_choice_ielts" — ví dụ ["A. mostly better.", "B. often preferred.", "C. often discussed.", "D. more costly."].
  Với các loại khác, để null.
- `sub_questions`: mảng các câu hỏi con, CHỈ áp dụng cho nhóm điền khuyết gộp nhiều câu
  (table/summary/sentence/diagram completion) — xem QUY TẮC 4. Với câu hỏi đơn lẻ, để null.
- `image_ref`: CHỈ điền khi block cung cấp sẵn 1 giá trị `image_ref` trong metadata của chính block đó —
  PHẢI COPY CHÍNH XÁC giá trị đã cho, TUYỆT ĐỐI KHÔNG được tự tạo/đoán/bịa ra bất kỳ chuỗi nào khác.
  Nếu block không có `image_ref` nào được cung cấp, để null — KHÔNG suy luận có ảnh dựa trên nội dung câu hỏi.

3. Chọn đúng `type` (CHỈ được chọn 1 trong các giá trị sau, không tự tạo giá trị mới):
- "true_false_not_given" (True/False/Not Given, Yes/No/Not Given) -> PHẢI tự sinh mảng `options` là ["True", "False", "Not Given"] hoặc ["Yes", "No", "Not Given"] dựa vào câu lệnh instruction.
- "multiple_choice" (Trắc nghiệm 1 đáp án đúng)
- "multiple_choice_ielts" (Trắc nghiệm chọn nhiều đáp án)
- "matching_headings" (Nối tiêu đề)
- "matching_features" (Nối đặc điểm)
- "sentence_completion" (Hoàn thành 1 câu độc lập)
- "summary_completion" (Hoàn thành đoạn tóm tắt liền mạch nhiều câu)
- "table_completion" (Hoàn thành bảng)
- "diagram_label_completion" (Điền nhãn biểu đồ, hình vẽ, HOẶC flow chart — dùng type này cho MỌI
  trường hợp có hình ảnh/sơ đồ kèm chỗ trống, không phân biệt "diagram" hay "flow chart")

4. LUẬT THÉP ĐỐI VỚI NHÓM CÂU HỎI GỘP (table_completion / summary_completion / sentence_completion /
   diagram_label_completion khi có nhiều chỗ trống, ví dụ câu 36 đến câu 40 thuộc 1 bảng):
   - CHỈ TẠO 1 OBJECT JSON DUY NHẤT chứa toàn bộ nhóm này. TUYỆT ĐỐI KHÔNG TÁCH thành nhiều object.
   - Trường `sub_questions` PHẢI là mảng, mỗi phần tử có dạng:
     {{"question_number": 36, "content_before": "...", "content_after": "..."}}
     trong đó `question_number` LÀ SỐ THẬT đã in sẵn trong văn bản gốc (ví dụ "(36)"), TUYỆT ĐỐI
     KHÔNG được thay bằng số đếm tự đặt như "blank_1", "blank_2". Đây là quy tắc quan trọng nhất —
     số này dùng để chấm điểm và hiển thị đúng vị trí trên giao diện, sai số này khiến toàn bộ
     câu hỏi không thể chấm điểm được.
   - Nếu là `table_completion`, BẮT BUỘC thêm trường `table_structure`:
     {{"columns": [...], "rows": [[{{"content": "...", "is_blank": false}}, {{"is_blank": true, "question_number": 36}}], ...]}}
     giữ NGUYÊN VĂN mọi nội dung có sẵn trong các ô không phải chỗ trống.

5. LUẬT THÉP ĐỐI VỚI MCQ / TRUE FALSE NOT GIVEN / MATCHING (câu hỏi ĐỘC LẬP, không dùng chung ngữ cảnh
   điền khuyết với câu khác):
   - NGHIÊM CẤM gộp các câu hỏi độc lập lại thành dạng điền khuyết đục lỗ.
   - Kể cả khi chúng nằm trong cụm "Questions 1-5", BẮT BUỘC phải tách rời thành 5 object câu hỏi
     JSON riêng biệt, mỗi object có `sub_questions = null`, và `question_number` của câu đó nằm
     trực tiếp ở object cha (thêm trường `question_number` ở cấp object khi không phải nhóm gộp).
"""


def get_ielts_extraction_prompt(batched_blocks_content: str) -> str:
    """
    Chuẩn bị prompt IELTS chứa danh sách các blocks.

    LƯU Ý QUAN TRỌNG: `batched_blocks_content` PHẢI đã được lọc bỏ các block có
    `is_image_block=True` trước khi truyền vào đây (những block đó xử lý hoàn
    toàn bằng code ở Giai đoạn 3, không qua AI). Hàm này không tự lọc — trách
    nhiệm lọc thuộc về nơi gọi hàm (xem ai_parser.py).
    """
    return IELTS_EXTRACT_USER_PROMPT_TEMPLATE.format(
        batched_blocks_content=batched_blocks_content.strip()
    )


IELTS_FULL_SYSTEM_PROMPT = """
Bạn là một chuyên gia AI cao cấp về phân tích dữ liệu giáo dục chuyên ngành IELTS.
Nhiệm vụ của bạn là nhận vào TOÀN BỘ Raw Text của một đề thi IELTS Reading/Listening và phân tách nó thành CẤU TRÚC PHÂN CẤP chuẩn xác nhất.

QUY TẮC VÀNG (BẮT BUỘC):
1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG MỘT KHỐI JSON HỢP LỆ.
2. TUYỆT ĐỐI BẮT BUỘC PHẢI TÌM ĐÚNG 3 PASSAGES (Bài đọc). Không hơn, không kém.
3. TUYỆT ĐỐI BẮT BUỘC TỔNG SỐ LƯỢNG CÂU HỎI TRONG 3 PASSAGES LÀ 40 CÂU (thường chia 13-13-14).
4. KHÔNG RÚT GỌN NỘI DUNG. Passage text và Question text phải được copy nguyên văn.
5. NẾU BÀI CÓ ĐÁP ÁN (ANSWER KEY) Ở CUỐI, BẮT BUỘC PHẢI TRÍCH XUẤT VÀ GÁN VÀO `correct_answer` CHO MỖI CÂU.

CẤU TRÚC JSON PHẢI TUÂN THỦ:
{
  "passages": [
    {
      "passage_id": "P1", // Tương tự P2, P3
      "title": "Tên bài đọc (nếu có)",
      "content": "Toàn bộ nội dung bài đọc, KHÔNG BAAO GỒM các câu hỏi ở dưới.",
      "blocks": [
        {
          "block_id": "block_1", // Tạo ID ngẫu nhiên cho block
          "range_start": 1, // Số thứ tự câu bắt đầu của block (Ví dụ câu 1)
          "range_end": 5, // Số thứ tự câu kết thúc của block (Ví dụ câu 5). Nếu là câu đơn độc lập, range_start = range_end
          "type": "...", // CHỈ CHỌN 1: true_false_not_given, multiple_choice, multiple_choice_ielts, matching_headings, matching_features, sentence_completion, summary_completion, table_completion, diagram_label_completion, fill_in_the_blank
          "instruction": "Câu lệnh hướng dẫn (vd: Choose NO MORE THAN TWO WORDS..., Do the following statements agree...). RẤT QUAN TRỌNG, BẮT BUỘC TRÍCH XUẤT NẾU CÓ.",
          "block_content": "Nội dung văn bản gốc CỦA BLOCK NÀY (Ví dụ: Đoạn văn Summary bị đục lỗ). NẾU LÀ HÌNH ẢNH HOẶC BẢNG DẠNG ẢNH CÓ [[IMAGE_REF: ...]], BẮT BUỘC ĐỂ TRỐNG (null), tuyệt đối không tự bịa ra markdown table thay cho ảnh.",
          "image_url": "...", // NẾU VÀ CHỈ NẾU trong Raw Text của Block này (hoặc ngay trước nó) có thẻ [[IMAGE_REF: <url>]], bạn PHẢI trích xuất chính xác <url> đó vào đây. Nếu không có, để null.
          "questions": [
             {
                "id": "q1",
                "original_question_number": 1, // BẮT BUỘC: Số thứ tự thật của câu hỏi được in trên đề (ví dụ 1, 36, 40). KHÔNG ĐỂ TRỐNG. Dùng số nguyên.
                "type": "...", // Giống type của block hoặc chi tiết hơn
                "question_text": "Nội dung câu 1",
                "options": ["A...", "B..."], // Chỉ dùng cho trắc nghiệm
                "correct_answer": "..." // Rất quan trọng: nếu text có Answer Key ở cuối, hãy dò và điền vào đây.
             }
          ]
        }
      ]
    }
  ]
}

LUẬT THÉP VỀ CHIA BLOCK VÀ GỘP CÂU:
- MỎ NEO CÂU HỎI: Trường `original_question_number` ở mỗi câu hỏi con là MỎ NEO BẮT BUỘC. Bạn phải đọc đúng số thứ tự của câu hỏi trên đề bài và điền vào đây (ví dụ 36). Tuyệt đối không tự đẻ thêm câu hỏi nếu không có số thứ tự rõ ràng trên đề.
- Đối với câu hỏi Điền từ (Table, Summary, Diagram, Sentence Completion) mà có một dải câu hỏi (Ví dụ: "Questions 10-13"), bạn PHẢI gộp chúng vào CÙNG 1 BLOCK.
- Đối với câu hỏi Trắc nghiệm, True/False độc lập, bạn vẫn gom chúng vào 1 BLOCK (ví dụ range_start=1, range_end=5), nhưng bên trong mảng `questions` phải chứa 5 object tách rời nhau, mỗi object chứa đúng 1 câu hỏi có `original_question_number` tương ứng.
- VỀ HÌNH ẢNH: Bạn KHÔNG được tự bịa ra `image_url`. Chỉ điền khi bạn thực sự nhìn thấy thẻ `[[IMAGE_REF: https://...]]` nằm lẫn trong Raw Text.
"""

def get_ielts_full_prompt(document_text: str) -> str:
    """
    Chuẩn bị prompt IELTS Full Document chứa toàn bộ raw text.
    """
    return f"""
Dưới đây là toàn bộ Raw Text được trích xuất từ một file PDF đề thi IELTS. 
Hãy đọc kỹ, nhận diện ĐÚNG 3 bài đọc (Reading Passages), và phân tách các câu hỏi thành các Blocks theo đúng định dạng JSON đã được hướng dẫn.

Đảm bảo tổng số câu hỏi tìm được trong cả 3 bài cộng lại xấp xỉ 40 câu (chuẩn IELTS).

--- BẮT ĐẦU VĂN BẢN ĐỀ THI ---
{document_text}
--- KẾT THÚC VĂN BẢN ĐỀ THI ---
"""