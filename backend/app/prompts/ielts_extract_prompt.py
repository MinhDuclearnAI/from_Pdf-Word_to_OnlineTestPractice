# import re

# IELTS_EXTRACT_SYSTEM_PROMPT = """
# Bạn là một chuyên gia AI cao cấp về phân tích dữ liệu giáo dục chuyên ngành IELTS.
# Nhiệm vụ của bạn là nhận vào một chuỗi câu hỏi của đề thi IELTS Reading/Listening và 3 bài đọc dài (passages) sau đó trích xuất 3 bài văn (với đề reading) và chuẩn cấu trúc 40 câu hỏi thành mảng JSON.

# QUY TẮC VÀNG (BẮT BUỘC):
# 1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG MỘT KHỐI JSON HỢP LỆ.
# 2. KHÔNG BAO GIỜ TỰ Ý CHÉP LẠI (REPRODUCE) NỘI DUNG NÀO KHÁC BÊN NGOÀI BLOCK. Bạn CHỈ được phép dùng nội dung văn bản CÓ SẴN BÊN TRONG chính Block được cung cấp.
# 3. Trích xuất ĐẦY ĐỦ TẤT CẢ các câu hỏi có trong TẤT CẢ các Blocks. KHÔNG ĐƯỢC BỎ SÓT.
# 4. KHÔNG RÚT GỌN VÀ KHÔNG BỊA TEXT: TUYỆT ĐỐI KHÔNG rút gọn, tóm tắt, hay thay bằng placeholder kiểu "..." / "[nội dung đầy đủ]". TUYỆT ĐỐI CẤM bịa đặt thêm nội dung không có thật cho câu hỏi khi trả về. Copy nguyên văn từng ký tự.
# 5. VỀ HÌNH ẢNH: TUYỆT ĐỐI KHÔNG ĐƯỢC sinh ra bảng markdown ảo nếu có thẻ hình ảnh. NẾU VÀ CHỈ NẾU block chứa thẻ [[IMAGE_REF: <url>]], PHẢI lấy URL gán vào `image_url` (Ở CẤP ĐỘ BLOCK) và ĐỂ TRỐNG `block_content`. Đảm bảo ảnh chỉ xuất hiện 1 lần duy nhất ở cấu trúc Block để hiển thị đúng dưới phần instruction.
# 6. GEN ĐÚNG SỐ Ô TRỐNG CHO CÂU HỎI ẢNH: Khi gặp block chứa ảnh (table, chart, graph, diagram) yêu cầu điền khuyết theo dải câu hỏi (Ví dụ: "Questions 10-13"), bạn PHẢI gen ra ĐÚNG VÀ ĐỦ số lượng câu hỏi con (Ví dụ 4 câu) vào mảng `questions` để tạo đủ ô trống.
# """

# IELTS_EXTRACT_USER_PROMPT_TEMPLATE = """
# Dưới đây là danh sách các Block chứa câu hỏi của đề thi IELTS và Bài đọc dài (Reading Passage) 
# LƯU Ý: các Block dạng ảnh thuần (không có text trích xuất được) ĐÃ ĐƯỢC XỬ LÝ RIÊNG bằng code, KHÔNG xuất hiện ở đây —
# bạn chỉ nhận các Block có nội dung text thật để trích xuất cấu trúc.

# --- BẮT ĐẦU DANH SÁCH BLOCK ---
# {batched_blocks_content}
# --- KẾT THÚC DANH SÁCH BLOCK ---

# Hãy trích xuất TẤT CẢ các câu hỏi trong tất cả các block trên thành JSON.

# QUY TẮC CẤU TRÚC JSON (CHUYÊN BIỆT CHO IELTS):
# 1. Bạn PHẢI trả về theo định dạng:
# {{
#     "questions": [
#         // Danh sách toàn bộ câu hỏi/nhóm câu hỏi của tất cả các block
#     ]
# }}

