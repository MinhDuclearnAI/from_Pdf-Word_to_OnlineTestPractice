from typing import Any, Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

# ==========================================
# Khai báo các loại Component hỗ trợ UI/UX
# ==========================================
ComponentType = Literal[
    "multiple_choice", 
    "math_equation", 
    "reading_passage",
    "fill_in_the_blank",
    "essay",
    "true_false_not_given",
    "matching_headings",
    "matching_features",
    "sentence_completion",
    "summary_completion",
    "table_completion",
    "diagram_label_completion",
    "multiple_choice_ielts"
]

TYPE_ALIASES = {
    "multiple choice": "multiple_choice",
    "multiple-choice": "multiple_choice",
    "mcq": "multiple_choice",
    "fill blank": "fill_in_the_blank",
    "fill-in-the-blank": "fill_in_the_blank",
    "writing": "essay",
    "latex_formula": "math_equation",
    # IELTS specific aliases
    "tfng": "true_false_not_given",
    "true/false/not given": "true_false_not_given",
    "yes/no/not given": "true_false_not_given",
    "ynng": "true_false_not_given",
    "matching headings": "matching_headings",
    "matching features": "matching_features",
    "sentence completion": "sentence_completion",
    "summary completion": "summary_completion",
    "table completion": "table_completion",
    "diagram label completion": "diagram_label_completion",
    "multiple choice ielts": "multiple_choice_ielts",
    "flowchart_completion": "diagram_label_completion",
    "flow_chart_completion": "diagram_label_completion",
    "flowchart completion": "diagram_label_completion",
    "flow chart completion": "diagram_label_completion",
    "diagram_completion": "diagram_label_completion",
    "diagram completion": "diagram_label_completion",
    "flowchart": "diagram_label_completion",
    "flow_chart": "diagram_label_completion",
    "diagram": "diagram_label_completion",
    "summary": "summary_completion",
    "summary_completion": "summary_completion",
    "table": "table_completion",
    "note_completion": "summary_completion",
    "note completion": "summary_completion",
    "form_completion": "table_completion",
    "form completion": "table_completion",
    "short_answer": "sentence_completion",
    "short_answer_questions": "sentence_completion",
    "short_answer_question": "sentence_completion",
    "short_answers": "sentence_completion",
    "short answer": "sentence_completion",
    "short answers": "sentence_completion",
    "short-answer": "sentence_completion",
    "short-answers": "sentence_completion",
    "short answer question": "sentence_completion",
    "short answer questions": "sentence_completion",
    "short-answer question": "sentence_completion",
    "short-answer questions": "sentence_completion",
    "question_answer": "sentence_completion",
    "question_answers": "sentence_completion",
    "question-answer": "sentence_completion",
    "question-answers": "sentence_completion",
    "question_answering": "sentence_completion",
    "question answering": "sentence_completion",
    "question-answering": "sentence_completion",
    "qa": "sentence_completion",
    "q&a": "sentence_completion",
}


# ==========================================
# 1. Schemas cho Output của AI (Parsing Pipeline)
# ==========================================

