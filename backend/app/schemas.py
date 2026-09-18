from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    school_slug: str = Field(min_length=2, max_length=120)
    identifier: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=200)


class ApplicationResponse(BaseModel):
    id: int
    reference_code: str
    status: str
    created_at: str


class AssessmentSubmission(BaseModel):
    school_slug: str = Field(min_length=2, max_length=120)
    subject: str = Field(min_length=2, max_length=120)
    answers: dict[str, str]


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(PENDING|APPROVED|REJECTED)$")


class SchoolResponse(BaseModel):
    id: int
    name: str
    slug: str
    motto: str | None = None
    logo_path: str | None = None


class AssessmentResponse(BaseModel):
    id: int
    student_number: str | None
    subject: str
    score: int
    total: int
    status: str
    date: str
    answers: dict[str, Any]
