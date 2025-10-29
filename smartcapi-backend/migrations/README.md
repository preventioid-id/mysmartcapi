"""markdown
``` 
# Migration scripts

See migrate_old_schema.py for an idempotent, defensive migration helper to move legacy transcript/audio records
into the new audio_files + transcription_segments schema.

Basic usage:
- Inspect the DB first with dry-run:
  python migrate_old_schema.py --database-url sqlite:///smartcapi.db
- When satisfied, run with --apply:
  python migrate_old_schema.py --database-url sqlite:///smartcapi.db --apply

Caveats:
- This is best-effort. Review logs and resulting rows before deleting legacy tables.
- Backup your DB before running --apply.
```