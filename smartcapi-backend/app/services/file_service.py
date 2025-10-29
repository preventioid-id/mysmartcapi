import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, BinaryIO, Tuple
from datetime import datetime
import json
import uuid
import config
from services.logging_service import get_logger, LogCategory

class FileType:
    """File type constants."""
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    DOCUMENT = "document"
    MODEL = "model"
    DATA = "data"
    UNKNOWN = "unknown"

class FileService:
    """Comprehensive file management service."""
    
    def __init__(self):
        self.logger = get_logger()
        self.base_dir = config.BASE_DIR
        self.dataset_dir = config.DATASET_DIR
        self.uploads_dir = config.UPLOADS_DIR
        self.temp_dir = config.TEMP_DIR
        self.model_dir = config.MODEL_DIR
        
        # Ensure directories exist
        self._ensure_directories()
        
        # File metadata storage
        self.metadata_file = config.LOGS_DIR / "file_metadata.json"
        self.file_registry = self._load_file_registry()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.dataset_dir,
            config.CLEAN_AUDIO_DIR,
            config.NOISY_AUDIO_DIR,
            self.uploads_dir,
            config.REGISTRATION_DIR,
            self.temp_dir,
            self.model_dir,
            config.LOGS_DIR,
            config.FEATURE_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_file_registry(self) -> Dict:
        """Load file registry from JSON."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_file_registry(self):
        """Save file registry to JSON."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.file_registry, f, indent=2)
    
    # ==================== FILE UPLOAD ====================
    
    def save_uploaded_file(self, file_content: bytes, filename: str,
                          destination: str, user_id: Optional[int] = None,
                          create_subdirs: bool = True) -> Dict:
        """
        Save uploaded file to specified destination.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            destination: Destination path relative to base dir
            user_id: User ID (for organizing files)
            create_subdirs: Create subdirectories if they don't exist
        
        Returns:
            Dictionary with file information
        """
        try:
            # Generate unique filename
            file_ext = Path(filename).suffix
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"
            
            # Determine destination path
            if user_id and create_subdirs:
                dest_path = self.uploads_dir / destination / f"user_{user_id}"
            else:
                dest_path = self.uploads_dir / destination
            
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Full file path
            file_path = dest_path / unique_filename
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Calculate file hash
            file_hash = self._calculate_hash(file_content)
            
            # Get file info
            file_info = self._get_file_info(file_path, filename, file_hash, user_id)
            
            # Register file
            self._register_file(file_path, file_info)
            
            self.logger.info(f"File uploaded: {filename}", LogCategory.FILE,
                           path=str(file_path), size=file_info['size_bytes'])
            
            return {
                'success': True,
                'file_path': str(file_path),
                'unique_filename': unique_filename,
                'original_filename': filename,
                'file_info': file_info
            }
        
        except Exception as e:
            self.logger.error(f"Failed to upload file: {filename}", 
                            LogCategory.FILE, exception=e)
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_file(self, source_path: str, destination: str,
                  move: bool = False, user_id: Optional[int] = None) -> Dict:
        """
        Save file from source to destination.
        
        Args:
            source_path: Source file path
            destination: Destination directory
            move: Move instead of copy
            user_id: User ID
        
        Returns:
            Dictionary with result
        """
        try:
            source = Path(source_path)
            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            
            # Determine destination
            if user_id:
                dest_dir = self.uploads_dir / destination / f"user_{user_id}"
            else:
                dest_dir = self.uploads_dir / destination
            
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / source.name
            
            # Copy or move
            if move:
                shutil.move(str(source), str(dest_path))
                action = "moved"
            else:
                shutil.copy2(str(source), str(dest_path))
                action = "copied"
            
            # Get file info
            with open(dest_path, 'rb') as f:
                content = f.read()
            file_hash = self._calculate_hash(content)
            file_info = self._get_file_info(dest_path, source.name, file_hash, user_id)
            
            # Register file
            self._register_file(dest_path, file_info)
            
            self.logger.info(f"File {action}: {source.name}", LogCategory.FILE,
                           from_path=str(source), to_path=str(dest_path))
            
            return {
                'success': True,
                'file_path': str(dest_path),
                'action': action,
                'file_info': file_info
            }
        
        except Exception as e:
            self.logger.error(f"Failed to save file: {source_path}",
                            LogCategory.FILE, exception=e)
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== FILE OPERATIONS ====================
    
    def read_file(self, file_path: str, mode: str = 'rb') -> Optional[bytes]:
        """
        Read file content.
        
        Args:
            file_path: Path to file
            mode: Read mode ('rb' for binary, 'r' for text)
        
        Returns:
            File content or None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"File not found: {file_path}", LogCategory.FILE)
                return None
            
            with open(path, mode) as f:
                return f.read()
        
        except Exception as e:
            self.logger.error(f"Failed to read file: {file_path}",
                            LogCategory.FILE, exception=e)
            return None
    
    def delete_file(self, file_path: str, permanent: bool = False) -> bool:
        """
        Delete file.
        
        Args:
            file_path: Path to file
            permanent: If True, permanently delete; otherwise move to temp
        
        Returns:
            True if successful
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"File not found for deletion: {file_path}",
                                  LogCategory.FILE)
                return False
            
            if permanent:
                path.unlink()
                action = "permanently deleted"
            else:
                # Move to temp/deleted directory
                deleted_dir = self.temp_dir / "deleted"
                deleted_dir.mkdir(parents=True, exist_ok=True)
                dest = deleted_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{path.name}"
                shutil.move(str(path), str(dest))
                action = "moved to trash"
            
            # Remove from registry
            self._unregister_file(path)
            
            self.logger.info(f"File {action}: {path.name}", LogCategory.FILE,
                           path=str(path))
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to delete file: {file_path}",
                            LogCategory.FILE, exception=e)
            return False
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """
        Move file to new location.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
        
        Returns:
            True if successful
        """
        try:
            source = Path(source_path)
            dest = Path(destination_path)
            
            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            
            # Create destination directory
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source), str(dest))
            
            # Update registry
            if str(source) in self.file_registry:
                file_info = self.file_registry.pop(str(source))
                file_info['path'] = str(dest)
                file_info['updated_at'] = datetime.now().isoformat()
                self.file_registry[str(dest)] = file_info
                self._save_file_registry()
            
            self.logger.info(f"File moved: {source.name}", LogCategory.FILE,
                           from_path=str(source), to_path=str(dest))
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to move file: {source_path}",
                            LogCategory.FILE, exception=e)
            return False
    
    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """Copy file to new location."""
        try:
            source = Path(source_path)
            dest = Path(destination_path)
            
            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(dest))
            
            self.logger.info(f"File copied: {source.name}", LogCategory.FILE,
                           from_path=str(source), to_path=str(dest))
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to copy file: {source_path}",
                            LogCategory.FILE, exception=e)
            return False
    
    # ==================== FILE INFORMATION ====================
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to file
        
        Returns:
            Dictionary with file information
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            # Check registry first
            if str(path) in self.file_registry:
                return self.file_registry[str(path)]
            
            # Calculate if not in registry
            with open(path, 'rb') as f:
                content = f.read()
            
            file_hash = self._calculate_hash(content)
            return self._get_file_info(path, path.name, file_hash)
        
        except Exception as e:
            self.logger.error(f"Failed to get file info: {file_path}",
                            LogCategory.FILE, exception=e)
            return None
    
    def _get_file_info(self, path: Path, original_name: str,
                       file_hash: str, user_id: Optional[int] = None) -> Dict:
        """Generate file information dictionary."""
        stats = path.stat()
        
        return {
            'path': str(path),
            'original_name': original_name,
            'filename': path.name,
            'extension': path.suffix,
            'size_bytes': stats.st_size,
            'size_mb': round(stats.st_size / (1024 * 1024), 2),
            'created_at': datetime.fromtimestamp(stats.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'file_type': self._detect_file_type(path),
            'mime_type': mimetypes.guess_type(str(path))[0],
            'hash': file_hash,
            'user_id': user_id
        }
    
    def _detect_file_type(self, path: Path) -> str:
        """Detect file type from extension."""
        ext = path.suffix.lower()
        
        audio_exts = ['.wav', '.mp3', '.ogg', '.flac', '.m4a', '.aac']
        video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']
        doc_exts = ['.pdf', '.doc', '.docx', '.txt', '.md']
        model_exts = ['.pkl', '.h5', '.pt', '.pth', '.onnx']
        data_exts = ['.csv', '.json', '.xml', '.xlsx']
        
        if ext in audio_exts:
            return FileType.AUDIO
        elif ext in video_exts:
            return FileType.VIDEO
        elif ext in image_exts:
            return FileType.IMAGE
        elif ext in doc_exts:
            return FileType.DOCUMENT
        elif ext in model_exts:
            return FileType.MODEL
        elif ext in data_exts:
            return FileType.DATA
        else:
            return FileType.UNKNOWN
    
    def _calculate_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    def verify_file_integrity(self, file_path: str) -> bool:
        """
        Verify file integrity using stored hash.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if file is intact
        """
        try:
            if str(file_path) not in self.file_registry:
                return False
            
            stored_hash = self.file_registry[str(file_path)]['hash']
            
            with open(file_path, 'rb') as f:
                current_hash = self._calculate_hash(f.read())
            
            return stored_hash == current_hash
        
        except Exception as e:
            self.logger.error(f"Failed to verify file integrity: {file_path}",
                            LogCategory.FILE, exception=e)
            return False
    
    # ==================== FILE REGISTRY ====================
    
    def _register_file(self, path: Path, file_info: Dict):
        """Register file in registry."""
        self.file_registry[str(path)] = file_info
        self._save_file_registry()
    
    def _unregister_file(self, path: Path):
        """Remove file from registry."""
        if str(path) in self.file_registry:
            del self.file_registry[str(path)]
            self._save_file_registry()
    
    def get_registered_files(self, file_type: Optional[str] = None,
                            user_id: Optional[int] = None) -> List[Dict]:
        """
        Get list of registered files.
        
        Args:
            file_type: Filter by file type
            user_id: Filter by user ID
        
        Returns:
            List of file information dictionaries
        """
        files = list(self.file_registry.values())
        
        if file_type:
            files = [f for f in files if f.get('file_type') == file_type]
        
        if user_id:
            files = [f for f in files if f.get('user_id') == user_id]
        
        return files
    
    # ==================== FILE SEARCH ====================
    
    def find_files(self, directory: str, pattern: str = "*",
                   recursive: bool = True, file_type: Optional[str] = None) -> List[Path]:
        """
        Find files matching pattern.
        
        Args:
            directory: Directory to search
            pattern: File pattern (e.g., "*.wav", "audio_*")
            recursive: Search recursively
            file_type: Filter by file type
        
        Returns:
            List of matching file paths
        """
        try:
            search_dir = Path(directory)
            if not search_dir.exists():
                return []
            
            if recursive:
                files = list(search_dir.rglob(pattern))
            else:
                files = list(search_dir.glob(pattern))
            
            # Filter by file type
            if file_type:
                files = [f for f in files if self._detect_file_type(f) == file_type]
            
            return [f for f in files if f.is_file()]
        
        except Exception as e:
            self.logger.error(f"Failed to find files in {directory}",
                            LogCategory.FILE, exception=e)
            return []
    
    def search_by_hash(self, file_hash: str) -> List[str]:
        """Find files with specific hash (detect duplicates)."""
        return [
            path for path, info in self.file_registry.items()
            if info.get('hash') == file_hash
        ]
    
    # ==================== DIRECTORY OPERATIONS ====================
    
    def create_directory(self, path: str) -> bool:
        """Create directory."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Directory created: {path}", LogCategory.FILE)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory: {path}",
                            LogCategory.FILE, exception=e)
            return False
    
    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """
        Delete directory.
        
        Args:
            path: Directory path
            recursive: Delete recursively
        
        Returns:
            True if successful
        """
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return False
            
            if recursive:
                shutil.rmtree(str(dir_path))
            else:
                dir_path.rmdir()
            
            self.logger.info(f"Directory deleted: {path}", LogCategory.FILE)
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to delete directory: {path}",
                            LogCategory.FILE, exception=e)
            return False
    
    def get_directory_size(self, path: str) -> Dict:
        """
        Get directory size and file count.
        
        Args:
            path: Directory path
        
        Returns:
            Dictionary with size information
        """
        try:
            dir_path = Path(path)
            if not dir_path.exists():
                return {'error': 'Directory not found'}
            
            total_size = 0
            file_count = 0
            
            for file in dir_path.rglob('*'):
                if file.is_file():
                    total_size += file.stat().st_size
                    file_count += 1
            
            return {
                'path': str(dir_path),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
                'file_count': file_count
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get directory size: {path}",
                            LogCategory.FILE, exception=e)
            return {'error': str(e)}
    
    # ==================== CLEANUP OPERATIONS ====================
    
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified hours.
        
        Args:
            older_than_hours: Delete files older than this many hours
        
        Returns:
            Number of files deleted
        """
        try:
            cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
            deleted_count = 0
            
            for file in self.temp_dir.rglob('*'):
                if file.is_file():
                    if file.stat().st_mtime < cutoff_time:
                        file.unlink()
                        deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} temp files", LogCategory.FILE)
            return deleted_count
        
        except Exception as e:
            self.logger.error("Failed to cleanup temp files", LogCategory.FILE, exception=e)
            return 0
    
    def cleanup_deleted_files(self, older_than_days: int = 30) -> int:
        """Clean up deleted files from trash."""
        try:
            deleted_dir = self.temp_dir / "deleted"
            if not deleted_dir.exists():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (older_than_days * 86400)
            deleted_count = 0
            
            for file in deleted_dir.iterdir():
                if file.is_file() and file.stat().st_mtime < cutoff_time:
                    file.unlink()
                    deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} deleted files", LogCategory.FILE)
            return deleted_count
        
        except Exception as e:
            self.logger.error("Failed to cleanup deleted files", LogCategory.FILE, exception=e)
            return 0
    
    # ==================== STATISTICS ====================
    
    def get_storage_statistics(self) -> Dict:
        """Get comprehensive storage statistics."""
        stats = {
            'directories': {},
            'total_size_mb': 0,
            'total_files': 0,
            'file_types': {}
        }
        
        directories = {
            'dataset': self.dataset_dir,
            'uploads': self.uploads_dir,
            'temp': self.temp_dir,
            'model': self.model_dir,
            'logs': config.LOGS_DIR
        }
        
        for name, path in directories.items():
            dir_stats = self.get_directory_size(str(path))
            stats['directories'][name] = dir_stats
            
            if 'total_size_mb' in dir_stats:
                stats['total_size_mb'] += dir_stats['total_size_mb']
                stats['total_files'] += dir_stats['file_count']
        
        # Count by file type
        for file_info in self.file_registry.values():
            file_type = file_info.get('file_type', FileType.UNKNOWN)
            stats['file_types'][file_type] = stats['file_types'].get(file_type, 0) + 1
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        stats['total_size_gb'] = round(stats['total_size_mb'] / 1024, 2)
        stats['registered_files'] = len(self.file_registry)
        
        return stats
    
    # ==================== VALIDATION ====================
    
    def validate_file(self, file_path: str, allowed_types: List[str],
                     max_size_mb: Optional[float] = None) -> Tuple[bool, str]:
        """
        Validate file type and size.
        
        Args:
            file_path: Path to file
            allowed_types: List of allowed file extensions
            max_size_mb: Maximum file size in MB
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False, "File not found"
            
            # Check extension
            if path.suffix.lower() not in allowed_types:
                return False, f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
            
            # Check size
            if max_size_mb:
                file_size_mb = path.stat().st_size / (1024 * 1024)
                if file_size_mb > max_size_mb:
                    return False, f"File too large. Maximum size: {max_size_mb}MB"
            
            return True, "File is valid"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"


# Global file service instance
_file_service = None

def get_file_service() -> FileService:
    """Get global file service instance."""
    global _file_service
    if _file_service is None:
        _file_service = FileService()
    return _file_service


if __name__ == "__main__":
    # Test file service
    service = FileService()
    
    print("Testing File Service...")
    
    # Get storage statistics
    stats = service.get_storage_statistics()
    print("\nStorage Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Find audio files
    audio_files = service.find_files(
        str(config.DATASET_DIR),
        "*.wav",
        recursive=True,
        file_type=FileType.AUDIO
    )
    print(f"\nFound {len(audio_files)} audio files")
    
    # Cleanup temp files
    cleaned = service.cleanup_temp_files(older_than_hours=24)
    print(f"\nCleaned up {cleaned} temporary files")
    
    print("\nFile service test completed!")