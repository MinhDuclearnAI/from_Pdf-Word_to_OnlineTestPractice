import json
import re
import logging
from typing import Type, TypeVar, Callable, Optional, Any
from pydantic import BaseModel, ValidationError


def extract_json_from_markdown(text: str) -> str:
    """
    Bóc tách chuỗi JSON thuần từ phản hồi của LLM.
    Xử lý 3 trường hợp phổ biến:
      1. LLM trả về kèm markdown fence: ```json ... ```
      2. LLM trả về kèm markdown fence không ghi rõ ngôn ngữ: ``` ... ```
      3. LLM trả về JSON thuần nhưng có text thừa trước/sau (vd: "Đây là kết quả: [...]")
    """
    text = text.strip()

    # Trường hợp 1 & 2: có markdown code fence
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    # Trường hợp 3: không có fence, tìm object {...} hoặc array [...] đầu tiên bao trọn nội dung.
    # Output chuẩn hiện tại là {"questions": [...]}; phải ưu tiên object để không
    # làm mất key "questions" trước khi Pydantic validate ExamExtractionSchema.
    object_match = re.search(r"\{.*\}", text, re.DOTALL)
    if object_match:
        return object_match.group(0).strip()

    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if array_match:
        return array_match.group(0).strip()

    # Không tìm thấy cấu trúc JSON nào -> trả nguyên văn để bước parse phía sau tự báo lỗi rõ ràng
    return text


def safe_json_parse(raw_json: str, schema: Any) -> Any:
    """
    Bóc tách JSON và validate theo Pydantic schema.
    
    Args:
        raw_json: Chuỗi raw text chứa JSON.
        schema: Pydantic model hoặc List[...] dùng để validate kết quả.
        
    Raises:
        json.JSONDecodeError: nếu không thể parse json.
        ValidationError: nếu dữ liệu không khớp schema.
    """
    json_str = extract_json_from_markdown(raw_json)
    
    # Loại bỏ các comment dạng // nếu LLM vô tình sinh ra (nhưng bỏ qua http://)
    # Lấy các dòng, bỏ phần // comments ở cuối dòng, sau đó nối lại
    lines = json_str.splitlines()
    cleaned_lines = []
    for line in lines:
        if '"//"' in line or '://' in line:
            cleaned_lines.append(line)
        else:
            cleaned_lines.append(re.sub(r'//.*$', '', line))
    json_str = '\n'.join(cleaned_lines)

    data = json.loads(json_str)

    from pydantic import BaseModel, TypeAdapter
    
    # Kiểm tra xem schema có phải là subclass của BaseModel không
    try:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema.model_validate(data)
    except TypeError:
        pass
        
    # Xử lý các Generic Types như List[Model]
    return TypeAdapter(schema).validate_python(data)