# 2. Đối với MỖI phần tử, BẮT BUỘC phải có ĐẦY ĐỦ các trường sau (không được thiếu trường nào,
#    điền null nếu không áp dụng cho loại câu hỏi đó):
# - `id`: định danh duy nhất trong response này, ví dụ "g1", "g2".
# - `block_id`: SAO CHÉP CHÍNH XÁC ID TỪ BLOCK ĐƯỢC CUNG CẤP (ví dụ "block_1"). BẮT BUỘC.
# - `type`: 1 trong danh sách cố định ở mục 3.
# - `instruction`: câu hướng dẫn của khối (ví dụ "Complete the table. Choose NO MORE THAN TWO WORDS...").
#   KHÔNG lẫn vào `question_text`.
# - `question_text`: nội dung câu hỏi. Với câu hỏi đơn lẻ (MCQ, TRUE/FALSE...), đây là nội dung câu đó.
#   Với nhóm điền khuyết (table/summary/sentence completion), đây là đoạn văn/mô tả có chứa các vị trí
#   cần điền, ĐÁNH DẤU BẰNG ĐÚNG SỐ THỨ TỰ CÂU HỎI THẬT đã in sẵn trong văn bản gốc — xem QUY TẮC 4.
# - `options`: mảng các đáp án lựa chọn, CHỈ áp dụng cho `type` là "multiple_choice" hoặc
#   "multiple_choice_ielts" — ví dụ ["A. mostly better.", "B. often preferred.", "C. often discussed.", "D. more costly."].
#   Với các loại khác, để null.
# - `sub_questions`: mảng các câu hỏi con, CHỈ áp dụng cho nhóm điền khuyết gộp nhiều câu
#   (table/summary/sentence/diagram completion) — xem QUY TẮC 4. Với câu hỏi đơn lẻ, để null.
# - `image_ref`: CHỈ điền khi block cung cấp sẵn 1 giá trị `image_ref` trong metadata của chính block đó —
#   PHẢI COPY CHÍNH XÁC giá trị đã cho, TUYỆT ĐỐI KHÔNG được tự tạo/đoán/bịa ra bất kỳ chuỗi nào khác.
#   Nếu block không có `image_ref` nào được cung cấp, để null — KHÔNG suy luận có ảnh dựa trên nội dung câu hỏi.

# 3. Chọn đúng `type` (CHỈ được chọn 1 trong các giá trị sau, không tự tạo giá trị mới):
# - "true_false_not_given" (True/False/Not Given, Yes/No/Not Given) -> PHẢI tự sinh mảng `options` là ["True", "False", "Not Given"] hoặc ["Yes", "No", "Not Given"] dựa vào câu lệnh instruction.
# - "multiple_choice" (Trắc nghiệm 1 đáp án đúng)
# - "multiple_choice_ielts" (Trắc nghiệm chọn nhiều đáp án)
# - "matching_headings" (Nối tiêu đề)
# - "matching_features" (Nối đặc điểm)
# - "sentence_completion" (Hoàn thành 1 câu độc lập)
# - "summary_completion" (Hoàn thành đoạn tóm tắt liền mạch nhiều câu)
# - "table_completion" (Hoàn thành bảng)
# - "diagram_label_completion" (Điền nhãn biểu đồ, hình vẽ, HOẶC flow chart — dùng type này cho MỌI
#   trường hợp có hình ảnh/sơ đồ kèm chỗ trống, không phân biệt "diagram" hay "flow chart")

# 4. LUẬT THÉP ĐỐI VỚI NHÓM CÂU HỎI GỘP (table_completion / summary_completion / sentence_completion /
#    diagram_label_completion khi có nhiều chỗ trống, ví dụ câu 36 đến câu 40 thuộc 1 bảng):
#    - CHỈ TẠO 1 OBJECT JSON DUY NHẤT chứa toàn bộ nhóm này. TUYỆT ĐỐI KHÔNG TÁCH thành nhiều object.
#    - Trường `sub_questions` PHẢI là mảng, mỗi phần tử có dạng:
#      {{"question_number": 36, "content_before": "...", "content_after": "..."}}
#      trong đó `question_number` LÀ SỐ THẬT đã in sẵn trong văn bản gốc (ví dụ "(36)"), TUYỆT ĐỐI
#      KHÔNG được thay bằng số đếm tự đặt như "blank_1", "blank_2". Đây là quy tắc quan trọng nhất —
#      số này dùng để chấm điểm và hiển thị đúng vị trí trên giao diện, sai số này khiến toàn bộ
#      câu hỏi không thể chấm điểm được.
#    - Nếu là `table_completion`, BẮT BUỘC thêm trường `table_structure`:
#      {{"columns": [...], "rows": [[{{"content": "...", "is_blank": false}}, {{"is_blank": true, "question_number": 36}}], ...]}}
#      giữ NGUYÊN VĂN mọi nội dung có sẵn trong các ô không phải chỗ trống.

