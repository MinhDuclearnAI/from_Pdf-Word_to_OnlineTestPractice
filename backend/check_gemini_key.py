import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Tạm dùng GEMINI_API_KEY vì key hiện tại đang đặt ở đó.
# Khi tích hợp chính thức, nên đổi tên thành VILAO_API_KEY.
api_key = os.getenv("GEMINI_API_KEY", "").strip()

if not api_key:
    print("FAIL: Không tìm thấy API key trong biến môi trường.")
    sys.exit(1)

request = Request(
    "https://api.vilao.ai/v1/models",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    },
)

try:
    with urlopen(request, timeout=15) as response:
        content_type = response.headers.get_content_type()
        body = response.read().decode("utf-8", errors="replace")

    if content_type != "application/json":
        print(f"FAIL: API trả Content-Type '{content_type}', không phải JSON.")
        sys.exit(1)

    data = json.loads(body)
    models = data.get("data", [])
    print(f"OK: Key ViLao hợp lệ. API trả về {len(models)} model.")
    sys.exit(0)

except HTTPError as error:
    body = error.read().decode("utf-8", errors="replace")
    print(f"FAIL: HTTP {error.code} | {body[:300]}")
    sys.exit(1)

except URLError as error:
    print(f"FAIL: Không kết nối được ViLao API: {error.reason}")
    sys.exit(1)