import logging
import time
from sqlalchemy.exc import OperationalError
from app.db.session import get_db_session
from app.db.init_db import init_db
import app.models  # Import models to register SQLAlchemy mappers properly

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    logger.info("Đang kết nối database và khởi tạo dữ liệu mẫu...")
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with get_db_session() as db:
                init_db(db)
                logger.info("Hoàn tất quy trình khởi tạo dữ liệu.")
                break
        except OperationalError as e:
            logger.warning(f"Database chưa sẵn sàng, thử lại lần {attempt + 1}/{max_retries}. Chi tiết: {e}")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Lỗi không xác định khi khởi tạo dữ liệu: {e}")
            break
    else:
        logger.error("Không thể kết nối đến Database sau nhiều lần thử.")

if __name__ == "__main__":
    main()
