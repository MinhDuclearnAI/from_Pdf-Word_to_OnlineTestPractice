from typing import Generator
import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import cấu hình Database
# Giả định bạn cấu hình SessionLocal trong file app/db/session.py theo chuẩn FastAPI
from app.db.session import SessionLocal

# Import Models & Security
from app.models.user import User
from app.core.security import verify_token
from app.core.exceptions import AuthenticationError, PermissionDeniedError

# Khai báo scheme OAuth2 để FastAPI tự động trích xuất token từ header: "Authorization: Bearer <token>"
# URL này cũng giúp Swagger UI (/docs) hiển thị nút "Authorize" và tự động test API
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator:
    """
    Dependency quản lý phiên làm việc với Database (Database Session).
    Tự động mở kết nối khi request bắt đầu và đóng lại khi request kết thúc,
    đảm bảo không bị tràn kết nối (connection leak).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency xác thực người dùng.
    Giải mã JWT Token để lấy ID người dùng, sau đó truy vấn DB để đảm bảo tài khoản còn tồn tại.
    """
    try:
        # Giải mã và kiểm tra tính hợp lệ của token (chữ ký, thời gian hết hạn)
        payload = verify_token(token)
        
        # 'sub' (subject) thường được dùng để lưu ID định danh trong JWT
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise AuthenticationError("Token không hợp lệ hoặc thiếu định danh người dùng.")
            
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Token không hợp lệ.")
    except Exception:
        raise AuthenticationError("Xác thực thất bại. Vui lòng đăng nhập lại.")

    # Truy vấn DB để lấy thông tin chi tiết của người dùng
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise AuthenticationError("Tài khoản người dùng không còn tồn tại trong hệ thống.")
        
    return user


def get_current_teacher(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency phân quyền cấp cao (Authorization).
    Sử dụng lại get_current_user để lấy thông tin, sau đó kiểm tra Role.
    Nếu không phải Giáo viên, lập tức chặn request (trả về 403 Forbidden).
    """
    if current_user.role != "teacher":
        raise PermissionDeniedError("Thao tác này yêu cầu quyền Giáo viên.")
    
    return current_user