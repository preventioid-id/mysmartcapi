from datetime import datetime
from enum import Enum
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from app import db

# Enums
class InterviewStatus(Enum):
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class InterviewMode(Enum):
    WITH_AI = "WITH_AI"
    WITHOUT_AI = "WITHOUT_AI"

class EducationLevel(Enum):
    NONE = "NONE"
    SD = "SD"
    SMP = "SMP"
    SMA = "SMA"
    UNIVERSITY = "UNIVERSITY"

class UserRole(Enum):
    ADMIN = "ADMIN"
    ENUMERATOR = "ENUMERATOR"

class AnswerSource(Enum):
    MANUAL = "MANUAL"
    AI_GENERATED = "AI_GENERATED"

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.ENUMERATOR, nullable=False)
    voice_sample_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interviews = relationship("Interview", back_populates="user")
    password_reset_token = relationship("PasswordResetToken", back_populates="user", uselist=False)

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="password_reset_token")

class Respondent(db.Model):
    __tablename__ = 'respondents'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(10), nullable=True)
    place_of_birth = db.Column(db.String(50), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    education_level = db.Column(db.Enum(EducationLevel), nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    hobby = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interviews = relationship("Interview", back_populates="respondent")

class Interview(db.Model):
    __tablename__ = 'interviews'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    respondent_id = db.Column(db.Integer, db.ForeignKey("respondents.id"), nullable=True)
    interview_code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.Enum(InterviewStatus), default=InterviewStatus.PENDING, nullable=False)
    mode = db.Column(db.Enum(InterviewMode), nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    has_recording = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interviews")
    respondent = relationship("Respondent", back_populates="interviews")
    audio_files = relationship("AudioFile", back_populates="interview", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="interview", cascade="all, delete-orphan")

class AudioFile(db.Model):
    __tablename__ = 'audio_files'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interviews.id"), nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="audio_files")
    transcription_segments = relationship("TranscriptionSegment", back_populates="audio_file", cascade="all, delete-orphan")

class TranscriptionSegment(db.Model):
    __tablename__ = 'transcription_segments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    audio_file_id = db.Column(db.Integer, db.ForeignKey("audio_files.id"), nullable=False)
    segment_start = db.Column(db.Float, nullable=True)
    segment_end = db.Column(db.Float, nullable=True)
    speaker_label = db.Column(db.String(50), nullable=True)
    transcription_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    audio_file = relationship("AudioFile", back_populates="transcription_segments")
    answer_segments = relationship("AnswerSegment", back_populates="segment", cascade="all, delete-orphan")

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interviews.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    answer_text = db.Column(db.Text, nullable=True)
    source = db.Column(db.Enum(AnswerSource), default=AnswerSource.MANUAL, nullable=False)
    confidence_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="answers")
    answer_segments = relationship("AnswerSegment", back_populates="answer", cascade="all, delete-orphan")

class AnswerSegment(db.Model):
    __tablename__ = 'answer_segments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    answer_id = db.Column(db.Integer, db.ForeignKey("answers.id"), nullable=False)
    segment_id = db.Column(db.Integer, db.ForeignKey("transcription_segments.id"), nullable=False)

    answer = relationship("Answer", back_populates="answer_segments")
    segment = relationship("TranscriptionSegment", back_populates="answer_segments")

    __table_args__ = (
        UniqueConstraint('answer_id', 'segment_id', name='uix_answer_segment'),
    )