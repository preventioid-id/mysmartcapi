import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
# config is a local import, assuming it exists and is correct
import config 
# UPDATED IMPORTS
from app.model.tables import Interview, AudioFile, TranscriptionSegment, UserRole, InterviewStatus
from utils.audio_utils import load_audio, split_audio, preprocess_audio, save_audio
# These are local project imports, assuming they are correct
from inference.infer_speaker import SpeakerPredictor
from services.whisper_service import WhisperTranscriber
from utils.feature_utils import extract_all_features

class InferenceService:
    """Service for complete interview inference pipeline."""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.speaker_predictor = SpeakerPredictor()
        self.transcriber = WhisperTranscriber()
        self.inference_log = config.INFERENCE_LOG
    
    def process_interview_audio(self, interview_id: int, 
                               audio_path: str,
                               segment_duration: float = None) -> Dict:
        """
        Process complete interview audio:
        1. Split audio into segments
        2. Identify speaker for each segment
        3. Transcribe each segment
        4. Combine results and save to database.
        """
        try:
            print(f"Processing interview {interview_id}...")
            
            # Step 1: Load and preprocess audio
            print("Step 1: Loading and preprocessing audio...")
            audio, sr = preprocess_audio(audio_path)
            
            # Step 2: Split audio into segments
            print("Step 2: Splitting audio into segments...")
            if segment_duration is None:
                segment_duration = config.AUDIO_DURATION
            
            segments = split_audio(audio, sr, segment_duration)
            print(f"Created {len(segments)} segments")
            
            # Step 3: Process each segment
            print("Step 3: Processing segments...")
            segment_results = []
            
            for i, segment in enumerate(segments):
                try:
                    # Identify speaker
                    speaker_id, confidence, _ = self.speaker_predictor.predict_from_audio(segment, sr)
                    
                    # Determine speaker type
                    is_enumerator = self.speaker_predictor.is_enumerator(speaker_id)
                    speaker_type = 'enumerator' if is_enumerator else 'respondent'
                    
                    # Calculate timestamps
                    start_time = i * segment_duration
                    end_time = start_time + segment_duration
                    
                    segment_results.append({
                        'segment_index': i,
                        'start_time': start_time,
                        'end_time': end_time,
                        'speaker_id': speaker_id,
                        'speaker_type': speaker_type,
                        'confidence': confidence,
                        'audio': segment
                    })
                    
                    print(f"Segment {i}: {speaker_type} (confidence: {confidence:.2f})")
                
                except Exception as e:
                    print(f"Error processing segment {i}: {e}")
                    continue
            
            # Step 4: Group consecutive segments by speaker (speaker diarization)
            print("Step 4: Grouping segments by speaker...")
            grouped_segments = self._group_segments_by_speaker(segment_results)
            
            # Step 5: Transcribe grouped segments
            print("Step 5: Transcribing segments...")
            transcribed_segments = []
            
            for group in grouped_segments:
                try:
                    # Combine audio from group
                    combined_audio = np.concatenate([seg['audio'] for seg in group['segments']])
                    
                    # Save temporary audio file for transcription
                    temp_audio_path = config.TEMP_DIR / f"segment_{interview_id}_{group['group_index']}.wav"
                    save_audio(str(temp_audio_path), combined_audio, sr)
                    
                    # Transcribe
                    transcription = self.transcriber.transcribe(str(temp_audio_path), language='id')
                    
                    # Clean up temp file
                    if temp_audio_path.exists():
                        temp_audio_path.unlink()
                    
                    transcribed_segments.append({
                        'group_index': group['group_index'],
                        'speaker_id': group['speaker_id'],
                        'speaker_type': group['speaker_type'],
                        'start_time': group['start_time'],
                        'end_time': group['end_time'],
                        'confidence': group['avg_confidence'],
                        'transcript': transcription['text'],
                        'language': transcription.get('language', 'id')
                    })
                    
                    print(f"Group {group['group_index']}: {group['speaker_type']} - {transcription['text'][:50]}...")
                
                except Exception as e:
                    print(f"Error transcribing group {group['group_index']}: {e}")
                    continue
            
            # Step 6: Save segments to database (MODIFIED)
            if self.db:
                print("Step 6: Saving segments to database...")
                self._save_segments_to_db(interview_id, audio_path, transcribed_segments)
            
            # Step 7: Generate full transcript for response
            print("Step 7: Generating full transcript...")
            full_transcript = self._generate_full_transcript(transcribed_segments)
            
            # Step 8: Update interview record (MODIFIED)
            if self.db:
                interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
                if interview:
                    # The 'transcript' column is removed from the Interview table.
                    # The full transcript can be generated from the segments when needed.
                    interview.end_time = datetime.now()
                    interview.status = InterviewStatus.COMPLETED
                    self.db.commit()
            
            # Log inference
            self._log_inference(interview_id, len(transcribed_segments), 'success')
            
            return {
                'success': True,
                'interview_id': interview_id,
                'segments_processed': len(segment_results),
                'transcribed_groups': len(transcribed_segments),
                'full_transcript': full_transcript,
                'segments': transcribed_segments
            }
        
        except Exception as e:
            # Log failure
            self._log_inference(interview_id, 0, 'failed', str(e))
            
            # Update interview status
            if self.db:
                interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
                if interview:
                    interview.status = InterviewStatus.FAILED
                    self.db.commit()
            
            return {
                'success': False,
                'interview_id': interview_id,
                'error': str(e)
            }
    
    def _group_segments_by_speaker(self, segments: List[Dict]) -> List[Dict]:
        # This method's logic remains the same.
        if not segments:
            return []
        
        grouped = []
        current_group = {
            'group_index': 0,
            'speaker_id': segments[0]['speaker_id'],
            'speaker_type': segments[0]['speaker_type'],
            'start_time': segments[0]['start_time'],
            'end_time': segments[0]['end_time'],
            'segments': [segments[0]],
            'confidences': [segments[0]['confidence']]
        }
        
        for segment in segments[1:]:
            if segment['speaker_id'] == current_group['speaker_id']:
                current_group['segments'].append(segment)
                current_group['confidences'].append(segment['confidence'])
                current_group['end_time'] = segment['end_time']
            else:
                current_group['avg_confidence'] = np.mean(current_group['confidences'])
                grouped.append(current_group)
                
                current_group = {
                    'group_index': len(grouped),
                    'speaker_id': segment['speaker_id'],
                    'speaker_type': segment['speaker_type'],
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'segments': [segment],
                    'confidences': [segment['confidence']]
                }
        
        current_group['avg_confidence'] = np.mean(current_group['confidences'])
        grouped.append(current_group)
        
        return grouped
    
    def _generate_full_transcript(self, segments: List[Dict]) -> str:
        # This method's logic remains the same.
        transcript_lines = []
        
        for segment in segments:
            speaker_label = "ENUMERATOR" if segment['speaker_type'] == 'enumerator' else "RESPONDENT"
            timestamp = f"[{self._format_timestamp(segment['start_time'])} - {self._format_timestamp(segment['end_time'])}]"
            
            transcript_lines.append(f"{timestamp} {speaker_label}: {segment['transcript']}")
        
        return "\n\n".join(transcript_lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        # This method's logic remains the same.
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    # REWRITTEN METHOD
    def _save_segments_to_db(self, interview_id: int, audio_path: str, segments: List[Dict]):
        """
        Save interview audio file and transcription segments to the database.
        """
        try:
            # Step 1: Create the AudioFile record
            audio_file = AudioFile(
                interview_id=interview_id,
                file_path=audio_path
            )
            self.db.add(audio_file)
            self.db.flush() # Use flush to get the ID before committing

            # Step 2: Create TranscriptionSegment records
            for segment in segments:
                # Map speaker_type to the label used in the DB
                speaker_label = "ENUMERATOR" if segment['speaker_type'] == 'enumerator' else "RESPONDENT"

                db_segment = TranscriptionSegment(
                    audio_file_id=audio_file.id,
                    segment_start=segment['start_time'],
                    segment_end=segment['end_time'],
                    speaker_label=speaker_label,
                    transcription_text=segment['transcript']
                    # 'confidence_score' is not in the new TranscriptionSegment model
                )
                self.db.add(db_segment)
            
            self.db.commit()
            print(f"Saved AudioFile and {len(segments)} transcription segments to database.")
        
        except Exception as e:
            print(f"Error saving segments to database: {e}")
            self.db.rollback() # Rollback on error

    def _log_inference(self, interview_id: int, segments_count: int, 
                      status: str, error: str = None):
        # This method's logic remains the same.
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'interview_id': interview_id,
            'segments_count': segments_count,
            'status': status,
            'error': error
        }
        
        logs = []
        if self.inference_log.exists():
            try:
                with open(self.inference_log, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(log_entry)
        logs = logs[-1000:]
        
        with open(self.inference_log, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def identify_single_speaker(self, audio_path: str) -> Dict:
        # This method's logic remains the same.
        try:
            speaker_id, confidence, probs = self.speaker_predictor.predict_from_file(audio_path)
            
            is_enumerator = self.speaker_predictor.is_enumerator(speaker_id)
            enumerator_name = self.speaker_predictor.get_enumerator_name(speaker_id) if is_enumerator else None
            
            return {
                'success': True,
                'speaker_id': speaker_id,
                'confidence': confidence,
                'is_enumerator': is_enumerator,
                'enumerator_name': enumerator_name,
                'probabilities': probs
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def transcribe_single_audio(self, audio_path: str, 
                                language: str = 'id') -> Dict:
        # This method's logic remains the same.
        try:
            result = self.transcriber.transcribe(audio_path, language=language)
            return result
        
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'error': str(e)
            }
    
    def verify_enumerator(self, audio_path: str, 
                         expected_speaker_id: str,
                         threshold: float = 0.7) -> Dict:
        # This method's logic remains the same.
        try:
            result = self.speaker_predictor.verify_speaker(
                audio_path, 
                expected_speaker_id, 
                threshold
            )
            return {
                'success': True,
                **result
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_inference_stats(self) -> Dict:
        # This method's logic remains the same.
        if not self.inference_log.exists():
            return {
                'total_inferences': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0.0
            }
        
        try:
            with open(self.inference_log, 'r') as f:
                logs = json.load(f)
            
            total = len(logs)
            successful = sum(1 for log in logs if log['status'] == 'success')
            failed = total - successful
            
            return {
                'total_inferences': total,
                'successful': successful,
                'failed': failed,
                'success_rate': successful / total if total > 0 else 0.0,
                'recent_logs': logs[-10:]
            }
        
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def process_real_time_segment(self, audio_segment: np.ndarray, 
                                  sr: int = None) -> Dict:
        # This method's logic remains the same.
        if sr is None:
            sr = config.SAMPLE_RATE
        
        try:
            speaker_id, confidence, _ = self.speaker_predictor.predict_from_audio(audio_segment, sr)
            
            is_enumerator = self.speaker_predictor.is_enumerator(speaker_id)
            speaker_type = 'enumerator' if is_enumerator else 'respondent'
            
            return {
                'success': True,
                'speaker_id': speaker_id,
                'speaker_type': speaker_type,
                'confidence': confidence,
                'is_enumerator': is_enumerator,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # REWRITTEN METHOD
    def generate_interview_summary(self, interview_id: int) -> Dict:
        """
        Generate summary of interview using data from the database.
        """
        if not self.db:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
            if not interview:
                return {'success': False, 'error': 'Interview not found'}

            # Get segments by joining through AudioFile
            audio_file = self.db.query(AudioFile).filter(AudioFile.interview_id == interview.id).first()
            if not audio_file:
                 return {
                    'success': False,
                    'error': 'Audio file for this interview not found.'
                }

            segments = self.db.query(TranscriptionSegment).filter(
                TranscriptionSegment.audio_file_id == audio_file.id
            ).order_by(TranscriptionSegment.segment_start).all()

            # Generate transcript on-the-fly
            transcript_text = self._generate_full_transcript_from_db_segments(segments)

            enumerator_segments = [s for s in segments if s.speaker_label == 'ENUMERATOR']
            respondent_segments = [s for s in segments if s.speaker_label == 'RESPONDENT']
            
            total_duration = max([s.segment_end for s in segments]) if segments else 0
            
            summary = {
                'success': True,
                'interview_id': interview_id,
                'total_duration': total_duration,
                'total_segments': len(segments),
                'enumerator_segments': len(enumerator_segments),
                'respondent_segments': len(respondent_segments),
                'transcript': transcript_text,
                'start_time': interview.start_time.isoformat(),
                'end_time': interview.end_time.isoformat() if interview.end_time else None,
                'status': interview.status.value if interview.status else None
            }
            
            # TODO: Integrate with LLM for more detailed summary
            
            return summary
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ADDED HELPER METHOD
    def _generate_full_transcript_from_db_segments(self, segments: List[TranscriptionSegment]) -> str:
        """
        Generate formatted full transcript from database segment objects.
        """
        transcript_lines = []
        for segment in segments:
            timestamp = f"[{self._format_timestamp(segment.segment_start)} - {self._format_timestamp(segment.segment_end)}]"
            transcript_lines.append(f"{timestamp} {segment.speaker_label}: {segment.transcription_text}")
        return "\n\n".join(transcript_lines)


def process_interview(interview_id: int, audio_path: str, db: Session = None) -> Dict:
    # This function's logic remains the same.
    service = InferenceService(db)
    return service.process_interview_audio(interview_id, audio_path)


if __name__ == "__main__":
    # This part of the script remains the same.
    import sys
    from app.services.db import SessionLocal

    if len(sys.argv) < 3:
        print("Usage: python inference_service.py <interview_id> <audio_file>")
        sys.exit(1)
    
    interview_id = int(sys.argv[1])
    audio_file = sys.argv[2]
    
    db_session = SessionLocal()
    print(f"Processing interview {interview_id}...")
    result = process_interview(interview_id, audio_file, db=db_session)
    db_session.close()
    
    print("\n" + "="*50)
    print("Processing Result:")
    print("="*50)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Segments: {result['segments_processed']}")
        print(f"Transcribed Groups: {result['transcribed_groups']}")
        print(f"\nFull Transcript:")
        print(result['full_transcript'])
