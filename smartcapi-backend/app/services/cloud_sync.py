"""
SmartCAPI Cloud Synchronization Service
Mengelola sinkronisasi data antara client (Progressive Web App) dan server
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiofiles
import httpx
from fastapi import UploadFile
import hashlib

from config import settings
from utils.file_service import FileService
from services.logging_service import LoggingService

logger = LoggingService.get_logger(__name__)


class CloudSyncService:
    """Service untuk sinkronisasi data dengan cloud storage dan database"""
    
    def __init__(self):
        self.sync_dir = Path(settings.SYNC_DIR)
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        
        self.audio_upload_dir = Path(settings.DATASET_DIR) / "uploads"
        self.audio_upload_dir.mkdir(parents=True, exist_ok=True)
        
        self.registration_dir = Path(settings.DATASET_DIR) / "registration"
        self.registration_dir.mkdir(parents=True, exist_ok=True)
        
        self.sync_queue_path = self.sync_dir / "sync_queue.json"
        self.sync_history_path = self.sync_dir / "sync_history.json"
        
        self.file_service = FileService()
        
    
    async def upload_audio_interview(
        self, 
        audio_file: UploadFile, 
        responden_id: str,
        enumerator_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Upload dan simpan audio wawancara dari PWA ke server
        
        Args:
            audio_file: File audio dari recording
            responden_id: ID responden
            enumerator_id: ID enumerator
            metadata: Metadata wawancara (timestamp, lokasi, dll)
            
        Returns:
            Dict dengan info file yang tersimpan
        """
        try:
            # Generate filename unik
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(f"{responden_id}_{timestamp}".encode()).hexdigest()[:8]
            filename = f"interview_{enumerator_id}_{responden_id}_{timestamp}_{file_hash}.wav"
            
            file_path = self.audio_upload_dir / filename
            
            # Simpan file audio
            content = await audio_file.read()
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Simpan metadata
            metadata_file = file_path.with_suffix('.json')
            metadata_info = {
                "responden_id": responden_id,
                "enumerator_id": enumerator_id,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": len(content),
                "upload_timestamp": timestamp,
                "duration_seconds": metadata.get("duration", 0),
                "location": metadata.get("location"),
                "device_info": metadata.get("device_info"),
                "sample_rate": metadata.get("sample_rate", 16000),
                "channels": metadata.get("channels", 1),
                "status": "uploaded",
                "processed": False
            }
            
            async with aiofiles.open(metadata_file, 'w') as f:
                await f.write(json.dumps(metadata_info, indent=2))
            
            # Log upload
            await self._log_sync_activity(
                activity_type="audio_upload",
                entity_id=responden_id,
                details=metadata_info,
                status="success"
            )
            
            logger.info(f"Audio wawancara berhasil diupload: {filename}")
            
            return {
                "success": True,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": len(content),
                "metadata": metadata_info
            }
            
        except Exception as e:
            logger.error(f"Error upload audio wawancara: {str(e)}")
            await self._log_sync_activity(
                activity_type="audio_upload",
                entity_id=responden_id,
                details={"error": str(e)},
                status="failed"
            )
            raise
    
    
    async def upload_registration_audio(
        self,
        audio_file: UploadFile,
        enumerator_id: str,
        username: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Upload audio registrasi enumerator baru untuk voice enrollment
        
        Args:
            audio_file: File audio recording registrasi (3-5 menit)
            enumerator_id: ID enumerator
            username: Username enumerator
            metadata: Metadata registrasi
            
        Returns:
            Dict dengan info registrasi
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"registration_{enumerator_id}_{timestamp}.wav"
            file_path = self.registration_dir / filename
            
            # Simpan file audio
            content = await audio_file.read()
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Simpan metadata registrasi
            registration_info = {
                "enumerator_id": enumerator_id,
                "username": username,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": len(content),
                "registration_timestamp": timestamp,
                "duration_seconds": metadata.get("duration", 0),
                "sample_rate": metadata.get("sample_rate", 16000),
                "status": "registered",
                "retrain_triggered": False,
                "retrain_status": "pending"
            }
            
            metadata_file = file_path.with_suffix('.json')
            async with aiofiles.open(metadata_file, 'w') as f:
                await f.write(json.dumps(registration_info, indent=2))
            
            # Tambahkan ke queue untuk retrain
            await self._add_to_retrain_queue(registration_info)
            
            # Log registrasi
            await self._log_sync_activity(
                activity_type="registration_upload",
                entity_id=enumerator_id,
                details=registration_info,
                status="success"
            )
            
            logger.info(f"Audio registrasi enumerator berhasil diupload: {filename}")
            
            return {
                "success": True,
                "filename": filename,
                "file_path": str(file_path),
                "enumerator_id": enumerator_id,
                "registration_info": registration_info
            }
            
        except Exception as e:
            logger.error(f"Error upload audio registrasi: {str(e)}")
            await self._log_sync_activity(
                activity_type="registration_upload",
                entity_id=enumerator_id,
                details={"error": str(e)},
                status="failed"
            )
            raise
    
    
    async def sync_responden_data(
        self,
        responden_data: Dict[str, Any],
        enumerator_id: str
    ) -> Dict[str, Any]:
        """
        Sinkronisasi data responden dari PWA ke database server
        
        Args:
            responden_data: Data responden yang dikumpulkan
            enumerator_id: ID enumerator yang melakukan survei
            
        Returns:
            Dict hasil sinkronisasi
        """
        try:
            timestamp = datetime.now().isoformat()
            
            # Tambahkan metadata sinkronisasi
            sync_data = {
                "responden_id": responden_data.get("responden_id"),
                "enumerator_id": enumerator_id,
                "sync_timestamp": timestamp,
                "data": responden_data,
                "sync_status": "pending"
            }
            
            # Simpan ke queue lokal dulu
            await self._add_to_sync_queue(sync_data)
            
            # Log sinkronisasi
            await self._log_sync_activity(
                activity_type="responden_sync",
                entity_id=responden_data.get("responden_id"),
                details=sync_data,
                status="queued"
            )
            
            logger.info(f"Data responden ditambahkan ke sync queue: {responden_data.get('responden_id')}")
            
            return {
                "success": True,
                "responden_id": responden_data.get("responden_id"),
                "sync_status": "queued",
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error sync data responden: {str(e)}")
            raise
    
    
    async def sync_extracted_answers(
        self,
        responden_id: str,
        extracted_answers: Dict[str, Any],
        verification_status: str
    ) -> Dict[str, Any]:
        """
        Sinkronisasi hasil ekstraksi jawaban yang sudah diverifikasi enumerator
        
        Args:
            responden_id: ID responden
            extracted_answers: Hasil ekstraksi dari AI/LLM
            verification_status: Status verifikasi (verified/corrected)
            
        Returns:
            Dict hasil sinkronisasi
        """
        try:
            timestamp = datetime.now().isoformat()
            
            sync_data = {
                "responden_id": responden_id,
                "extracted_answers": extracted_answers,
                "verification_status": verification_status,
                "sync_timestamp": timestamp,
                "sync_type": "extracted_answers"
            }
            
            # Simpan hasil verifikasi
            answers_file = self.sync_dir / f"answers_{responden_id}_{timestamp}.json"
            async with aiofiles.open(answers_file, 'w') as f:
                await f.write(json.dumps(sync_data, indent=2))
            
            # Log
            await self._log_sync_activity(
                activity_type="answers_sync",
                entity_id=responden_id,
                details=sync_data,
                status="success"
            )
            
            logger.info(f"Jawaban terverifikasi disinkronkan: {responden_id}")
            
            return {
                "success": True,
                "responden_id": responden_id,
                "verification_status": verification_status,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error sync extracted answers: {str(e)}")
            raise
    
    
    async def download_rekrutmen_data(
        self,
        enumerator_id: str
    ) -> Dict[str, Any]:
        """
        Download data rekrutmen responden untuk ditampilkan di PWA
        
        Args:
            enumerator_id: ID enumerator
            
        Returns:
            Dict data rekrutmen
        """
        try:
            # Simulasi download dari database
            # Di implementasi real, ini akan query database
            
            rekrutmen_data = {
                "enumerator_id": enumerator_id,
                "responden_list": [
                    {
                        "responden_id": "RESP001",
                        "nama": "John Doe",
                        "alamat": "Jl. Contoh No. 1",
                        "status": "pending_interview"
                    }
                    # ... data lainnya
                ],
                "download_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Data rekrutmen didownload untuk enumerator: {enumerator_id}")
            
            return rekrutmen_data
            
        except Exception as e:
            logger.error(f"Error download rekrutmen data: {str(e)}")
            raise
    
    
    async def check_sync_status(self) -> Dict[str, Any]:
        """
        Cek status sinkronisasi (pending items, errors, dll)
        
        Returns:
            Dict status sinkronisasi
        """
        try:
            sync_queue = await self._load_sync_queue()
            
            status = {
                "total_pending": len(sync_queue),
                "queue_items": sync_queue,
                "last_sync": await self._get_last_sync_time(),
                "sync_health": "healthy" if len(sync_queue) < 100 else "warning"
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking sync status: {str(e)}")
            return {"error": str(e)}
    
    
    async def process_sync_queue(self) -> Dict[str, Any]:
        """
        Process semua item di sync queue (background job)
        
        Returns:
            Dict hasil processing
        """
        try:
            sync_queue = await self._load_sync_queue()
            
            processed = 0
            failed = 0
            
            for item in sync_queue:
                try:
                    # Process item berdasarkan tipe
                    if item.get("sync_type") == "responden_sync":
                        # Sync ke database
                        await self._sync_to_database(item)
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing sync item: {str(e)}")
                    failed += 1
            
            # Clear processed items
            if processed > 0:
                await self._clear_processed_items(processed)
            
            return {
                "processed": processed,
                "failed": failed,
                "remaining": len(sync_queue) - processed
            }
            
        except Exception as e:
            logger.error(f"Error processing sync queue: {str(e)}")
            return {"error": str(e)}
    
    
    # Helper Methods
    
    async def _add_to_sync_queue(self, data: Dict[str, Any]):
        """Tambah item ke sync queue"""
        queue = await self._load_sync_queue()
        queue.append(data)
        await self._save_sync_queue(queue)
    
    
    async def _add_to_retrain_queue(self, registration_info: Dict[str, Any]):
        """Tambah registrasi baru ke retrain queue"""
        retrain_queue_path = self.sync_dir / "retrain_queue.json"
        
        queue = []
        if retrain_queue_path.exists():
            async with aiofiles.open(retrain_queue_path, 'r') as f:
                content = await f.read()
                queue = json.loads(content)
        
        queue.append(registration_info)
        
        async with aiofiles.open(retrain_queue_path, 'w') as f:
            await f.write(json.dumps(queue, indent=2))
    
    
    async def _load_sync_queue(self) -> List[Dict[str, Any]]:
        """Load sync queue dari file"""
        if not self.sync_queue_path.exists():
            return []
        
        async with aiofiles.open(self.sync_queue_path, 'r') as f:
            content = await f.read()
            return json.loads(content)
    
    
    async def _save_sync_queue(self, queue: List[Dict[str, Any]]):
        """Simpan sync queue ke file"""
        async with aiofiles.open(self.sync_queue_path, 'w') as f:
            await f.write(json.dumps(queue, indent=2))
    
    
    async def _clear_processed_items(self, count: int):
        """Hapus item yang sudah diproses dari queue"""
        queue = await self._load_sync_queue()
        queue = queue[count:]
        await self._save_sync_queue(queue)
    
    
    async def _sync_to_database(self, data: Dict[str, Any]):
        """Sync data ke database (implementasi sesuai DB yang digunakan)"""
        # Implementasi sync ke database
        # Contoh: insert/update ke PostgreSQL, MongoDB, dll
        pass
    
    
    async def _get_last_sync_time(self) -> Optional[str]:
        """Dapatkan waktu sync terakhir"""
        if not self.sync_history_path.exists():
            return None
        
        async with aiofiles.open(self.sync_history_path, 'r') as f:
            content = await f.read()
            history = json.loads(content)
            if history:
                return history[-1].get("timestamp")
        
        return None
    
    
    async def _log_sync_activity(
        self,
        activity_type: str,
        entity_id: str,
        details: Dict[str, Any],
        status: str
    ):
        """Log aktivitas sinkronisasi"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "activity_type": activity_type,
            "entity_id": entity_id,
            "details": details,
            "status": status
        }
        
        # Load history
        history = []
        if self.sync_history_path.exists():
            async with aiofiles.open(self.sync_history_path, 'r') as f:
                content = await f.read()
                history = json.loads(content)
        
        # Tambah log baru
        history.append(log_entry)
        
        # Batasi history (keep last 1000 entries)
        if len(history) > 1000:
            history = history[-1000:]
        
        # Save history
        async with aiofiles.open(self.sync_history_path, 'w') as f:
            await f.write(json.dumps(history, indent=2))


# Singleton instance
cloud_sync_service = CloudSyncService()