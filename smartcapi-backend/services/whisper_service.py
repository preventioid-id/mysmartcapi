"""
Whisper service integration (placeholder).
This module demonstrates how to save transcription segments into transcription_segments table.
Replace the transcribe_file(...) implementation with actual call to your ASR model.
"""
from typing import List, Dict
from app import db
from app.models import AudioFile, TranscriptionSegment
from datetime import datetime

def transcribe_file_and_save(audio_file_path: str, segments: List[Dict]):
    """
audio_file_path: file path string
segments: list of dicts:
      - start, end, speaker, text
Behavior:
      - find/create AudioFile by file_path
      - insert TranscriptionSegment rows for every segment
    """
    session = db.session
    audio = session.query(AudioFile).filter_by(file_path=audio_file_path).first()
    if not audio:
        audio = AudioFile(file_path=audio_file_path, created_at=datetime.utcnow())
        session.add(audio)
        session.flush()

    created = []
    for s in segments:
        seg = TranscriptionSegment(
            audio_file_id=audio.id,
            segment_start=s.get("start"),
            segment_end=s.get("end"),
            speaker_label=s.get("speaker"),
            transcription_text=s.get("text"),
            created_at=s.get("created_at") or datetime.utcnow()
        )
        session.add(seg)
        created.append(seg)
    session.commit()
    return [c.id for c in created]
