from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Import Database Dependencies
from app.api.deps import get_db, get_current_user

# Import Models
from app.models.user import User

# Import Schemas
from app.schemas.user import UserOut, UserUpdate

# Import Security
from app.core.security import get_password_hash

router = APIRouter()

# ==========================================
# 1. Lấy thông tin cá nhân (GET /users/me)
# ==========================================
@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Lấy thông tin profile của người dùng đang đăng nhập hiện tại.
    API này thường được Frontend gọi ngay sau khi đăng nhập thành công 
    hoặc khi load lại trang (F5) để nạp dữ liệu vào Redux/Context.
    """
    # current_user đã được query và xác thực bên trong dependency get_current_user
    # nên ở đây chỉ việc trả về trực tiếp. Schema UserOut sẽ tự động lọc bỏ password.
    return current_user


# ==========================================
# 2. Cập nhật thông tin cá nhân (PATCH /users/me)
# ==========================================
@router.patch("/me", response_model=UserOut)
def update_current_user(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cập nhật thông tin cá nhân (Ví dụ: Đổi mật khẩu).
    Chỉ cập nhật những trường được gửi lên (exclude_unset=True).
    """
    # Chuyển đổi payload Pydantic thành dictionary, bỏ qua các trường không được gửi
    update_data = user_in.model_dump(exclude_unset=True)

    # Nếu có yêu cầu đổi mật khẩu, tiến hành băm (hash) trước khi lưu
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        current_user.hashed_password = hashed_password
        del update_data["password"] # Xóa key password thô để tránh lưu nhầm

    # Cập nhật các trường thông tin khác (nếu có mở rộng thêm avatar, full_name sau này)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    
    return current_user