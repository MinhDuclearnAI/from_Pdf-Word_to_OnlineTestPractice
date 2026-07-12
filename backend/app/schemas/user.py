from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# ==========================================
# Khai báo các Type (Literal) đồng bộ với thiết kế
# ==========================================
RoleType = Literal["student", "teacher"]


# ==========================================
# Base Schema (Chứa các trường chung nhất)
# ==========================================
class UserBase(BaseModel):
    """
    Schema gốc chứa các thông tin cơ bản nhất của một người dùng.
    Sử dụng EmailStr của Pydantic để tự động validate định dạng email (Gmail).
    """
    email: EmailStr = Field(
        ..., 
        description="Địa chỉ email của người dùng (dùng để đăng nhập)"
    )
    role: RoleType = Field(
        default="student", 
        description="Vai trò người dùng trong hệ thống: 'student' hoặc 'teacher'"
    )


# ==========================================
# Schemas cho Input (Auth - Đăng ký & Đăng nhập)
# ==========================================
class UserCreate(UserBase):
    """
    Schema nhận dữ liệu khi người dùng đăng ký tài khoản mới (POST /auth/register).
    Yêu cầu mật khẩu thô để backend tiến hành băm (hash) trước khi lưu.
    """
    password: str = Field(
        ..., 
        min_length=6, 
        description="Mật khẩu người dùng (yêu cầu tối thiểu 6 ký tự)"
    )


class UserLogin(BaseModel):
    """
    Schema nhận dữ liệu khi người dùng đăng nhập (POST /auth/login).
    """
    email: EmailStr = Field(..., description="Email đăng nhập")
    password: str = Field(..., description="Mật khẩu đăng nhập")


class UserUpdate(BaseModel):
    """
    Schema dùng cho API cập nhật thông tin cá nhân (PATCH /users/me).
    Các trường đều là Optional để hỗ trợ cập nhật từng phần.
    """
    password: Optional[str] = Field(
        None, 
        min_length=6, 
        description="Mật khẩu mới (nếu muốn đổi)"
    )
    # Có thể mở rộng thêm avatar_url, full_name, phone_number... tại đây trong tương lai


# ==========================================
# Schema cho Output (API Trả về)
# ==========================================
class UserOut(UserBase):
    """
    Schema định dạng dữ liệu trả về cho Frontend (GET /users/me, hoặc nằm trong danh sách lớp học).
    Tuyệt đối không chứa trường 'password' hay 'hashed_password' để đảm bảo an toàn.
    """
    id: int = Field(..., description="ID duy nhất của người dùng")
    created_at: datetime
    updated_at: datetime

    # ConfigDict(from_attributes=True) giúp Pydantic đọc trực tiếp data từ SQLAlchemy ORM object
    model_config = ConfigDict(from_attributes=True)