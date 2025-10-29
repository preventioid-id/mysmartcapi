from sqlalchemy.orm import Session
from app import db
from app.models import TranscriptionSegment, AudioFile, Interview
import time
from datetime import datetime

def sync_transcription_segments(db_session: Session, items: list[dict]):
    """
    items: list of dict with keys:
      - uuid (optional): legacy id
      - interview_code (optional): to find interview
      - audio_file_path (optional): used to find/create audio_file
      - segment_start, segment_end (optional floats)
      - speaker_label (optional)
      - transcription_text (string)
      - created_at or updated_at (ISO string or datetime)
    """
    results = []
    for item in items:
        # Resolve interview if provided
        interview = None
        if item.get("interview_code"):
            interview = db_session.query(Interview).filter_by(interview_code=item["interview_code"]).first()

        # Resolve or create audio_file
        audio_file = None
        if item.get("audio_file_path"):
            audio_file = db_session.query(AudioFile).filter_by(file_path=item["audio_file_path"]).first()
            if not audio_file:
                audio_file = AudioFile(
                    interview_id=interview.id if interview else None,
                    file_path=item["audio_file_path"],
                    created_at=datetime.utcnow()
                )
                db_session.add(audio_file)
                db_session.flush()  # get id

        # If no audio_file found, create a placeholder migrated file
        if not audio_file:
            audio_file = AudioFile(
                interview_id=interview.id if interview else None,
                file_path=item.get("audio_file_path") or "migrated_unknown",
                created_at=datetime.utcnow()
            )
            db_session.add(audio_file)
            db_session.flush()

        # Create new transcription segment
        seg = TranscriptionSegment(
            audio_file_id=audio_file.id,
            segment_start=item.get("segment_start"),
            segment_end=item.get("segment_end"),
            speaker_label=item.get("speaker_label"),
            transcription_text=item.get("transcription_text") or item.get("text"),
            created_at=item.get("created_at") or item.get("updated_at") or datetime.utcnow()
        )
        db_session.add(seg)
        results.append({"audio_file": audio_file.file_path, "segment_id": None, "status": "created"})
    db_session.commit()
    # populate created ids
    for r, seg in zip(results, db_session.query(TranscriptionSegment).order_by(TranscriptionSegment.id.desc()).limit(len(results)).all()[::-1]):
        r["segment_id"] = seg.id
    return results
