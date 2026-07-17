import json
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

# Khởi tạo logger để theo dõi kết nối WebSocket
logger = logging.getLogger(__name__)

router = APIRouter()

from app.config import settings

# ==========================================
# API WebSocket: Lắng nghe trạng thái Job (WS /ws/jobs/{job_id})
# ==========================================
@router.websocket("/jobs/{job_id}")
async def websocket_job_status(websocket: WebSocket, job_id: str):
    """
    Endpoint WebSocket để Frontend kết nối và lắng nghe tiến độ xử lý của hệ thống AI.
    Sử dụng cơ chế Pub/Sub của Redis để nhận thông điệp từ Celery Worker.
    """
    # 1. Chấp nhận kết nối từ Frontend
    await websocket.accept()
    
    # 2. Khởi tạo kết nối bất đồng bộ (async) tới Redis
    redis_client = aioredis.from_url(settings.REDIS_URL)
    pubsub = redis_client.pubsub()
    
    # Tên channel phải khớp tuyệt đối với tên channel mà notification_service (hoặc celery task) bắn ra
    channel_name = f"channel:ai_job_status:{job_id}"
    
    try:
        # 3. Đăng ký theo dõi (Subscribe) channel tương ứng với job_id
        await pubsub.subscribe(channel_name)
        logger.info(f"Client đã kết nối WebSocket và Subscribe vào channel: {channel_name}")
        
        # 4. Vòng lặp lắng nghe tin nhắn từ Redis
        while True:
            # Lấy tin nhắn từ Redis (timeout 1s để không block event loop quá lâu)
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            
            if message is not None:
                # Dữ liệu từ Redis trả về thường ở dạng bytes, cần decode ra chuỗi string
                data_str = message["data"].decode("utf-8")
                
                # Bắn dữ liệu thẳng về Frontend qua WebSocket
                try:
                    await websocket.send_text(data_str)
                except (WebSocketDisconnect, RuntimeError):
                    # Client đã rời trang hoặc backend vừa reload trong môi trường dev.
                    # Không tiếp tục publish vào một transport đã đóng.
                    logger.info(f"WebSocket client đã đóng trước khi nhận trạng thái job {job_id}.")
                    break
                
                # (Tùy chọn) Kiểm tra nếu tiến trình đã "done" hoặc "failed" thì có thể chủ động ngắt kết nối
                try:
                    parsed_data = json.loads(data_str)
                    if parsed_data.get("status") in ["done", "failed"]:
                        # Đợi một chút để Frontend kịp xử lý tin nhắn cuối cùng trước khi đóng
                        await asyncio.sleep(0.5)
                        break
                except json.JSONDecodeError:
                    pass
            
            # Nhường quyền điều khiển cho Event Loop của FastAPI xử lý các request khác
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        # Bắt exception khi người dùng chủ động đóng trình duyệt hoặc chuyển trang
        logger.info(f"Client ngắt kết nối WebSocket khỏi channel: {channel_name}")
        
    except Exception as e:
        logger.error(f"Lỗi WebSocket trên channel {channel_name}: {str(e)}", exc_info=True)
        
    finally:
        # 5. Dọn dẹp tài nguyên cực kỳ quan trọng để tránh rò rỉ bộ nhớ (Memory Leak)
        try:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()
            await redis_client.aclose() # Đóng kết nối Redis
        except Exception as cleanup_error:
            logger.debug(f"Lỗi dọn dẹp Redis cho job {job_id}: {cleanup_error}")
        
        # Đảm bảo socket đã được đóng an toàn
        try:
            await websocket.close()
        except RuntimeError:
            # Bỏ qua lỗi nếu socket đã bị đóng từ phía client
            pass