class QuestionSchema(BaseModel):
    """
    Schema siêu nghiêm ngặt dùng để validate kết quả JSON trả về từ LLM (Pass 2).
    Khớp tuyệt đối với các key được yêu cầu trong extract_prompt.py.
    """
    id: str = Field(
        ..., 
        description="ID tạm thời do AI tạo ra (ví dụ: 'q1', 'q2')"
    )
    type: ComponentType = Field(
        ..., 
        description="Phân loại UI Component để Frontend gọi chính xác component render"
    )
    question_text: Optional[str] = Field(
        default="", 
        description="Nội dung đầy đủ của câu hỏi (có thể rỗng nếu là câu hỏi con trong bảng)"
    )
    options: List[str] = Field(
        default_factory=list, 
        description="Danh sách đáp án (chỉ dành cho câu trắc nghiệm, nếu không có để rỗng [])"
    )
    correct_answer: Optional[str] = Field(
        None, 
        description="Đáp án đúng được trích xuất từ đề/đáp án (nếu có)"
    )
    score_weight: float = Field(
        1.0, 
        description="Điểm mặc định cho câu hỏi này"
    )
    passage_ref: Optional[str] = Field(
        None, 
        description="Nội dung đoạn văn bài đọc (chỉ dành cho type 'reading_passage')"
    )
    block_id: Optional[str] = Field(
        None,
        description="ID của block cha chứa câu hỏi này (nếu có)"
    )
    is_block_parent: Optional[bool] = Field(
        False,
        description="Đánh dấu câu hỏi này là Parent đại diện cho 1 block câu hỏi"
    )
    parent_block_id: Optional[str] = Field(
        None,
        description="ID trỏ về câu hỏi Parent đại diện cho block"
    )
    part_title: Optional[str] = Field(
        None,
        description="Tiêu đề của Part hoặc Passage (vd: 'Passage 1')"
    )
    original_question_number: Optional[int] = Field(
        None,
        description="Số thứ tự thật của câu hỏi in trên đề thi gốc (vd: 1, 14, 36)"
    )
    answer_placeholder: Optional[str] = Field(
        None,
        description="Placeholder/gợi ý hiển thị trong ô nhập liệu (vd: 'NO MORE THAN THREE WORDS')"
    )
    image_url: Optional[str] = Field(
        None,
        description="URL ảnh đính kèm (nếu câu hỏi có hình ảnh riêng)"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_llm_question(cls, value: Any) -> Any:
        """
        Validator thông minh chuẩn hóa dữ liệu trả về từ LLM trước khi Pydantic validate.
        """
        if not isinstance(value, dict):
            return value

        data = dict(value)

        raw_id = data.get("id") or data.get("question_id") or data.get("number")
        if raw_id is None:
            data["id"] = "temp_id"
        else:
            data["id"] = str(raw_id)

        raw_options = data.get("options", data.get("choices"))
        if isinstance(raw_options, dict):
            normalized_options: List[str] = []
            for label, option in raw_options.items():
                option_text = str(option).strip()
                label_text = str(label).strip()
                normalized_options.append(
                    option_text if option_text.startswith(f"{label_text}.") else f"{label_text}. {option_text}"
                )
            data["options"] = normalized_options
        elif raw_options is None:
            data["options"] = []
        elif isinstance(raw_options, list):
            data["options"] = [str(option) for option in raw_options]

        raw_type = data.get("type")
        if isinstance(raw_type, str):
            data["type"] = TYPE_ALIASES.get(raw_type.strip().lower(), raw_type.strip().lower())
        elif data["options"]:
            data["type"] = "multiple_choice"
        else:
            q_raw = data.get("question_text")
            question_text = str(q_raw) if q_raw is not None else ""
            data["type"] = "fill_in_the_blank" if "_" in question_text else "sentence_completion"

        if data.get("question_text") is None:
            data["question_text"] = ""

        if data.get("type") == "true_false_not_given" and not data.get("options"):
            q_text_lower = str(data.get("question_text", "")).lower()
            if "yes" in q_text_lower or "no" in q_text_lower:
                data["options"] = ["Yes", "No", "Not Given"]
            else:
                data["options"] = ["True", "False", "Not Given"]

        return data


class ExamExtractionSchema(BaseModel):
    """
    Schema bọc ngoài cùng cho kết quả trả về từ LLM.
    Hỗ trợ nhận diện cả cấu trúc 'sections' (cho bài đọc IELTS/Đọc hiểu)
    và cấu trúc phẳng 'questions'.
    """
    questions: List[QuestionSchema] = Field(
        default_factory=list, 
        description="Danh sách các câu hỏi đã được AI bóc tách và phân loại"
    )

    @model_validator(mode="before")
    @classmethod
    def wrap_and_flatten_sections(cls, value: Any) -> Any:
        """Tự động phân giải cả dạng list, dạng sections hoặc dạng questions."""
        if isinstance(value, list):
            return {"questions": value}
        
        if not isinstance(value, dict):
            return value

        # Trường hợp LLM trả về cấu trúc sections: [...]
        if "sections" in value and isinstance(value["sections"], list):
            flattened_questions = []
            for sec in value["sections"]:
                if not isinstance(sec, dict):
                    continue
                sec_title = sec.get("section_title") or sec.get("title") or sec.get("part")
                passage_text = sec.get("passage_text") or sec.get("passage") or sec.get("reading_passage") or sec.get("passage_ref")
                sec_questions = sec.get("questions") or sec.get("question_list") or []
                
                for q in sec_questions:
                    if isinstance(q, dict):
                        q_copy = dict(q)
                        if passage_text and not q_copy.get("passage_ref"):
                            q_copy["passage_ref"] = passage_text
                        if sec_title and not q_copy.get("part_title"):
                            q_copy["part_title"] = sec_title
                        flattened_questions.append(q_copy)

            if flattened_questions:
                return {"questions": flattened_questions}

        return value


class IELTSBlockSchema(BaseModel):
    """Schema cho một block câu hỏi (có thể là câu đơn hoặc range câu hỏi)."""
    block_id: str = Field(..., description="ID của block, ví dụ 'block_1'")
    range_start: Optional[int] = Field(None, description="Số thứ tự câu bắt đầu (vd: 1)")
    range_end: Optional[int] = Field(None, description="Số thứ tự câu kết thúc (vd: 5)")
    type: ComponentType = Field(..., description="Loại UI Component của block này")
    instruction: Optional[str] = Field(None, description="Câu lệnh hướng dẫn, vd: 'Choose NO MORE THAN TWO WORDS...'")
    block_content: Optional[str] = Field(None, description="Nội dung văn bản của block (vd: Cấu trúc bảng, đoạn tóm tắt) CỰC KỲ QUAN TRỌNG cho các dạng điền từ.")
    image_url: Optional[str] = Field(None, description="Trích xuất thẻ [[IMAGE_REF: ...]] từ Raw Text nếu có")
    questions: List[QuestionSchema] = Field(
        default_factory=list, 
        description="Danh sách các câu hỏi cụ thể bên trong block này"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_block_type(cls, value: Any) -> Any:
        if isinstance(value, dict):
            raw_type = value.get("type")
            if isinstance(raw_type, str):
                normalized = TYPE_ALIASES.get(raw_type.strip().lower(), raw_type.strip().lower())
                value["type"] = normalized
        return value

class IELTSPassageSchema(BaseModel):
    """Schema cho một Passage trong đề thi IELTS."""
    passage_id: str = Field(..., description="ID của passage, ví dụ 'P1', 'P2', 'P3'")
    title: Optional[str] = Field(default="", description="Tiêu đề của bài đọc")
    content: Optional[str] = Field(default="", description="Nội dung đầy đủ của bài đọc (loại bỏ các câu hỏi)")
    blocks: List[IELTSBlockSchema] = Field(
        default_factory=list,
        description="Danh sách các block câu hỏi thuộc bài đọc này"
    )

class IELTSExamSchema(BaseModel):
    """Schema bọc ngoài cùng cho kết quả bóc tách toàn bộ đề thi IELTS (1 request)."""
    passages: List[IELTSPassageSchema] = Field(
        ...,
        description="Danh sách đúng 3 bài đọc của đề IELTS"
    )

# ==========================================
# 2. Schemas cho CRUD API (Giao tiếp Frontend - Backend)
# ==========================================

from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator

class QuestionBase(BaseModel):
    """
    Schema chứa các trường chung nhất của một câu hỏi lưu trong DB.
    """
    component_type: ComponentType
    question_text: str
    options: List[str] = Field(default_factory=list)
    correct_answer: Optional[str] = None
    score_weight: float = 1.0
    passage_ref: Optional[str] = None
    part_title: Optional[str] = None
    answer_placeholder: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None
    original_question_number: Optional[int] = None

    @field_validator("options", mode="before")
    @classmethod
    def convert_none_to_list(cls, v):
        return v if v is not None else []


class QuestionCreate(QuestionBase):
    """
    Schema dùng khi Giáo viên muốn thêm tay một câu hỏi mới vào đề thi đã có.
    """
    exam_id: int


class QuestionUpdate(BaseModel):
    """
    Schema dùng cho API PATCH/PUT để chỉnh sửa câu hỏi (Ví dụ: Giáo viên phát hiện AI bóc tách sai).
    """
    component_type: Optional[ComponentType] = None
    question_text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    score_weight: Optional[float] = None
    passage_ref: Optional[str] = None
    part_title: Optional[str] = None
    answer_placeholder: Optional[str] = None
    image_url: Optional[str] = None


class QuestionOut(QuestionBase):
    """
    Schema trả về chi tiết câu hỏi cho Frontend render giao diện làm bài (GET /exams/{id}/questions).
    Đã được map từ cấu trúc SQLAlchemy Model.
    """
    id: int
    exam_id: int

    # ConfigDict(from_attributes=True) thay thế orm_mode trong Pydantic V2
    # Cho phép Pydantic tự động convert data từ class ORM (SQLAlchemy) sang JSON.
    model_config = ConfigDict(from_attributes=True)


class QuestionForStudentOut(QuestionBase):
    """
    Schema bảo mật: Dành riêng cho học sinh khi làm bài.
    Ghi đè trường correct_answer thành chuỗi rỗng hoặc bỏ đi để tránh học sinh 
    F12 mở Network Tab xem trộm được đáp án.
    """
    id: int
    exam_id: int
    correct_answer: Optional[str] = Field(None, exclude=True) # Loại bỏ trường này khỏi JSON trả về
    
    model_config = ConfigDict(from_attributes=True)
