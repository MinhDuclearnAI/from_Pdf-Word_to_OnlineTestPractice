# Import all models to ensure SQLAlchemy mapper is initialized correctly
# when relationships between models are resolved by string names.
from .user import User
from .class_model import Class
from .enrollment import ClassEnrollment
from .exam import Exam
from .question import Question
from .submission import Submission
from .submission_draft import SubmissionDraft
from .ai_job import AIProcessingJob

__all__ = [
    "User",
    "Class",
    "ClassEnrollment",
    "Exam",
    "Question",
    "Submission",
    "SubmissionDraft",
    "AIProcessingJob",
]
