# smartcapi-backend/app/model/tables.py

import datetime
import enum
from sqlalchemy import (Column, Integer, String, Boolean, DateTime, Date, Text,
                        ForeignKey, Enum as SQLAlchemyEnum, Float, UniqueConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# ENUMS
class UserRole(str, enum.Enum):
    ADMIN = 'ADMIN'
    ENUMERATOR = 'ENUMERATOR'
    SUPERVISOR = 'SUPERVISOR'

class InterviewStatus(str, enum.Enum):
    SUBMITTED = 'SUBMITTED'
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

class InterviewMode(str, enum.Enum):
    WITH_AI = 'WITH_AI'
    WITHOUT_AI = 'WITHOUT_AI'

class EducationLevel(str, enum.Enum):
    NONE = 'NONE'
    SD = 'SD'
    SMP = 'SMP'
    SMA = 'SMA'
    UNIVERSITY = 'UNIVERSITY'

class AnswerSource(str, enum.Enum):
    MANUAL = 'MANUAL'
    AI_GENERATED = 'AI_GENERATED'

# MODELS
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, increment=True)
    full_name = Column(String(255), nullable=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.ENUMERATOR)
    voice_sample_path = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interviews = relationship("Interview", back_populates="user")
    password_reset_token = relationship("PasswordResetToken", uselist=False, back_populates="user")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, increment=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="password_reset_token")

class Respondent(Base):
    __tablename__ = "respondents"

    id = Column(Integer, primary_key=True, increment=True)
    full_name = Column(String(255), nullable=False)
    gender = Column(String(10))
    place_of_birth = Column(String(50), nullable=True)
    date_of_birth = Column(Date)
    age = Column(Integer)
    education_level = Column(SQLAlchemyEnum(EducationLevel))
    occupation = Column(String(100))
    hobby = Column(String(50), nullable=True)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interviews = relationship("Interview", back_populates="respondent")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, increment=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    respondent_id = Column(Integer, ForeignKey('respondents.id'))
    interview_code = Column(String(50), unique=True, nullable=False)
    status = Column(SQLAlchemyEnum(InterviewStatus), default=InterviewStatus.PENDING)
    mode = Column(SQLAlchemyEnum(InterviewMode), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Integer)
    has_recording = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="interviews")
    respondent = relationship("Respondent", back_populates="interviews")
    audio_files = relationship("AudioFile", back_populates="interview")
    answers = relationship("Answer", back_populates="interview")

class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, increment=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'))
    file_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interview = relationship("Interview", back_populates="audio_files")
    transcription_segments = relationship("TranscriptionSegment", back_populates="audio_file")

class TranscriptionSegment(Base):
    __tablename__ = "transcription_segments"

    id = Column(Integer, primary_key=True, increment=True)
    audio_file_id = Column(Integer, ForeignKey('audio_files.id'))
    segment_start = Column(Float)
    segment_end = Column(Float)
    speaker_label = Column(String(50))
    transcription_text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    audio_file = relationship("AudioFile", back_populates="transcription_segments")
    answer_links = relationship("AnswerSegment", back_populates="segment")

class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, increment=True)
    interview_id = Column(Integer, ForeignKey('interviews.id'))
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text)
    source = Column(SQLAlchemyEnum(AnswerSource), default=AnswerSource.MANUAL)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interview = relationship("Interview", back_populates="answers")
    segment_links = relationship("AnswerSegment", back_populates="answer")

class AnswerSegment(Base):
    __tablename__ = "answer_segments"

    id = Column(Integer, primary_key=True, increment=True)
    answer_id = Column(Integer, ForeignKey('answers.id'), nullable=False)
    segment_id = Column(Integer, ForeignKey('transcription_segments.id'), nullable=False)

    answer = relationship("Answer", back_populates="segment_links")
    segment = relationship("TranscriptionSegment", back_populates="answer_links")

    __table_args__ = (UniqueConstraint('answer_id', 'segment_id', name='_answer_segment_uc'),)