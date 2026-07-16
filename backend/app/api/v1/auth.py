from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import Database Dependencies
# Giả định get_db được định nghĩa ở app.api.deps để cấp phát session cho mỗi request
from app.api.deps import get_db

# Import Models & Schemas
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut

# Import Security & Exceptions
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token
)
from app.core.exceptions import DuplicateResourceError, AuthenticationError

# Khởi tạo Router cho Auth
router = APIRouter()

# ==========================================
# Schema nội bộ cho API Trả về Token
# ==========================================
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


# ==========================================
# 1. API Đăng ký (Register)
# ==========================================
@router.post("/register", response_model=UserOut, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Đăng ký tài khoản mới cho Học sinh hoặc Giáo viên.
    """
    from fastapi import HTTPException
    
    # 0. Validate yêu cầu bổ sung
    if user_in.role == "student":
        if not user_in.full_name or not user_in.date_of_birth or not user_in.school:
            raise HTTPException(status_code=400, detail="Học sinh bắt buộc phải nhập Họ tên, Ngày sinh và Trường lớp.")
    elif user_in.role == "teacher":
        if not user_in.full_name or not user_in.workplace:
            raise HTTPException(status_code=400, detail="Giáo viên bắt buộc phải nhập Họ tên và Nơi công tác.")

    # 1. Kiểm tra xem email đã tồn tại trong hệ thống chưa
    user_exists = db.query(User).filter(User.email == user_in.email).first()
    if user_exists:
        raise DuplicateResourceError("Email này đã được đăng ký. Vui lòng sử dụng email khác hoặc đăng nhập.")

    # 2. Băm mật khẩu (Hash password)
    hashed_pwd = get_password_hash(user_in.password)

    # 3. Tạo bản ghi User mới
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        role=user_in.role,
        full_name=user_in.full_name,
        date_of_birth=user_in.date_of_birth,
        school=user_in.school,
        workplace=user_in.workplace
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Lấy dữ liệu mới nhất (bao gồm cả ID sinh tự động) từ DB

    return new_user


# ==========================================
# 2. API Đăng nhập (Login)
# ==========================================
@router.post("/login", response_model=TokenResponse)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Đăng nhập bằng Email và Password. Trả về JWT Access Token và Refresh Token.
    """
    # 1. Tìm user theo email
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user:
        raise AuthenticationError("Email hoặc mật khẩu không chính xác.")

    # 2. Xác thực mật khẩu
    if not verify_password(user_in.password, user.hashed_password):
        raise AuthenticationError("Email hoặc mật khẩu không chính xác.")

    # 3. Tạo JWT Tokens
    # Dùng user.id làm subject (sub) cho token
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    # 4. Trả về Token kèm theo thông tin user cơ bản (để Frontend lưu vào Redux/Context)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


# ==========================================
# 3. API Refresh Token
# ==========================================
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Cấp lại Access Token mới khi token cũ hết hạn, dựa vào Refresh Token.
    """
    from app.core.security import verify_token
    import jwt
    
    try:
        # 1. Giải mã và kiểm tra Refresh Token
        payload = verify_token(request.refresh_token)
        
        # 2. Đảm bảo đây đúng là refresh token chứ không phải access token
        if payload.get("type") != "refresh":
            raise AuthenticationError("Token không hợp lệ.")
            
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Token không chứa định danh người dùng.")
            
        # 3. Kiểm tra xem user có còn tồn tại trong DB không
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise AuthenticationError("Tài khoản người dùng không còn tồn tại.")

        # 4. Tạo Access Token mới
        new_access_token = create_access_token(subject=user.id)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Refresh token đã hết hạn. Vui lòng đăng nhập lại.")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Token không hợp lệ.")


# ==========================================
# 4. API Đăng xuất (Logout)
# ==========================================
@router.post("/logout")
def logout():
    """
    API Đăng xuất.
    Với kiến trúc JWT Stateless hiện tại, việc đăng xuất chủ yếu được xử lý ở Frontend 
    bằng cách xóa token khỏi localStorage/Cookies. 
    API này trả về 200 OK để xác nhận hành động.
    """
    return {"message": "Đăng xuất thành công."}