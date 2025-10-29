# smartcapi-backend/app/schemas/interview.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from ..model.tables import InterviewStatus, InterviewMode, EducationLevel, AnswerSource
from .auth import UserResponse

# Respondent Schemas
class RespondentBase(BaseModel):
    full_name: str
    gender: Optional[str] = None
    place_of_birth: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    education_level: Optional[EducationLevel] = None
    occupation: Optional[str] = None
    hobby: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class RespondentCreate(RespondentBase):
    pass

class Respondent(RespondentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Interview Schemas
class InterviewBase(BaseModel):
    interview_code: str
    status: Optional[InterviewStatus] = InterviewStatus.PENDING
    mode: InterviewMode
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    has_recording: Optional[bool] = False

class InterviewCreate(InterviewBase):
    user_id: int
    respondent_id: int

class Interview(InterviewBase):
    id: int
    user: UserResponse
    respondent: Respondent
    created_at: datetime

    class Config:
        orm_mode = True

# AudioFile Schemas
class AudioFileBase(BaseModel):
    file_path: str

class AudioFileCreate(AudioFileBase):
    interview_id: int

class AudioFile(AudioFileBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# TranscriptionSegment Schemas
class TranscriptionSegmentBase(BaseModel):
    segment_start: float
    segment_end: float
    speaker_label: str
    transcription_text: str

class TranscriptionSegmentCreate(TranscriptionSegmentBase):
    audio_file_id: int

class TranscriptionSegment(TranscriptionSegmentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Answer Schemas
class AnswerBase(BaseModel):
    question_text: str
    answer_text: Optional[str] = None
    source: Optional[AnswerSource] = AnswerSource.MANUAL
    confidence_score: Optional[float] = None

class AnswerCreate(AnswerBase):
    interview_id: int

class Answer(AnswerBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# AnswerSegment Schemas
class AnswerSegmentBase(BaseModel):
    answer_id: int
    segment_id: int

class AnswerSegmentCreate(AnswerSegmentBase):
    pass

class AnswerSegment(AnswerSegmentBase):
    id: int

    class Config:
        orm_mode = True