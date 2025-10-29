# models/interview.py
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database.cloud_db import Base

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Data dari form
    nama = Column(String(255), nullable=False)
    alamat = Column(Text)
    tempat_lahir = Column(String(100))
    tanggal_lahir = Column(String(100)) # Disimpan sebagai string sesuai Pydantic model
    usia = Column(Integer)
    pendidikan = Column(String(100))
    pekerjaan = Column(String(100))
    hobi = Column(Text)
    nomor_telepon = Column(String(20))
    alamat_email = Column(String(255))
    
    # Metadata rekaman
    duration = Column(Integer) # dalam detik
    mode = Column(String(50)) # "AI" atau "Manual"
    has_recording = Column(Boolean, default=False)
    audio_filename = Column(String(255), nullable=True)
    
    # Metadata sinkronisasi
    client_uuid = Column(String(255), unique=True, nullable=False, index=True)
    sync_status = Column(String(50), default="synced")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified_client = Column(DateTime)
    
    def __repr__(self):
        return f"<Interview(nama='{self.nama}', client_uuid='{self.client_uuid}')>"
