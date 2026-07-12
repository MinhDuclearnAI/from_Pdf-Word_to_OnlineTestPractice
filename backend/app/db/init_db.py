import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Giả định bạn đã import các models và tiện ích băm mật khẩu
# Nếu đường dẫn import của bạn khác, hãy điều chỉnh lại cho khớp
from app.models.user import User
from app.models.class_model import Class
from app.models.exam import Exam
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    """
    Hàm khởi tạo dữ liệu mẫu (Mock Data) cho Database.
    Chỉ chèn dữ liệu nếu bảng User chưa có tài khoản giáo viên nào.
    """
    
    # 1. Kiểm tra xem database đã có dữ liệu chưa
    first_teacher = db.query(User).filter(User.role == "teacher").first()
    if first_teacher:
        logger.info("Dữ liệu mẫu đã tồn tại. Bỏ qua bước init_db.")
        return

    logger.info("Bắt đầu tạo dữ liệu mẫu: 1 Giáo viên, 1 Lớp học, 1 Đề thi...")

    try:
        # 2. Tạo 1 tài khoản Giáo viên mẫu
        teacher = User(
            email="teacher@examplatform.com",
            hashed_password=get_password_hash("123456"), # Thay bằng hàm băm password thực tế của bạn
            role="teacher"
        )
        db.add(teacher)
        db.flush() # flush để lấy được teacher.id ngay lập tức mà chưa cần commit

        # 3. Tạo 1 Lớp học mẫu do Giáo viên này quản lý
        demo_class = Class(
            name="Lớp Toán IELTS Nâng Cao",
            subject="Toán",
            teacher_id=teacher.id
        )
        db.add(demo_class)
        db.flush()

        # 4. Tạo 1 Đề thi mẫu cho Lớp học này
        demo_exam = Exam(
            class_id=demo_class.id,
            title="Đề Thi Thử Toán Lần 1",
            subject="Toán",
            test_type="practice",
            duration=90, # 90 phút
            open_at=datetime.utcnow(),
            close_at=datetime.utcnow() + timedelta(days=7), # Mở trong 7 ngày
            result_visibility="detailed"
        )
        db.add(demo_exam)
        
        # 5. Commit toàn bộ thay đổi vào database
        db.commit()
        logger.info("Khởi tạo dữ liệu mẫu thành công!")

    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi khi khởi tạo dữ liệu mẫu: {e}")
        raise e