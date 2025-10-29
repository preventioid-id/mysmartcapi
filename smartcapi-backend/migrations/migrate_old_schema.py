"""
Migration helper: try to move data from older schema to new DBML schema.

Features:
- Uses SQLAlchemy reflection to discover legacy tables/columns.
- Conservative: runs in dry-run by default (no writes). Use --apply to commit.
- Handles common legacy shapes observed in repo:
  * legacy transcripts table (uuid, speaker_id, text, updated_at) => transcription_segments
  * legacy audio_files table that included transcription fields => split into audio_files + transcription_segments
- Logs actions and creates basic mapping table in-memory to show how rows were mapped.

Usage:
  python migrate_old_schema.py --database-url sqlite:///smartcapi.db --dry-run
  python migrate_old_schema.py --database-url postgresql://... --apply

IMPORTANT:
- Inspect logs before using --apply on production.
- This script attempts best-effort mapping; manual review recommended.
"""
import argparse
import sys
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import Session
from datetime import datetime
import app.models as models
from app import create_app, db

def reflect_table(engine, table_name):
    meta = MetaData()
    try:
        tbl = Table(table_name, meta, autoload_with=engine)
        return tbl
    except Exception:
        return None

def migrate_transcripts(engine, session, legacy_table, apply=False):
    """
    Map legacy transcripts -> transcription_segments.
    Legacy columns expected: uuid, speaker_id, text, updated_at, maybe audio_file_path or interview_code
    """
    print("Migrating legacy transcripts table:", legacy_table.name)
    stmt = select(legacy_table)
    rows = engine.execute(stmt).fetchall()
    print("Found", len(rows), "rows in legacy transcripts")
    mappings = []
    for r in rows:
        # Try to extract fields defensively
        row = dict(r)
        text = row.get("text") or row.get("transcription") or row.get("transcript") or ""
        speaker = row.get("speaker_id") or row.get("speaker") or None
        updated = row.get("updated_at") or row.get("created_at") or row.get("timestamp") or None
        try:
            created_at = datetime.fromisoformat(updated) if isinstance(updated, str) else updated
        except Exception:
            created_at = datetime.utcnow()

        # Resolve audio file:
        audio_file_path = row.get("audio_file_path") or row.get("file_path") or row.get("audio_path")
        interview_code = row.get("interview_code") or row.get("survey_code") or None

        # Attempt to find interview by code
        interview = None
        if interview_code:
            interview = session.query(models.Interview).filter_by(interview_code=interview_code).first()

        # Find or create audio_file placeholder
        audio_file = None
        if audio_file_path:
            audio_file = session.query(models.AudioFile).filter_by(file_path=audio_file_path).first()
        if not audio_file:
            audio_file = models.AudioFile(
                interview_id=interview.id if interview else None,
                file_path=audio_file_path or "migrated_from_transcripts",
                created_at=created_at or datetime.utcnow()
            )
            if apply:
                session.add(audio_file)
                session.flush()
        # Create transcription_segment
        seg = models.TranscriptionSegment(
            audio_file_id=audio_file.id if apply else (None),
            segment_start=row.get("segment_start"),
            segment_end=row.get("segment_end"),
            speaker_label=speaker,
            transcription_text=text,
            created_at=created_at or datetime.utcnow()
        )
        if apply:
            # if audio_file not persisted yet in DB (apply True), ensure audio_file.id exists
            if audio_file.id is None:
                session.add(audio_file)
                session.flush()
            seg.audio_file_id = audio_file.id
            session.add(seg)
            session.flush()
            mappings.append({"legacy_id": row.get("id") or row.get("uuid"), "segment_id": seg.id, "audio_file_id": audio_file.id})
        else:
            mappings.append({"legacy_id": row.get("id") or row.get("uuid"), "would_create_segment": True, "audio_file_path": audio_file.file_path})
    return mappings

def migrate_audio_files_with_embedded_transcription(engine, session, legacy_table, apply=False):
    """
    Handle legacy audio_files table that included transcription columns.
    We split into audio_files rows + transcription_segments rows.
    """
    print("Migrating legacy audio_files-with-transcription:", legacy_table.name)
    stmt = select(legacy_table)
    rows = engine.execute(stmt).fetchall()
    mappings = []
    for r in rows:
        row = dict(r)
        file_path = row.get("file_path") or row.get("path") or row.get("audio_path") or "migrated_audio"
        interview_code = row.get("interview_code")
        interview = None
        if interview_code:
            interview = session.query(models.Interview).filter_by(interview_code=interview_code).first()

        audio_file = session.query(models.AudioFile).filter_by(file_path=file_path).first()
        if not audio_file:
            audio_file = models.AudioFile(
                interview_id=interview.id if interview else None,
                file_path=file_path,
                created_at=row.get("created_at") or datetime.utcnow()
            )
            if apply:
                session.add(audio_file)
                session.flush()

        # If transcription text exists in this table, create segment row
        text = row.get("transcription_text") or row.get("text") or row.get("transcript")
        if text:
            seg = models.TranscriptionSegment(
                audio_file_id=audio_file.id if apply else None,
                segment_start=row.get("segment_start"),
                segment_end=row.get("segment_end"),
                speaker_label=row.get("speaker_label") or row.get("speaker"),
                transcription_text=text,
                created_at=row.get("created_at") or datetime.utcnow()
            )
            if apply:
                session.add(seg)
                session.flush()
                mappings.append({"audio_file": audio_file.file_path, "segment_id": seg.id})
            else:
                mappings.append({"audio_file": audio_file.file_path, "would_create_segment": True})
    return mappings

def main(args):
    engine = create_engine(args.database_url)
    meta = MetaData()
    meta.reflect(bind=engine)
    session = None

    # Create app context to have models registered (for db.session binding)
    flask_app = create_app({'SQLALCHEMY_DATABASE_URI': args.database_url})
    with flask_app.app_context():
        session = db.session

        # Detect legacy tables heuristically
        legacy_transcripts = None
        legacy_audio_files = None
        for t in meta.tables.values():
            name = t.name.lower()
            if 'transcript' in name and legacy_transcripts is None:
                legacy_transcripts = t
            if 'audio' in name and ('transcription' in t.columns.keys() or 'transcription_text' in t.columns.keys() or 'transcript' in t.columns.keys()):
                legacy_audio_files = t

        mappings = {}
        if legacy_transcripts is not None:
            mappings['transcripts'] = migrate_transcripts(engine, session, legacy_transcripts, apply=args.apply)
        else:
            print("No legacy transcripts table found.")

        if legacy_audio_files is not None:
            mappings['audio_with_transcription'] = migrate_audio_files_with_embedded_transcription(engine, session, legacy_audio_files, apply=args.apply)
        else:
            print("No legacy audio_files-with-transcription table found.")

        if args.apply:
            session.commit()
            print("Migration applied. Mappings (sample):")
            for k, v in mappings.items():
                print(k, "=>", v[:10])
        else:
            print("Dry-run mode (no changes). Proposed mappings (sample):")
            for k, v in mappings.items():
                print(k, "=>", v[:10])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True, help="SQLAlchemy database URL")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = parser.parse_args()
    main(args)
