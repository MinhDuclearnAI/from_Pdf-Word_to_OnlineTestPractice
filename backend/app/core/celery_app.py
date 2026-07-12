import os
from celery import Celery

# Trong dự án thực tế, bạn nên import cấu hình từ file config của hệ thống
# Ví dụ: from app.config import settings -> broker_url = settings.REDIS_URL
class MockSettings:
    # URL mặc định cho Redis (tương ứng với service redis trong docker-compose)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings = MockSettings()

# 1. Khởi tạo Celery Application
# Tên của app ("worker") có thể đặt tùy ý, nhưng nên đồng nhất.
celery_app = Celery(
    "exam_platform_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    # Khai báo sẵn các thư mục/file chứa task để Celery tự động nhận diện (Auto-discover)
    include=[
        "app.tasks.exam_processing",
        "app.tasks.grading_tasks"
    ]
)

# 2. Cấu hình chuyên sâu cho Celery (Tối ưu cho tác vụ AI)
celery_app.conf.update(
    # Sử dụng chuẩn JSON để serialize dữ liệu truyền qua lại giữa FastAPI và Worker
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Cài đặt múi giờ (Phù hợp với khu vực Việt Nam)
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    
    # --- CÁC CẤU HÌNH QUAN TRỌNG CHO TÁC VỤ LLM / AI ---
    
    # task_acks_late = True: Đảm bảo worker chỉ báo cáo "xong" (ack) khi task THỰC SỰ chạy xong.
    # Nếu worker bị crash giữa chừng khi đang chờ LLM trả lời, task sẽ được đẩy lại vào Queue.
    task_acks_late=True,
    
    # worker_prefetch_multiplier = 1: Mỗi worker chỉ nhận đúng 1 task tại một thời điểm.
    # Tránh tình trạng một worker ôm quá nhiều file PDF nặng làm treo RAM, 
    # trong khi các worker khác lại ngồi rảnh rỗi.
    worker_prefetch_multiplier=1,
    
    # Giới hạn thời gian chạy tối đa cho một task (Tránh việc gọi API LLM bị treo vĩnh viễn)
    # Ví dụ: 10 phút (600s) cho tác vụ hard, và 8 phút (480s) cho soft limit
    task_time_limit=600,
    task_soft_time_limit=480,
)