import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import pandas as pd
from sqlalchemy.orm import Session
import config
from api.database import User, VoiceRegistration
from utils.audio_utils import preprocess_audio, split_audio_file
from utils.feature_utils import extract_features_from_file

class VoiceRegistrationService:
    """Service for registering enumerator voices."""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.registration_dir = config.REGISTRATION_DIR
        self.enumerator_list_path = config.ENUMERATOR_LIST_PATH
        self.enumerator_list = self.load_enumerator_list()
    
    def load_enumerator_list(self) -> Dict:
        """Load enumerator list from JSON."""
        if self.enumerator_list_path.exists():
            with open(self.enumerator_list_path, 'r') as f:
                return json.load(f)
        return {}
    
    def save_enumerator_list(self):
        """Save enumerator list to JSON."""
        with open(self.enumerator_list_path, 'w') as f:
            json.dump(self.enumerator_list, f, indent=2)
    
    def register_voice(self, user_id: int, username: str, 
                      audio_file_path: str,
                      num_segments: int = 20) -> Dict:
        """
        Register user voice for speaker identification.
        
        Args:
            user_id: User ID
            username: Username
            audio_file_path: Path to uploaded audio file
            num_segments: Number of audio segments to create
        
        Returns:
            Registration result dictionary
        """
        try:
            # Create user directory
            user_dir = self.registration_dir / username
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Preprocess audio
            temp_preprocessed = config.TEMP_DIR / f"{username}_preprocessed.wav"
            preprocess_audio(audio_file_path, str(temp_preprocessed))
            
            # Split audio into segments
            segments = split_audio_file(
                str(temp_preprocessed),
                str(user_dir),
                segment_duration=config.AUDIO_DURATION
            )
            
            if len(segments) < num_segments:
                return {
                    'success': False,
                    'message': f'Audio too short. Need at least {num_segments} segments, got {len(segments)}',
                    'segments_created': len(segments)
                }
            
            # Use only required number of segments
            segments = segments[:num_segments]
            
            # Generate speaker ID
            speaker_id = f"enum_{user_id}_{username}"
            
            # Add to enumerator list
            self.enumerator_list[speaker_id] = {
                'user_id': user_id,
                'username': username,
                'registration_date': datetime.now().isoformat(),
                'num_segments': len(segments)
            }
            self.save_enumerator_list()
            
            # Save registration to database
            if self.db:
                registration = VoiceRegistration(
                    user_id=user_id,
                    speaker_id=speaker_id,
                    audio_file_path=str(user_dir),
                    is_verified=True,
                    confidence_score=1.0
                )
                self.db.add(registration)
                self.db.commit()
            
            # Log registration
            self.log_registration(user_id, username, speaker_id, len(segments))
            
            # Clean up temp file
            if temp_preprocessed.exists():
                temp_preprocessed.unlink()
            
            return {
                'success': True,
                'speaker_id': speaker_id,
                'username': username,
                'segments_created': len(segments),
                'message': 'Voice registration successful. Model will be retrained automatically.'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Registration failed: {str(e)}'
            }
    
    def log_registration(self, user_id: int, username: str, 
                        speaker_id: str, num_segments: int):
        """Log registration to CSV."""
        log_file = config.REGISTRATION_LOG
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'username': username,
            'speaker_id': speaker_id,
            'num_segments': num_segments,
            'status': 'pending_retrain'
        }
        
        # Create or append to CSV
        df = pd.DataFrame([log_data])
        if log_file.exists():
            df.to_csv(log_file, mode='a', header=False, index=False)
        else:
            df.to_csv(log_file, index=False)
    
    def get_pending_retrains(self) -> List[Dict]:
        """Get list of registrations pending retrain."""
        log_file = config.REGISTRATION_LOG
        
        if not log_file.exists():
            return []
        
        df = pd.read_csv(log_file)
        pending = df[df['status'] == 'pending_retrain']
        
        return pending.to_dict('records')
    
    def mark_retrain_complete(self, speaker_id: str):
        """Mark registration as retrained."""
        log_file = config.REGISTRATION_LOG
        
        if not log_file.exists():
            return
        
        df = pd.read_csv(log_file)
        df.loc[df['speaker_id'] == speaker_id, 'status'] = 'retrained'
        df.to_csv(log_file, index=False)
    
    def delete_voice_registration(self, user_id: int, speaker_id: str) -> bool:
        """Delete voice registration."""
        try:
            # Remove from enumerator list
            if speaker_id in self.enumerator_list:
                username = self.enumerator_list[speaker_id]['username']
                del self.enumerator_list[speaker_id]
                self.save_enumerator_list()
                
                # Remove audio files
                user_dir = self.registration_dir / username
                if user_dir.exists():
                    shutil.rmtree(user_dir)
                
                # Update database
                if self.db:
                    self.db.query(VoiceRegistration).filter(
                        VoiceRegistration.speaker_id == speaker_id
                    ).delete()
                    self.db.commit()
                
                return True
            
            return False
        
        except Exception as e:
            print(f"Error deleting registration: {e}")
            return False
    
    def get_registration_stats(self) -> Dict:
        """Get registration statistics."""
        total_enumerators = len(self.enumerator_list)
        
        # Count audio files
        total_segments = 0
        for speaker_id, info in self.enumerator_list.items():
            username = info['username']
            user_dir = self.registration_dir / username
            if user_dir.exists():
                total_segments += len(list(user_dir.glob("*.wav")))
        
        # Get pending retrains
        pending_retrains = len(self.get_pending_retrains())
        
        return {
            'total_enumerators': total_enumerators,
            'total_segments': total_segments,
            'pending_retrains': pending_retrains,
            'enumerators': list(self.enumerator_list.keys())
        }

def register_enumerator_voice(user_id: int, username: str, 
                              audio_file_path: str,
                              db: Session = None) -> Dict:
    """
    Convenience function to register enumerator voice.
    
    Args:
        user_id: User ID
        username: Username
        audio_file_path: Path to audio file
        db: Database session
    
    Returns:
        Registration result
    """
    service = VoiceRegistrationService(db)
    return service.register_voice(user_id, username, audio_file_path)