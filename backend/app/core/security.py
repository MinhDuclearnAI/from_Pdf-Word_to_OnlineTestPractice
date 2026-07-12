import os
from datetime import datetime, timedelta
from typing import Any, Union, Optional

import jwt
from passlib.context import CryptContext

# Trong thực tế, bạn sẽ import cấu hình từ app.config
# Ví dụ: from app.config import settings
class MockSettings:
    JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-for-dev-only-change-in-prod")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)) # Mặc định 1 ngày
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))           # Mặc định 7 ngày

settings = MockSettings()

# Khởi tạo ngữ cảnh của Passlib để sử dụng thuật toán bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu người dùng nhập vào có khớp với mật khẩu đã băm trong cơ sở dữ liệu hay không.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Băm mật khẩu bằng thuật toán bcrypt trước khi lưu vào cơ sở dữ liệu.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Tạo JWT Access Token để xác thực người dùng trong các API requests.
    
    Args:
        subject: Thông tin định danh người dùng (thường là user_id hoặc email).
        expires_delta: Thời gian sống của token. Nếu không truyền sẽ dùng mặc định từ settings.
        
    Returns:
        Chuỗi JWT Token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload chuẩn của JWT thường bao gồm 'exp' (thời gian hết hạn) và 'sub' (subject - định danh)
    to_encode = {"exp": expire, "sub": str(subject)}
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Tạo JWT Refresh Token (thời gian sống dài hơn) dùng để xin cấp lại Access Token mới khi bị hết hạn.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Giải mã và kiểm tra tính hợp lệ của JWT Token.
    
    Returns:
        Payload đã được giải mã (dạng dictionary) nếu token hợp lệ.
        
    Raises:
        jwt.ExpiredSignatureError: Nếu token đã hết hạn.
        jwt.InvalidTokenError: Nếu token bị sai chữ ký hoặc cấu trúc.
    """
    payload = jwt.decode(
        token, 
        settings.JWT_SECRET, 
        algorithms=[settings.JWT_ALGORITHM]
    )
    return payload