import json
import re
import logging
from typing import Type, TypeVar, Callable, Optional
from pydantic import BaseModel, ValidationError

from app.core.exceptions import InvalidSchemaError

logger = logging.getLogger(__name__)

# TypeVar để hỗ trợ Generic Types cho Pydantic Models
T = TypeVar("T", bound=BaseModel)


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

    # Trường hợp 3: không có fence, tìm object {...} hoặc array [...] đầu tiên bao trọn nội dung
    # Ưu tiên array trước vì phần lớn output của ta là list câu hỏi
    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if array_match:
        return array_match.group(0).strip()

    object_match = re.search(r"\{.*\}", text, re.DOTALL)
    if object_match:
        return object_match.group(0).strip()

    # Không tìm thấy cấu trúc JSON nào -> trả nguyên văn để bước parse phía sau tự báo lỗi rõ ràng
    return text


def safe_json_parse(
    llm_callable: Callable[[str], str],
    schema: Type[T],
    prompt: str,
    max_retries: int = 3,
) -> T:
    """
    Gọi LLM, bóc tách JSON, validate theo Pydantic schema.
    Nếu lỗi (JSON sai cú pháp hoặc không khớp schema), tự động retry với prompt
    được bổ sung thông tin lỗi để LLM tự sửa ở lần gọi sau.

    Args:
        llm_callable: hàm nhận vào prompt (str) và trả về raw text response từ LLM.
        schema: Pydantic model dùng để validate kết quả.
        prompt: prompt gốc gửi cho LLM.
        max_retries: số lần thử lại tối đa khi gặp lỗi.

    Raises:
        InvalidSchemaError: khi đã hết số lần retry mà vẫn không parse/validate được.
    """
    current_prompt = prompt
    last_error: Optional[Exception] = None
    raw_response = ""

    for attempt in range(1, max_retries + 1):
        try:
            raw_response = llm_callable(current_prompt)
            json_str = extract_json_from_markdown(raw_response)
            data = json.loads(json_str)

            # Hỗ trợ cả trường hợp schema bọc list (vd: {"questions": [...]})
            # lẫn schema là chính list đó luôn.
            validated = schema.model_validate(data)

            if attempt > 1:
                logger.info(f"safe_json_parse: thành công ở lần thử thứ {attempt}")
            return validated

        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            logger.warning(
                f"safe_json_parse: lỗi ở lần thử {attempt}/{max_retries} - {type(e).__name__}: {e}"
            )

            if attempt < max_retries:
                # Bổ sung lỗi cụ thể vào prompt để LLM tự sửa ở lần gọi tiếp theo
                current_prompt = (
                    f"{prompt}\n\n"
                    f"--- LƯU Ý QUAN TRỌNG ---\n"
                    f"Ở lần trả lời trước, kết quả của bạn bị lỗi:\n{type(e).__name__}: {e}\n"
                    f"Nội dung bạn đã trả về (một phần):\n{raw_response[:1000]}\n\n"
                    f"Hãy trả lời lại CHÍNH XÁC theo đúng schema JSON yêu cầu, "
                    f"KHÔNG kèm markdown fence, KHÔNG kèm giải thích, chỉ trả về JSON thuần túy."
                )

    # Hết số lần retry mà vẫn lỗi
    logger.error(
        f"safe_json_parse: thất bại sau {max_retries} lần thử. Lỗi cuối: {last_error}"
    )
    raise InvalidSchemaError(
        f"Không thể parse/validate kết quả từ LLM sau {max_retries} lần thử: {last_error}"
    )