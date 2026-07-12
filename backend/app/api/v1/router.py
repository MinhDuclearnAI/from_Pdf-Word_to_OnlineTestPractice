from fastapi import APIRouter

# Import tất cả các sub-routers đã được định nghĩa trong thư mục v1
from app.api.v1 import (
    auth,
    users,
    classes,
    exams,
    exam_upload,
    self_practice,
    submissions,
    grading,
    leaderboard,
    ws
)

# Khởi tạo APIRouter chính cho phiên bản v1
api_router = APIRouter()

# ==========================================
# 1. Module Auth & Users
# ==========================================
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users Profile"])

# ==========================================
# 2. Module Giáo viên & Quản lý Lớp học
# ==========================================
api_router.include_router(classes.router, prefix="/classes", tags=["Classes Management"])
# Đưa leaderboard vào chung prefix /classes vì endpoint là /classes/{id}/leaderboard
api_router.include_router(leaderboard.router, prefix="/classes", tags=["Leaderboard & Stats"])

# ==========================================
# 3. Module Quản lý Kỳ thi & Bóc tách AI
# ==========================================
# Đưa exam_upload lên trước exams để tránh xung đột route path (FastAPI match từ trên xuống)
api_router.include_router(exam_upload.router, prefix="/exams", tags=["Exam AI Upload"])
api_router.include_router(exams.router, prefix="/exams", tags=["Exams Management"])

# ==========================================
# 4. Module Nộp bài & Chấm điểm AI
# ==========================================
api_router.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])
# Đưa grading vào chung prefix /submissions vì endpoint là /submissions/{id}/grade-essay
api_router.include_router(grading.router, prefix="/submissions", tags=["AI Essay Grading"])

# ==========================================
# 5. Module Tự Luyện Tập (Học sinh)
# ==========================================
api_router.include_router(self_practice.router, prefix="/practice", tags=["Self Practice"])

# ==========================================
# 6. Module WebSocket (Real-time)
# ==========================================
api_router.include_router(ws.router, prefix="/ws", tags=["Real-time Notification"])