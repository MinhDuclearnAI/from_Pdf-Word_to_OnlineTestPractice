import os
import uuid
import logging
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError

# Giả định bạn đã cấu hình settings chung ở backend/app/config.py
# from app.config import settings
# Ở đây tôi mock class Settings để file này độc lập và dễ hiểu:
class MockSettings:
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000") # Dành cho MinIO local
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "exam-platform-bucket")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")

settings = MockSettings()
logger = logging.getLogger(__name__)

class StorageService:
    """
    Service quản lý việc lưu trữ file (PDF, DOCX) thông qua giao thức S3.
    Hỗ trợ MinIO cho môi trường Development và AWS S3 cho môi trường Production.
    """
    def __init__(self):
        self.bucket_name = settings.S3_BUCKET_NAME
        # Khởi tạo boto3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """
        Kiểm tra bucket đã tồn tại chưa. Nếu chưa thì tự động tạo mới.
        Rất hữu ích khi setup tự động môi trường dev với docker-compose (MinIO).
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                logger.info(f"Bucket '{self.bucket_name}' chưa tồn tại. Hệ thống đang tạo mới...")
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                logger.error(f"Lỗi không xác định khi kiểm tra bucket: {e}")
                raise

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Tạo tên file duy nhất (UUID) để tránh ghi đè dữ liệu trên S3."""
        ext = os.path.splitext(original_filename)[1]
        unique_id = uuid.uuid4().hex
        return f"{unique_id}{ext}"

    def upload_file(self, file_obj: BinaryIO, original_filename: str, content_type: str = "application/pdf", folder: str = "exams") -> str:
        """
        Upload file từ bộ nhớ (File được gửi qua API) lên S3.
        
        Args:
            file_obj: Object file đọc dưới dạng binary.
            original_filename: Tên file gốc.
            content_type: Kiểu MIME của file.
            folder: Thư mục logic trên S3 (ví dụ: 'exams', 'avatars').
            
        Returns:
            object_name: Đường dẫn key của file trên S3 (dùng để lưu vào DB).
        """
        unique_filename = self._generate_unique_filename(original_filename)
        object_name = f"{folder}/{unique_filename}" if folder else unique_filename

        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                object_name,
                ExtraArgs={'ContentType': content_type}
            )
            logger.info(f"Đã upload file thành công: {object_name}")
            return object_name
        except ClientError as e:
            logger.error(f"Lỗi khi upload file lên S3: {e}")
            raise Exception(f"Không thể upload file do lỗi từ storage server.")

    def get_presigned_url(self, object_name: str, expiration: int = 3600) -> Optional[str]:
        """
        Tạo một URL tạm thời (Presigned URL) có giới hạn thời gian sống.
        Dùng cho Frontend gọi thẳng tải file từ S3 mà không cần luân chuyển qua Backend,
        đảm bảo bảo mật và giảm tải băng thông.
        
        Args:
            object_name: Đường dẫn key đã lưu trong DB.
            expiration: Thời gian URL hết hạn (tính bằng giây). Mặc định 1 giờ.
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Lỗi khi tạo presigned URL cho {object_name}: {e}")
            return None

    def download_file_to_local(self, object_name: str, dest_dir: str = "/tmp") -> str:
        """
        Tải file từ S3 về local disk.
        Hàm này cực kỳ quan trọng đối với Celery Worker. Trước khi AI trích xuất (PyMuPDF), 
        worker cần tải file tĩnh về môi trường của nó để phân tích.
        
        Args:
            object_name: Đường dẫn key trên S3.
            dest_dir: Thư mục tải về. (Nên dùng /tmp trên Linux container).
            
        Returns:
            Đường dẫn tuyệt đối tới file vừa tải về.
        """
        filename = os.path.basename(object_name)
        dest_path = os.path.join(dest_dir, filename)
        
        try:
            self.s3_client.download_file(self.bucket_name, object_name, dest_path)
            logger.info(f"Đã tải thành công {object_name} về {dest_path}")
            return dest_path
        except ClientError as e:
            logger.error(f"Lỗi khi download file vật lý {object_name}: {e}")
            raise Exception(f"Không thể tải file từ Storage để xử lý.")

# Khởi tạo instance duy nhất (Singleton pattern) để import và dùng ở các module khác
# Ví dụ: từ app.services.storage_service import storage
storage = StorageService()