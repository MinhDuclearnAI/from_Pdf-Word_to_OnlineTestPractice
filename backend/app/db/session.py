import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

# Import SessionLocal đã được định nghĩa ở file base.py
from app.db.base import SessionLocal

logger = logging.getLogger(__name__)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager để cấp phát và quản lý Database Session.
    Được thiết kế chuyên biệt để sử dụng trong Celery Workers, Background Tasks, 
    hoặc các luồng xử lý không gắn với FastAPI HTTP Request.
    
    Cách hoạt động:
    - Mở một session mới.
    - Yield session ra cho caller sử dụng.
    - Tự động rollback nếu có Exception xảy ra trong quá trình xử lý.
    - Luôn luôn đóng (close) session ở block finally để trả connection về pool.
    """
    db: Session = SessionLocal()
    try:
        yield db
        
        # Lưu ý: Không tự động gọi db.commit() ở đây.
        # Nguyên tắc Best Practice là để hàm gọi (caller) chủ động gọi db.commit() 
        # khi họ chắc chắn logic nghiệp vụ đã thành công hoàn toàn.
        
    except Exception as e:
        # Nếu có bất kỳ lỗi nào (kể cả lỗi từ LLM, hay lỗi logic Python),
        # tự động rollback database để tránh trạng thái dữ liệu lơ lửng (dirty state).
        logger.error(f"Lỗi hệ thống hoặc Database, đang thực hiện rollback: {e}")
        db.rollback()
        raise e
        
    finally:
        # Quan trọng nhất: Luôn đóng session để giải phóng tài nguyên.
        db.close()