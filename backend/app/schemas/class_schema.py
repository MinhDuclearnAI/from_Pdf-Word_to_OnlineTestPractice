from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ClassBase(BaseModel):
    name: str
    subject: Optional[str] = None

class ClassCreate(ClassBase):
    pass

class ClassOut(ClassBase):
    id: int
    teacher_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
