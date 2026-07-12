import os
import sys
import logging

# ==========================================
# 1. Xử lý Đường dẫn (Path Resolution)
# ==========================================
# Thêm thư mục gốc 'backend/' vào sys.path để có thể import trực tiếp package 'app'
# Điều này cực kỳ quan trọng vì thư mục 'worker/' nằm ngang hàng với 'app/'
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from celery.signals import worker_process_init, worker_process_shutdown

# ==========================================
# 2. Import Celery Instance & Các Module Tasks
# ==========================================
# Import app Celery đã được cấu hình từ core (chứa broker url, backend url...)
from app.core.celery_app import celery_app

# BẮT BUỘC: Phải import các file chứa tasks tại đây để Celery Registry nhận diện được.
# Nếu không import, worker khởi động thành công nhưng sẽ báo lỗi "NotRegistered" khi nhận task.
import app.tasks.exam_processing
import app.tasks.grading_tasks

# Import SQLAlchemy Engine để xử lý kết nối
from app.db.session import engine


logger = logging.getLogger(__name__)

# ==========================================
# 3. Quản lý Vòng đời Worker (Signals)
# ==========================================

@worker_process_init.connect
def init_worker_process(**kwargs):
    """
    Hook được kích hoạt mỗi khi một Worker Process (Child process) được sinh ra (Fork).
    SQLAlchemy Engine KHÔNG an toàn khi fork (Not fork-safe). Do đó, ta cần 
    dispose engine cũ để ép tiến trình con tự tạo Connection Pool mới độc lập.
    """
    logger.info("Khởi tạo Celery Worker Process. Đang dọn dẹp Database Engine cũ để tránh deadlock...")
    
    # Ép tạo lại Pool kết nối mới cho process này
    engine.dispose()
    
    # Nếu hệ thống AI của bạn có tải các model nhẹ cục bộ (như Sentence Transformers),
    # đây là nơi lý tưởng để load chúng vào RAM 1 lần cho mỗi worker:
    # load_local_embedding_model()


@worker_process_shutdown.connect
def shutdown_worker_process(**kwargs):
    """
    Hook được kích hoạt khi Worker Process bị tắt (Ví dụ: scale down, deploy bản mới).
    Đảm bảo đóng các kết nối dang dở một cách an toàn (Graceful Shutdown).
    """
    logger.info("Worker Process đang tắt. Đóng các kết nối Database...")
    engine.dispose()