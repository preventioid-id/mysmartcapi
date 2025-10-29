# models/speaker.py
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database.cloud_db import Base

class VoiceRegistry(Base):
    __tablename__ = "voice_registries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metadata pengguna & rekaman
    user_name = Column(String(255), nullable=False)
    duration = Column(Integer) # dalam detik
    audio_filename = Column(String(255), nullable=False)
    registration_type = Column(String(50)) # misal: "initial", "retrain"

    # Metadata sinkronisasi
    client_uuid = Column(String(255), unique=True, nullable=False, index=True)
    sync_status = Column(String(50), default="synced")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified_client = Column(DateTime)

    def __repr__(self):
        return f"<VoiceRegistry(user_name='{self.user_name}', client_uuid='{self.client_uuid}')>"