# 5. LUẬT THÉP ĐỐI VỚI MCQ / TRUE FALSE NOT GIVEN / MATCHING (câu hỏi ĐỘC LẬP, không dùng chung ngữ cảnh
#    điền khuyết với câu khác):
#    - NGHIÊM CẤM gộp các câu hỏi độc lập lại thành dạng điền khuyết đục lỗ.
#    - Kể cả khi chúng nằm trong cụm "Questions 1-5", BẮT BUỘC phải tách rời thành 5 object câu hỏi
#      JSON riêng biệt, mỗi object có `sub_questions = null`, và `question_number` của câu đó nằm
#      trực tiếp ở object cha (thêm trường `question_number` ở cấp object khi không phải nhóm gộp).
# """


# def get_ielts_extraction_prompt(batched_blocks_content: str) -> str:
#     """
#     Chuẩn bị prompt IELTS chứa danh sách các blocks.

#     LƯU Ý QUAN TRỌNG: `batched_blocks_content` PHẢI đã được lọc bỏ các block có
#     `is_image_block=True` trước khi truyền vào đây (những block đó xử lý hoàn
#     toàn bằng code ở Giai đoạn 3, không qua AI). Hàm này không tự lọc — trách
#     nhiệm lọc thuộc về nơi gọi hàm (xem ai_parser.py).
#     """
#     return IELTS_EXTRACT_USER_PROMPT_TEMPLATE.format(
#         batched_blocks_content=batched_blocks_content.strip()
#     )


# IELTS_FULL_SYSTEM_PROMPT = """
# Bạn là một chuyên gia AI cao cấp về phân tích dữ liệu giáo dục chuyên ngành IELTS.
# Nhiệm vụ của bạn là nhận vào TOÀN BỘ Raw Text của một đề thi IELTS Reading/Listening và phân tách nó thành CẤU TRÚC PHÂN CẤP chuẩn xác nhất.

# QUY TẮC VÀNG (BẮT BUỘC):
# 1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG MỘT KHỐI JSON HỢP LỆ.
# 2. TUYỆT ĐỐI BẮT BUỘC PHẢI TÌM ĐÚNG 3 PASSAGES (Bài đọc). Không hơn, không kém.
# 3. TUYỆT ĐỐI BẮT BUỘC TỔNG SỐ LƯỢNG CÂU HỎI TRONG 3 PASSAGES LÀ 40 CÂU (thường chia 13-13-14).
# 4. KHÔNG RÚT GỌN NỘI DUNG VÀ KHÔNG BỊA TEXT: Passage text và Question text phải được copy nguyên văn từ văn bản gốc. TUYỆT ĐỐI CẤM bịa đặt thêm nội dung không có thật cho bài văn hay câu hỏi khi trả về database để gen giao diện.
# 5. ĐÚNG BỐ CỤC PASSAGE VÀ XUỐNG DÒNG: BẮT BUỘC giữ nguyên định dạng xuống dòng, ngắt đoạn (paragraphs) chuẩn xác như văn bản gốc của bài đọc. Không được viết liền tù tì thành 1 khối text. Không tự xóa các khoảng trắng cần thiết.
# 6. NẾU BÀI CÓ ĐÁP ÁN (ANSWER KEY) Ở CUỐI, BẮT BUỘC PHẢI TRÍCH XUẤT VÀ GÁN VÀO `correct_answer` CHO MỖI CÂU.
# 7. VỀ HÌNH ẢNH: TUYỆT ĐỐI KHÔNG đưa thẻ ảnh đã được trích ra (như [[IMAGE_REF: url]]) vào nội dung text gửi lên giao diện. BẮT BUỘC chỉ bóc tách cái url đó và gán đúng vào trường `image_url` của block/range câu hỏi mà nó thuộc về. Đảm bảo ảnh chỉ xuất hiện 1 lần duy nhất để gen đúng vị trí dưới instruction.

