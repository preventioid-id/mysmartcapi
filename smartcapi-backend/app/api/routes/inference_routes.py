from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import config
from api.database import get_db, User, Interview, InterviewSegment
from api.routes.auth_routes import get_current_user
from services.whisper_service import transcribe_audio
from inference.infer_speaker import predict_speaker
from utils.audio_utils import save_audio, load_audio

router = APIRouter()

# Pydantic models
class InterviewCreate(BaseModel):
    mode: str  # 'ai' or 'manual'
    respondent_id: Optional[str] = None

class InterviewResponse(BaseModel):
    id: int
    enumerator_id: int
    respondent_id: Optional[str]
    mode: str
    status: str
    start_time: datetime
    
    class Config:
        from_attributes = True

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    success: bool
    segments: List[Dict]

class SpeakerIdentificationResponse(BaseModel):
    speaker_id: str
    confidence: float
    is_enumerator: bool
    enumerator_name: Optional[str]

# Routes
@router.post("/interview/start", response_model=InterviewResponse)
async def start_interview(
    interview_data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start new interview session.
    
    Mode options:
    - 'ai': AI-assisted interview with automatic transcription
    - 'manual': Manual interview mode
    """
    if not current_user.is_enumerator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only enumerators can start interviews"
        )
    
    # Create interview record
    interview = Interview(
        enumerator_id=current_user.id,
        respondent_id=interview_data.respondent_id,
        mode=interview_data.mode,
        status='in_progress'
    )
    
    db.add(interview)
    db.commit()
    db.refresh(interview)
    
    return interview

@router.post("/interview/{interview_id}/upload-audio")
async def upload_interview_audio(
    interview_id: int,
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload audio recording for interview.
    
    Audio will be processed for:
    - Speaker diarization
    - Transcription
    - Speaker identification
    """
    # Get interview
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    if interview.enumerator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload audio for this interview"
        )
    
    # Save audio file
    audio_dir = config.UPLOADS_DIR / f"interview_{interview_id}"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    audio_path = audio_dir / f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    
    try:
        with open(audio_path, 'wb') as f:
            content = await audio_file.read()
            f.write(content)
        
        # Update interview
        interview.audio_file_path = str(audio_path)
        db.commit()
        
        return {
            "message": "Audio uploaded successfully",
            "interview_id": interview_id,
            "audio_path": str(audio_path)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload audio: {str(e)}"
        )

@router.post("/interview/{interview_id}/process")
async def process_interview_audio(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process interview audio:
    1. Speaker diarization
    2. Identify speakers (enumerator vs respondent)
    3. Transcribe each speaker segment
    4. Generate summary
    """
    # Get interview
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    if not interview.audio_file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio file uploaded for this interview"
        )
    
    try:
        # TODO: Implement full processing pipeline
        # For now, just transcribe the whole audio
        
        # Transcribe audio
        transcription = transcribe_audio(interview.audio_file_path, language="id")
        
        if not transcription['success']:
            raise Exception("Transcription failed")
        
        # Update interview
        interview.transcript = transcription['text']
        interview.status = 'completed'
        interview.end_time = datetime.now()
        db.commit()
        
        return {
            "message": "Interview processed successfully",
            "interview_id": interview_id,
            "transcript": transcription['text'],
            "language": transcription['language']
        }
    
    except Exception as e:
        interview.status = 'failed'
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process interview: {str(e)}"
        )

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio_file(
    audio_file: UploadFile = File(...),
    language: str = Form("id"),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe uploaded audio file using Whisper.
    
    Supports Indonesian ('id') and English ('en').
    """
    # Save temp file
    temp_file = config.TEMP_DIR / f"transcribe_{current_user.username}_{datetime.now().timestamp()}.wav"
    
    try:
        with open(temp_file, 'wb') as f:
            content = await audio_file.read()
            f.write(content)
        
        # Transcribe
        result = transcribe_audio(str(temp_file), language=language)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )
    
    finally:
        if temp_file.exists():
            temp_file.unlink()

@router.post("/identify-speaker", response_model=SpeakerIdentificationResponse)
async def identify_speaker(
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Identify speaker from audio file.
    
    Returns speaker ID, confidence score, and whether speaker is a registered enumerator.
    """
    # Save temp file
    temp_file = config.TEMP_DIR / f"identify_{current_user.username}_{datetime.now().timestamp()}.wav"
    
    try:
        with open(temp_file, 'wb') as f:
            content = await audio_file.read()
            f.write(content)
        
        # Predict speaker
        result = predict_speaker(str(temp_file))
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Speaker identification failed: {str(e)}"
        )
    
    finally:
        if temp_file.exists():
            temp_file.unlink()

@router.get("/interview/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get interview details."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    if interview.enumerator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this interview"
        )
    
    return interview

@router.get("/interviews", response_model=List[InterviewResponse])
async def list_interviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all interviews for current enumerator."""
    interviews = db.query(Interview).filter(
        Interview.enumerator_id == current_user.id
    ).order_by(Interview.start_time.desc()).all()
    
    return interviews