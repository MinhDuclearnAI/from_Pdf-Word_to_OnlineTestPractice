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


logger = logging.getLogger(__name__)


def remove_json_comments(json_str: str) -> str:
    """
    Loại bỏ an toàn các comment dạng // hoặc /* */ trong JSON
    chỉ khi chúng nằm NGOÀI chuỗi string ngoặc kép "".
    """
    result = []
    in_string = False
    escape = False
    i = 0
    n = len(json_str)

    while i < n:
        char = json_str[i]

        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == '"':
                in_string = False
            i += 1
        else:
            if char == '"':
                in_string = True
                result.append(char)
                i += 1
            elif char == '/' and i + 1 < n and json_str[i + 1] == '/':
                # Bỏ qua comment // đến hết dòng
                i += 2
                while i < n and json_str[i] != '\n':
                    i += 1
            elif char == '/' and i + 1 < n and json_str[i + 1] == '*':
                # Bỏ qua comment /* */
                i += 2
                while i + 1 < n and not (json_str[i] == '*' and json_str[i + 1] == '/'):
                    i += 1
                i += 2  # Bỏ qua */
            else:
                result.append(char)
                i += 1

    return "".join(result)


def repair_json_string(json_str: str) -> str:
    """
    Tự động sửa các lỗi phổ biến khi LLM sinh JSON dài bị cụt đuôi hoặc thừa dấu phẩy.
    """
    text = json_str.strip()
    
    # 1. Xóa trailing commas trước } hoặc ]
    text = re.sub(r',\s*([\}\]])', r'\1', text)
    
    return text


def safe_json_parse(raw_json: str, schema: Any) -> Any:
    """
    Bóc tách JSON và validate theo Pydantic schema với cơ chế xử lý lỗi nhiều tầng.
    
    Args:
        raw_json: Chuỗi raw text chứa JSON.
        schema: Pydantic model hoặc List[...] dùng để validate kết quả.
        
    Raises:
        json.JSONDecodeError: nếu không thể parse json.
        ValidationError: nếu dữ liệu không khớp schema.
    """
    json_str = extract_json_from_markdown(raw_json)
    
    # Bỏ comment an toàn (không làm hỏng text bên trong string)
    json_str = remove_json_comments(json_str)
    json_str = repair_json_string(json_str)

    try:
        # strict=False cho phép các ký tự điều khiển (control chars/raw newlines) trong string
        data = json.loads(json_str, strict=False)
    except json.JSONDecodeError:
        # Thử lại nếu JSON bị cắt ngắn ở đuôi (auto-close open braces/brackets)
        stack = []
        in_str = False
        esc = False
        for ch in json_str:
            if in_str:
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch in ('{', '['):
                    stack.append(ch)
                elif ch == '}' and stack and stack[-1] == '{':
                    stack.pop()
                elif ch == ']' and stack and stack[-1] == '[':
                    stack.pop()
        
        repaired = json_str
        if in_str:
            repaired += '"'
        while stack:
            opener = stack.pop()
            repaired += '}' if opener == '{' else ']'
        
        repaired = re.sub(r',\s*([\}\]])', r'\1', repaired)
        data = json.loads(repaired, strict=False)

    from pydantic import BaseModel, TypeAdapter
    
    # Kiểm tra xem schema có phải là subclass của BaseModel không
    try:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema.model_validate(data)
    except TypeError:
        pass
        
    # Xử lý các Generic Types như List[Model]
    return TypeAdapter(schema).validate_python(data)