import json
import logging
import os
from typing import Any, Dict, Optional
import redis

# Giả định bạn đã cấu hình settings chung ở backend/app/config.py
# Ở đây tôi mock class Settings để file này độc lập và dễ chạy thử:
class MockSettings:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings = MockSettings()
logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service quản lý việc gửi thông báo (Pub/Sub) qua Redis.
    Được sử dụng chủ yếu bởi Celery Worker để báo cáo tiến độ xử lý file AI,
    sau đó FastAPI (tại api/v1/ws.py) sẽ lắng nghe và đẩy về Frontend qua WebSocket.
    """
    def __init__(self):
        try:
            # decode_responses=True giúp dữ liệu lấy ra từ Redis tự động chuyển thành string (thay vì bytes)
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection nhanh khi khởi động
            self.redis_client.ping()
            logger.info("Đã kết nối thành công tới Redis cho Notification Service.")
        except Exception as e:
            logger.error(f"Không thể kết nối tới Redis (Pub/Sub có thể không hoạt động): {e}")
            # Không raise exception để tránh crash toàn bộ app nếu Redis rớt mạng tạm thời
            self.redis_client = None

    def _get_job_channel(self, job_id: str) -> str:
        """
        Tạo tên channel duy nhất cho từng job_id.
        Frontend khi gọi WebSocket cũng sẽ subscribe vào đúng tên channel này.
        """
        return f"channel:ai_job_status:{job_id}"

    def publish_job_status(
        self, 
        job_id: str, 
        status: str, 
        progress: int = 0, 
        message: str = "", 
        result_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Bắn thông báo trạng thái của công việc (AI Processing, Auto Grading...) qua Redis.
        
        Args:
            job_id: ID của công việc (ví dụ: UUID của AIProcessingJob).
            status: Trạng thái hiện tại ("pending", "processing", "done", "failed").
            progress: Phần trăm hoàn thành (0-100) để UI vẽ Progress bar.
            message: Thông báo chi tiết (vd: "Đang đọc nội dung PDF...", "Hoàn thành bóc tách").
            result_data: Dữ liệu trả về khi thành công (vd: trả về exam_id để frontend redirect).
            
        Returns:
            bool: True nếu publish thành công, False nếu thất bại.
        """
        if not self.redis_client:
            logger.warning("Redis client không khả dụng. Bỏ qua việc gửi thông báo realtime.")
            return False

        channel = self._get_job_channel(job_id)
        
        # Cấu trúc JSON payload thống nhất để Frontend dễ dàng parse
        payload = {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "message": message
        }
        
        if result_data:
            payload["result"] = result_data

        try:
            # Chuyển Python Dictionary thành chuỗi JSON
            message_json = json.dumps(payload, ensure_ascii=False)
            
            # Publish thông điệp vào channel. 
            # redis_client.publish trả về số lượng client đang lắng nghe channel này.
            subscribers_count = self.redis_client.publish(channel, message_json)
            
            logger.debug(f"Đã publish '{status}' (Job: {job_id}) tới {subscribers_count} WebSocket client(s).")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi publish trạng thái cho job {job_id} vào Redis: {e}")
            return False

# Khởi tạo instance duy nhất (Singleton pattern) để dùng chung trên toàn hệ thống
# Ví dụ gọi trong Celery task: 
# from app.services.notification_service import notification
# notification.publish_job_status(job_id="123", status="processing", progress=50, message="Đang gọi AI...")
notification = NotificationService()