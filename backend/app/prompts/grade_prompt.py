# backend/app/prompts/grading_prompt.py

# System Prompt định hình vai trò của LLM: Một giáo viên chấm thi công bằng, chi tiết và tuân thủ định dạng.
GRADING_SYSTEM_PROMPT = """
Bạn là một giáo viên chấm thi xuất sắc, khách quan và tận tâm.
Nhiệm vụ của bạn là chấm điểm câu trả lời tự luận của học sinh dựa trên câu hỏi, đáp án chuẩn (hoặc hướng dẫn chấm), và điểm tối đa của câu hỏi.

QUY TẮC TỐI QUAN TRỌNG:
1. BẠN CHỈ ĐƯỢC PHÉP TRẢ VỀ MỘT CHUỖI JSON HỢP LỆ.
2. Tuyệt đối KHÔNG giải thích, KHÔNG chào hỏi, KHÔNG sử dụng markdown format ngoài block ```json.
3. Điểm số (score_earned) phải là một số thực (float) nằm trong khoảng từ 0 đến điểm tối đa (max_score).
4. Nhận xét (feedback) cần mang tính xây dựng, chỉ ra điểm đúng, điểm sai hoặc thiếu sót của học sinh một cách ngắn gọn.
"""

# User Prompt chứa dữ liệu thực tế: Câu hỏi, Đáp án chuẩn, Bài làm của học sinh và Điểm tối đa.
GRADING_USER_PROMPT_TEMPLATE = """
Hãy chấm điểm bài làm tự luận sau đây:

--- THÔNG TIN CÂU HỎI ---
Câu hỏi: {question_text}
Đáp án chuẩn / Hướng dẫn chấm (Rubric): {model_answer}
Điểm tối đa có thể đạt được: {max_score}

--- BÀI LÀM CỦA HỌC SINH ---
{student_answer}

Dựa vào các thông tin trên, hãy chấm điểm và trả về ĐÚNG cấu trúc JSON sau:

{{
    "score_earned": "Điểm số học sinh đạt được (kiểu số thực, ví dụ: 0.5, 1.0, 2.5). Không được vượt quá max_score.",
    "feedback": "Nhận xét chi tiết: khen ngợi điểm làm tốt, chỉ ra lỗi sai hoặc ý còn thiếu so với đáp án chuẩn.",
    "is_correct": "Trả về true nếu bài làm đạt từ 50% số điểm tối đa trở lên, ngược lại trả về false."
}}
"""

def get_grading_prompt(
    question_text: str, 
    model_answer: str, 
    student_answer: str, 
    max_score: float = 1.0
) -> str:
    """
    Hàm tiện ích để tạo prompt chấm điểm cho một câu hỏi tự luận.
    
    Args:
        question_text: Nội dung câu hỏi.
        model_answer: Đáp án chuẩn hoặc barem điểm từ hệ thống.
        student_answer: Bài làm thực tế của học sinh.
        max_score: Điểm tối đa của câu hỏi này.
        
    Returns:
        Chuỗi prompt đã được điền đầy đủ thông tin để gửi cho LLM.
    """
    # Xử lý text an toàn: thay thế các giá trị null/rỗng nếu có
    safe_question = question_text.strip() if question_text else "Không có nội dung câu hỏi"
    safe_model_answer = model_answer.strip() if model_answer else "Không có hướng dẫn chấm cụ thể, hãy chấm dựa trên kiến thức phổ quát."
    safe_student_answer = student_answer.strip() if student_answer else "[Học sinh bỏ trống]"
    
    # Format template
    return GRADING_USER_PROMPT_TEMPLATE.format(
        question_text=safe_question,
        model_answer=safe_model_answer,
        student_answer=safe_student_answer,
        max_score=max_score
    )