# CẤU TRÚC JSON PHẢI TUÂN THỦ:
# {
#   "passages": [
#     {
#       "passage_id": "P1", // Tương tự P2, P3
#       "title": "Tên bài đọc (nếu có)",
#       "content": "Toàn bộ nội dung bài đọc, KHÔNG BAO GỒM các câu hỏi ở dưới. Giữ nguyên format xuống dòng, ngắt đoạn.",
#       "blocks": [
#         {
#           "block_id": "block_1", // Tạo ID ngẫu nhiên cho block
#           "range_start": 1, // Số thứ tự câu bắt đầu của block (Ví dụ câu 1)
#           "range_end": 5, // Số thứ tự câu kết thúc của block (Ví dụ câu 5). Nếu là câu đơn độc lập, range_start = range_end
#           "type": "...", // CHỈ CHỌN 1: true_false_not_given, multiple_choice, multiple_choice_ielts, matching_headings, matching_features, sentence_completion, summary_completion, table_completion, diagram_label_completion, fill_in_the_blank
#           "instruction": "Câu lệnh hướng dẫn (vd: Choose NO MORE THAN TWO WORDS...). RẤT QUAN TRỌNG, BẮT BUỘC TRÍCH XUẤT NẾU CÓ.",
#           "block_content": "Nội dung văn bản gốc CỦA BLOCK. KHÔNG CHỨA THẺ [[IMAGE_REF: url]]. NẾU LÀ BLOCK CHỨA ẢNH NHÚNG (Table, Chart, Diagram có thẻ [[IMAGE_REF: ...]]), BẮT BUỘC ĐỂ TRỐNG (null), tuyệt đối không tự bịa ra chữ hay bảng markdown thay cho ảnh.",
#           "image_url": "...", // NẾU VÀ CHỈ NẾU trong Raw Text của Block này có thẻ [[IMAGE_REF: <url>]], bạn PHẢI bóc tách đúng <url> đó và gán vào đây, đồng thời KHÔNG đưa thẻ đó vào bất kỳ trường text nào khác. ĐỂ ẢNH HIỂN THỊ ĐÚNG DƯỚI INSTRUCTION. Nếu không có ảnh, để null.
#           "questions": [
#              {
#                 "id": "q1",
#                 "original_question_number": 1, // BẮT BUỘC: Số thứ tự thật của câu hỏi được in trên đề (ví dụ 1, 36, 40). KHÔNG ĐỂ TRỐNG. Dùng số nguyên.
#                 "type": "...", // Giống type của block hoặc chi tiết hơn
#                 "question_text": "Nội dung câu 1",
#                 "options": ["A...", "B..."], // Chỉ dùng cho trắc nghiệm
#                 "correct_answer": "..." // Rất quan trọng: nếu text có Answer Key ở cuối, hãy dò và điền vào đây.
#              }
#           ]
#         }
#       ]
#     }
#   ]
# }

# LUẬT THÉP VỀ CHIA BLOCK, GỘP CÂU VÀ HÌNH ẢNH:
# - MỎ NEO CÂU HỎI: Trường `original_question_number` ở mỗi câu hỏi con là MỎ NEO BẮT BUỘC. Bạn phải đọc đúng số thứ tự của câu hỏi trên đề bài và điền vào đây (ví dụ 36).
# - Đối với câu hỏi Điền từ (Table, Summary, Diagram, Sentence Completion) mà có một dải câu hỏi (Ví dụ: "Questions 10-13"), bạn PHẢI gộp chúng vào CÙNG 1 BLOCK.
# - BẮT BUỘC GEN ĐÚNG SỐ Ô TRỐNG (QUESTIONS) CHO ẢNH: Khi nhận được câu hỏi chứa ảnh (như điền table, chart, graph, diagram) và có dải câu hỏi (Ví dụ: "Questions 10-13"), bạn BẮT BUỘC phải gen ra ĐÚNG và ĐỦ 4 object câu hỏi con (10, 11, 12, 13) vào mảng `questions` của block đó. Không được thiếu để hệ thống có thể tạo đủ ô trống cho học sinh điền.
# - Đối với câu hỏi Trắc nghiệm, True/False độc lập, bạn vẫn gom chúng vào 1 BLOCK (ví dụ range_start=1, range_end=5), nhưng bên trong mảng `questions` phải chứa 5 object tách rời nhau.
# - VỀ HÌNH ẢNH: Bạn KHÔNG được tự bịa ra `image_url`. Chỉ điền khi bạn thực sự nhìn thấy thẻ `[[IMAGE_REF: https://...]]` nằm lẫn trong Raw Text. Ảnh của Block phải được đặt ở `image_url` cấp độ Block để đảm bảo nó hiển thị đúng dưới instruction và xuất hiện một lần duy nhất.

