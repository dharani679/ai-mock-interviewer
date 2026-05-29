from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


InterviewStatus = Literal["created", "in_progress", "completed"]


class InterviewCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    role: str = Field(min_length=2, max_length=150)
    domain: str | None = Field(default=None, max_length=100)
    mode: str | None = Field(default=None, max_length=80)
    difficulty: str | None = Field(default=None, max_length=50)
    job_description: str | None = None


class InterviewStatusUpdateRequest(BaseModel):
    status: InterviewStatus


class InterviewResponse(BaseModel):
    id: int
    user_id: int
    title: str
    role: str
    domain: str | None
    mode: str | None
    difficulty: str | None
    status: str
    job_description: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class InterviewListResponse(BaseModel):
    items: list[InterviewResponse]


class QuestionGenerateRequest(BaseModel):
    count: int = Field(default=5, ge=3, le=10)


class QuestionResponse(BaseModel):
    id: int
    interview_id: int
    question_text: str
    question_type: str | None
    difficulty: str | None
    order_index: int
    category: str | None
    expected_answer: str | None


class QuestionListResponse(BaseModel):
    items: list[QuestionResponse]
