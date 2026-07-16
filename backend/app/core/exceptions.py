from fastapi import status

class BaseAppException(Exception):
    """
    Lớp ngoại lệ cơ sở cho toàn bộ ứng dụng.
    """
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Đã xảy ra lỗi hệ thống."

    def __init__(self, message: str = None, status_code: int = None):
        super().__init__(message or self.message)
        if message:
            self.message = message
        if status_code is not None:
            self.status_code = status_code

class AuthenticationError(BaseAppException):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    message: str = "Thông tin xác thực không chính xác hoặc đã hết hạn."

class PermissionDeniedError(BaseAppException):
    status_code: int = status.HTTP_403_FORBIDDEN
    message: str = "Bạn không có quyền thực hiện hành động này."

class ResourceNotFoundError(BaseAppException):
    status_code: int = status.HTTP_404_NOT_FOUND
    message: str = "Không tìm thấy tài nguyên được yêu cầu."

class DuplicateResourceError(BaseAppException):
    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str = "Tài nguyên này đã tồn tại."

class FileParsingError(BaseAppException):
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
    message: str = "Lỗi khi xử lý hoặc phân tích tệp tin."

class InvalidSchemaError(BaseAppException):
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
    message: str = "Cấu trúc dữ liệu schema không hợp lệ."