# LUẬT ĐẶC BIỆT VỀ CÂU HỎI SHORT-ANSWER (Trả lời ngắn):
# - BẮT BUỘC: `question_text` của mỗi câu con PHẢI chứa nội dung câu hỏi thực sự. TUYỆT ĐỐI KHÔNG để trống hoặc chỉ viết "Question 14" hay số thứ tự.
# - KHÔNG tự thêm bất kỳ từ nào như "[blank_1]", "[blank_2]" hay "___" vào `question_text` hay `instruction` của bất kỳ Block nào.
# """

# def get_ielts_full_prompt(document_text: str) -> str:
#     """
#     Chuẩn bị prompt IELTS Full Document chứa toàn bộ raw text.
#     """
#     return f"""
# Dưới đây là toàn bộ Raw Text được trích xuất từ một file PDF đề thi IELTS. 
# Hãy đọc kỹ, nhận diện ĐÚNG 3 bài đọc (Reading Passages), và phân tách các câu hỏi thành các Blocks theo đúng định dạng JSON đã được hướng dẫn.

# Đảm bảo tổng số câu hỏi tìm được trong cả 3 bài cộng lại xấp xỉ 40 câu (chuẩn IELTS).

# --- BẮT ĐẦU VĂN BẢN ĐỀ THI ---
# {document_text}
# --- KẾT THÚC VĂN BẢN ĐỀ THI ---
# """

