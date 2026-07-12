import logging
from typing import Dict, List, Any, Union

logger = logging.getLogger(__name__)

def _normalize_text(text: Any) -> str:
    """
    Chuẩn hóa văn bản trước khi so sánh để tránh sai sót do dấu cách hoặc in hoa/thường.
    Ví dụ: " A " -> "a", "Đáp án B" -> "đáp án b"
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        return str(text).strip().lower()
    return text.strip().lower()

def _grade_exact_match(student_answer: Any, correct_answer: Any) -> bool:
    """
    So sánh đáp án học sinh với đáp án đúng (dùng cho Trắc nghiệm).
    """
    if not student_answer or not correct_answer:
        return False
    
    # Xử lý trường hợp đáp án là mảng (nhiều lựa chọn đúng) - Multiple Response
    if isinstance(correct_answer, list) and isinstance(student_answer, list):
        # Sắp xếp và so sánh 2 mảng
        student_sorted = sorted([_normalize_text(a) for a in student_answer])
        correct_sorted = sorted([_normalize_text(a) for a in correct_answer])
        return student_sorted == correct_sorted

    # Xử lý chuẩn trắc nghiệm 1 lựa chọn
    return _normalize_text(student_answer) == _normalize_text(correct_answer)

def calculate_exam_score(
    student_answers: Dict[str, Any], 
    exam_questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Hàm chính để chấm điểm bài thi.
    
    Args:
        student_answers: Dict map question_id với đáp án học sinh chọn.
                         Ví dụ: {"q1": "A", "q2": "C", "q3": "Bức tranh rất đẹp"}
        exam_questions: Danh sách câu hỏi lấy từ DB, chứa đáp án đúng và trọng số điểm.
                         Ví dụ: [{"id": "q1", "type": "multiple_choice", "correct_answer": "A", "score_weight": 1.0}, ...]
                         
    Returns:
        Dict chứa tổng kết điểm số và chi tiết chấm từng câu (để lưu vào bảng Submission).
    """
    total_score_raw = 0.0
    max_possible_score_raw = 0.0
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0
    
    # Cờ đánh dấu bài thi có câu tự luận, cần trigger Celery task (ai_grading) sau bước này
    needs_ai_grading = False 

    details = []

    for question in exam_questions:
        q_id = str(question.get("id"))
        q_type = question.get("type", "multiple_choice")
        weight = float(question.get("score_weight", 1.0))
        correct_answer = question.get("correct_answer")
        
        # Lấy đáp án của học sinh
        student_ans = student_answers.get(q_id)

        # Template cho kết quả chấm 1 câu
        detail = {
            "question_id": q_id,
            "type": q_type,
            "student_answer": student_ans,
            "correct_answer": correct_answer, # Có thể ẩn đi nếu chưa muốn cho HS xem đáp án
            "score_weight": weight,
            "is_correct": False,
            "status": "graded", # graded | pending_ai
            "score_earned": 0.0
        }

        # Nếu là câu tự luận -> Không chấm tự động, đẩy vào trạng thái chờ AI
        if q_type == "essay" or q_type == "writing":
            detail["status"] = "pending_ai"
            needs_ai_grading = True
            details.append(detail)
            continue

        # Các câu hỏi tự động chấm (Multiple choice, Fill in the blanks...)
        max_possible_score_raw += weight

        if student_ans is None or student_ans == "":
            unanswered_count += 1
            detail["is_correct"] = False
            detail["student_answer"] = None
        else:
            is_correct = _grade_exact_match(student_ans, correct_answer)
            if is_correct:
                correct_count += 1
                total_score_raw += weight
                detail["is_correct"] = True
                detail["score_earned"] = weight
            else:
                incorrect_count += 1
                detail["is_correct"] = False
        
        details.append(detail)

    # Tính điểm quy đổi ra thang 10 (Thường dùng ở VN)
    score_scale_10 = 0.0
    if max_possible_score_raw > 0:
        score_scale_10 = round((total_score_raw / max_possible_score_raw) * 10, 2)

    return {
        "summary": {
            "total_score_raw": round(total_score_raw, 2),
            "max_possible_score_raw": round(max_possible_score_raw, 2),
            "score_scale_10": score_scale_10,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "unanswered_count": unanswered_count,
            "needs_ai_grading": needs_ai_grading,
            "is_fully_graded": not needs_ai_grading # True nếu đề 100% trắc nghiệm
        },
        "details": details
    }