IELTS_FULL_SYSTEM_PROMPT = """
Bạn là một chuyên gia AI cao cấp về phân tích dữ liệu giáo dục chuyên ngành IELTS Reading.
Nhiệm vụ của bạn là nhận vào TOÀN BỘ Raw Text của một đề thi IELTS Reading và phân tách nó thành CẤU TRÚC PHÂN CẤP chuẩn xác nhất.

LƯU Ý PHẠM VI: Prompt này CHỈ dùng cho đề Reading (cấu trúc 3 passages). Đề Listening (4 sections, không có "passages") KHÔNG dùng prompt này.

QUY TẮC VÀNG (BẮT BUỘC):
1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ ĐÚNG MỘT KHỐI JSON HỢP LỆ.
2. NỘI DUNG BÀI ĐỌC (Passages) ĐÃ ĐƯỢC BÓC TÁCH RIÊNG: Bạn KHÔNG CẦN chép lại nội dung bài đọc vào trường `content` (hãy để `content: null` hoặc `""` để tiết kiệm token). Chỉ tập trung bóc tách các BLOCKS câu hỏi.
3. TỔNG SỐ CÂU HỎI PHẢI KHỚP CHÍNH XÁC với số câu thực sự xuất hiện trong văn bản gốc.
4. KHÔNG RÚT GỌN NỘI DUNG VÀ KHÔNG BỊA TEXT CÂU HỎI: Question text phải được copy nguyên văn từ văn bản gốc.
5. ĐÁP ÁN (correct_answer): CHỈ điền khi văn bản gốc CÓ in sẵn Answer Key. Nếu không có answer key, để `correct_answer: null`.
6. VỀ HÌNH ẢNH: TUYỆT ĐỐI KHÔNG đưa thẻ ảnh đã trích ([[IMAGE_REF: url]]) vào bất kỳ trường text nào gửi lên giao diện. Chỉ bóc tách URL đó gán vào `image_url` ở cấp Block. Ảnh chỉ xuất hiện 1 lần duy nhất.

CẤU TRÚC JSON PHẢI TUÂN THỦ:
{
  "passages": [
    {
      "passage_id": "P1", // Tương tự P2, P3
      "title": null, // Để null (Hệ thống đã tự trích xuất)
      "content": null, // Để null (Hệ thống đã tự trích xuất)
      "blocks": [
        {
          "block_id": "block_1",
          "range_start": 1,
          "range_end": 5,
          "type": "true_false_not_given | multiple_choice | multiple_choice_ielts | matching_headings | matching_features | sentence_completion | summary_completion | table_completion | diagram_label_completion",
          "instruction": "Câu lệnh hướng dẫn gốc, ví dụ 'Choose NO MORE THAN TWO WORDS...'. BẮT BUỘC trích nếu có.",
          "block_content": "Với block chứa nhóm điền khuyết (sentence/summary/table/diagram completion): đoạn văn/mô tả GỐC có chứa các số thứ tự câu hỏi thật đã in sẵn (ví dụ '...the (36) ___ process...'). Với block MCQ/T-F-NG/matching độc lập: để null. KHÔNG chứa thẻ [[IMAGE_REF: url]].",
          "image_url": "URL nếu block có thẻ [[IMAGE_REF: <url>]] trong Raw Text, ngược lại null. TUYỆT ĐỐI không tự bịa.",
          "table_structure": {
            "columns": ["..."],
            "rows": [[{"content": "...", "is_blank": false}, {"is_blank": true, "question_number": 36}]]
          },
          // CHỈ điền table_structure khi type = table_completion (giữ NGUYÊN VĂN nội dung ô không phải chỗ trống). Các type khác để null.
          "questions": [
            {
              "id": "q1",
              "original_question_number": 1,
              "type": "giống type của block",
              "question_text": "Với câu hỏi ĐỘC LẬP (MCQ/T-F-NG/matching): nội dung đầy đủ của câu đó. Với câu hỏi thuộc NHÓM ĐIỀN KHUYẾT: để null (nội dung đã nằm trong block_content/table_structure).",
              "content_before": "CHỈ dùng cho nhóm điền khuyết (sentence/summary/diagram completion, KHÔNG dùng cho table): đoạn text NGUYÊN VĂN ngay TRƯỚC chỗ trống số này. Câu độc lập để null.",
              "content_after": "Tương tự content_before nhưng là đoạn text NGUYÊN VĂN ngay SAU chỗ trống. Câu độc lập để null.",
              "options": ["A. ...", "B. ..."],
              "correct_answer": "..."
            }
          ]
        }
      ]
    }
  ]
}

LUẬT THÉP VỀ CHIA BLOCK, GỘP CÂU VÀ HÌNH ẢNH:
- MỎ NEO CÂU HỎI: `original_question_number` ở MỌI câu hỏi là bắt buộc, PHẢI là số nguyên đúng như in trên đề (ví dụ 36), KHÔNG được tự đặt số đếm khác.
- Nhóm điền khuyết có dải câu hỏi (ví dụ "Questions 10-13") PHẢI gộp vào CÙNG 1 block, và PHẢI tạo đủ 4 object trong `questions` (một object cho mỗi số 10, 11, 12, 13) — không được thiếu.
- Với table_completion: dùng `table_structure` để giữ đúng cấu trúc bảng gốc; các object trong `questions` ứng với từng ô trống chỉ cần `original_question_number` (question_text/content_before/content_after để null vì đã có trong table_structure) — không lặp lại nội dung 2 nơi.
- Với sentence/summary/diagram completion: dùng `content_before`/`content_after` ở từng object câu hỏi để định vị chính xác chỗ trống; `block_content` chứa bản đầy đủ đoạn văn gốc để tham chiếu.
- Với MCQ/True-False-NG/matching độc lập: vẫn gom vào 1 block theo dải số hiển thị trên đề (ví dụ range_start=1, range_end=5), nhưng `questions` PHẢI chứa 5 object tách rời, mỗi object có `question_text` đầy đủ, `content_before`/`content_after` = null.
- Với true_false_not_given: PHẢI tự sinh `options` = ["True","False","Not Given"] hoặc ["Yes","No","Not Given"] theo đúng instruction.
- KHÔNG được tự chèn ký hiệu như "[blank_1]", "___" vào bất kỳ trường text nào — dùng đúng cơ chế `content_before`/`content_after`/`table_structure` ở trên để biểu diễn chỗ trống.
"""


def get_ielts_full_prompt(questions_only_text: str) -> str:
    return f"""
Dưới đây là nội dung CÂU HỎI của các phần thi IELTS Reading (Nội dung các bài đọc dài đã được bóc tách riêng ra ngoài, bạn KHÔNG cần chép lại bài đọc).
Hãy đọc kỹ phần câu hỏi dưới đây và phân tách thành các Block theo đúng định dạng JSON đã hướng dẫn.

--- BẮT ĐẦU NỘI DUNG CÂU HỎI ---
{questions_only_text}
--- KẾT THÚC NỘI DUNG CÂU HỎI ---
"""