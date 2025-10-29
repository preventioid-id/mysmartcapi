import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json
import config
from utils.audio_utils import load_audio, save_audio
from inference.infer_speaker import SpeakerPredictor

class DiarizationSegment:
    """Represents a single speaker segment in diarization."""
    
    def __init__(self, start_time: float, end_time: float, 
                 speaker_id: str = None, confidence: float = 0.0):
        self.start_time = start_time
        self.end_time = end_time
        self.speaker_id = speaker_id
        self.confidence = confidence
        self.duration = end_time - start_time
    
    def to_dict(self) -> Dict:
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'speaker_id': self.speaker_id,
            'confidence': self.confidence
        }
    
    def __repr__(self):
        return f"Segment({self.start_time:.2f}s-{self.end_time:.2f}s, {self.speaker_id}, conf={self.confidence:.2f})"


class SpeakerDiarizationService:
    """
    Service for speaker diarization - identifying who spoke when.
    
    This implementation uses:
    1. Fixed-length windowing with overlap
    2. Speaker identification per window using trained RF model
    3. Post-processing to merge consecutive same-speaker segments
    4. Smoothing to remove very short speaker changes
    """
    
    def __init__(self):
        self.speaker_predictor = SpeakerPredictor()
        self.window_size = config.AUDIO_DURATION  # 3.5 seconds
        self.hop_size = 1.0  # 1 second overlap
        self.min_segment_duration = 0.5  # Minimum segment duration in seconds
        self.smoothing_window = 3  # Number of consecutive predictions for smoothing
    
    def diarize_audio_file(self, audio_path: str, 
                          save_segments: bool = False,
                          output_dir: Optional[Path] = None) -> List[DiarizationSegment]:
        """
        Perform speaker diarization on audio file.
        
        Args:
            audio_path: Path to audio file
            save_segments: Whether to save individual speaker segments
            output_dir: Directory to save segments
        
        Returns:
            List of DiarizationSegment objects
        """
        print(f"Starting diarization for: {audio_path}")
        
        # Load audio
        audio, sr = load_audio(audio_path)
        duration = len(audio) / sr
        print(f"Audio duration: {duration:.2f}s")
        
        # Perform diarization
        segments = self.diarize_audio(audio, sr)
        
        # Optionally save segments
        if save_segments and output_dir:
            self._save_speaker_segments(audio, sr, segments, output_dir)
        
        return segments
    
    def diarize_audio(self, audio: np.ndarray, sr: int) -> List[DiarizationSegment]:
        """
        Perform speaker diarization on audio array.
        
        Args:
            audio: Audio signal
            sr: Sample rate
        
        Returns:
            List of DiarizationSegment objects
        """
        # Step 1: Extract windows with overlap
        windows = self._extract_windows(audio, sr)
        print(f"Extracted {len(windows)} windows")
        
        # Step 2: Identify speaker for each window
        window_predictions = []
        for i, (window_audio, start_time, end_time) in enumerate(windows):
            try:
                speaker_id, confidence, _ = self.speaker_predictor.predict_from_audio(
                    window_audio, sr
                )
                window_predictions.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'speaker_id': speaker_id,
                    'confidence': confidence
                })
            except Exception as e:
                print(f"Error predicting window {i}: {e}")
                continue
        
        print(f"Identified speakers for {len(window_predictions)} windows")
        
        # Step 3: Apply smoothing to reduce noise
        smoothed_predictions = self._smooth_predictions(window_predictions)
        
        # Step 4: Merge consecutive same-speaker windows
        segments = self._merge_consecutive_segments(smoothed_predictions)
        
        # Step 5: Remove very short segments
        segments = self._filter_short_segments(segments)
        
        # Step 6: Fill gaps between segments
        segments = self._fill_gaps(segments, len(audio) / sr)
        
        print(f"Final diarization: {len(segments)} segments")
        
        return segments
    
    def _extract_windows(self, audio: np.ndarray, sr: int) -> List[Tuple[np.ndarray, float, float]]:
        """
        Extract overlapping windows from audio.
        
        Args:
            audio: Audio signal
            sr: Sample rate
        
        Returns:
            List of (window_audio, start_time, end_time) tuples
        """
        window_samples = int(self.window_size * sr)
        hop_samples = int(self.hop_size * sr)
        
        windows = []
        start = 0
        
        while start + window_samples <= len(audio):
            window_audio = audio[start:start + window_samples]
            start_time = start / sr
            end_time = (start + window_samples) / sr
            
            windows.append((window_audio, start_time, end_time))
            start += hop_samples
        
        # Add last window if there's remaining audio
        if start < len(audio):
            remaining = audio[start:]
            # Pad if necessary
            if len(remaining) < window_samples:
                remaining = np.pad(remaining, (0, window_samples - len(remaining)))
            start_time = start / sr
            end_time = len(audio) / sr
            windows.append((remaining, start_time, end_time))
        
        return windows
    
    def _smooth_predictions(self, predictions: List[Dict]) -> List[Dict]:
        """
        Apply median filtering to smooth speaker predictions.
        
        Args:
            predictions: List of window predictions
        
        Returns:
            Smoothed predictions
        """
        if len(predictions) < self.smoothing_window:
            return predictions
        
        smoothed = []
        
        for i, pred in enumerate(predictions):
            # Get window of predictions
            start_idx = max(0, i - self.smoothing_window // 2)
            end_idx = min(len(predictions), i + self.smoothing_window // 2 + 1)
            window = predictions[start_idx:end_idx]
            
            # Find most common speaker in window
            speaker_counts = {}
            confidence_sum = {}
            
            for p in window:
                speaker_id = p['speaker_id']
                speaker_counts[speaker_id] = speaker_counts.get(speaker_id, 0) + 1
                confidence_sum[speaker_id] = confidence_sum.get(speaker_id, 0) + p['confidence']
            
            # Choose speaker with most occurrences
            most_common_speaker = max(speaker_counts, key=speaker_counts.get)
            avg_confidence = confidence_sum[most_common_speaker] / speaker_counts[most_common_speaker]
            
            smoothed.append({
                'start_time': pred['start_time'],
                'end_time': pred['end_time'],
                'speaker_id': most_common_speaker,
                'confidence': avg_confidence
            })
        
        return smoothed
    
    def _merge_consecutive_segments(self, predictions: List[Dict]) -> List[DiarizationSegment]:
        """
        Merge consecutive windows with the same speaker.
        
        Args:
            predictions: List of window predictions
        
        Returns:
            List of merged segments
        """
        if not predictions:
            return []
        
        segments = []
        current_segment = {
            'start_time': predictions[0]['start_time'],
            'end_time': predictions[0]['end_time'],
            'speaker_id': predictions[0]['speaker_id'],
            'confidences': [predictions[0]['confidence']]
        }
        
        for pred in predictions[1:]:
            if pred['speaker_id'] == current_segment['speaker_id']:
                # Extend current segment
                current_segment['end_time'] = pred['end_time']
                current_segment['confidences'].append(pred['confidence'])
            else:
                # Finalize current segment
                avg_confidence = np.mean(current_segment['confidences'])
                segments.append(DiarizationSegment(
                    start_time=current_segment['start_time'],
                    end_time=current_segment['end_time'],
                    speaker_id=current_segment['speaker_id'],
                    confidence=avg_confidence
                ))
                
                # Start new segment
                current_segment = {
                    'start_time': pred['start_time'],
                    'end_time': pred['end_time'],
                    'speaker_id': pred['speaker_id'],
                    'confidences': [pred['confidence']]
                }
        
        # Add last segment
        avg_confidence = np.mean(current_segment['confidences'])
        segments.append(DiarizationSegment(
            start_time=current_segment['start_time'],
            end_time=current_segment['end_time'],
            speaker_id=current_segment['speaker_id'],
            confidence=avg_confidence
        ))
        
        return segments
    
    def _filter_short_segments(self, segments: List[DiarizationSegment]) -> List[DiarizationSegment]:
        """
        Remove segments shorter than minimum duration.
        
        Args:
            segments: List of segments
        
        Returns:
            Filtered segments
        """
        filtered = []
        
        for segment in segments:
            if segment.duration >= self.min_segment_duration:
                filtered.append(segment)
            else:
                # Merge short segment with previous or next segment
                if filtered:
                    # Merge with previous
                    filtered[-1].end_time = segment.end_time
                    filtered[-1].duration = filtered[-1].end_time - filtered[-1].start_time
        
        return filtered
    
    def _fill_gaps(self, segments: List[DiarizationSegment], 
                   total_duration: float) -> List[DiarizationSegment]:
        """
        Fill small gaps between segments.
        
        Args:
            segments: List of segments
            total_duration: Total audio duration
        
        Returns:
            Segments with gaps filled
        """
        if not segments:
            return segments
        
        filled = []
        gap_threshold = 0.3  # 300ms
        
        # Add first segment
        filled.append(segments[0])
        
        for i in range(1, len(segments)):
            prev_segment = filled[-1]
            curr_segment = segments[i]
            
            gap = curr_segment.start_time - prev_segment.end_time
            
            if gap < gap_threshold:
                # Fill gap by extending previous segment
                prev_segment.end_time = curr_segment.start_time
                prev_segment.duration = prev_segment.end_time - prev_segment.start_time
            
            filled.append(curr_segment)
        
        return filled
    
    def _save_speaker_segments(self, audio: np.ndarray, sr: int, 
                               segments: List[DiarizationSegment],
                               output_dir: Path):
        """
        Save individual speaker segments to files.
        
        Args:
            audio: Full audio signal
            sr: Sample rate
            segments: List of segments
            output_dir: Directory to save segments
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, segment in enumerate(segments):
            # Extract audio segment
            start_sample = int(segment.start_time * sr)
            end_sample = int(segment.end_time * sr)
            segment_audio = audio[start_sample:end_sample]
            
            # Save segment
            filename = f"segment_{i:03d}_{segment.speaker_id}_{segment.start_time:.2f}-{segment.end_time:.2f}.wav"
            filepath = output_dir / filename
            save_audio(str(filepath), segment_audio, sr)
        
        print(f"Saved {len(segments)} segments to {output_dir}")
    
    def get_speaker_statistics(self, segments: List[DiarizationSegment]) -> Dict:
        """
        Calculate statistics for each speaker.
        
        Args:
            segments: List of segments
        
        Returns:
            Dictionary with speaker statistics
        """
        stats = {}
        
        for segment in segments:
            speaker_id = segment.speaker_id
            
            if speaker_id not in stats:
                stats[speaker_id] = {
                    'total_duration': 0.0,
                    'num_segments': 0,
                    'avg_confidence': 0.0,
                    'confidences': []
                }
            
            stats[speaker_id]['total_duration'] += segment.duration
            stats[speaker_id]['num_segments'] += 1
            stats[speaker_id]['confidences'].append(segment.confidence)
        
        # Calculate averages
        for speaker_id in stats:
            confidences = stats[speaker_id]['confidences']
            stats[speaker_id]['avg_confidence'] = np.mean(confidences)
            stats[speaker_id]['min_confidence'] = np.min(confidences)
            stats[speaker_id]['max_confidence'] = np.max(confidences)
            del stats[speaker_id]['confidences']
        
        return stats
    
    def export_diarization(self, segments: List[DiarizationSegment], 
                          output_path: Path, format: str = 'json'):
        """
        Export diarization results to file.
        
        Args:
            segments: List of segments
            output_path: Output file path
            format: Export format ('json', 'rttm', 'txt')
        """
        if format == 'json':
            self._export_json(segments, output_path)
        elif format == 'rttm':
            self._export_rttm(segments, output_path)
        elif format == 'txt':
            self._export_txt(segments, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, segments: List[DiarizationSegment], output_path: Path):
        """Export as JSON."""
        data = {
            'segments': [seg.to_dict() for seg in segments],
            'statistics': self.get_speaker_statistics(segments),
            'total_segments': len(segments),
            'export_time': datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Exported diarization to {output_path}")
    
    def _export_rttm(self, segments: List[DiarizationSegment], output_path: Path):
        """
        Export as RTTM (Rich Transcription Time Marked) format.
        Format: SPEAKER <file> 1 <start> <duration> <NA> <NA> <speaker> <conf>
        """
        lines = []
        filename = output_path.stem
        
        for segment in segments:
            line = f"SPEAKER {filename} 1 {segment.start_time:.3f} {segment.duration:.3f} <NA> <NA> {segment.speaker_id} {segment.confidence:.3f}"
            lines.append(line)
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"Exported RTTM to {output_path}")
    
    def _export_txt(self, segments: List[DiarizationSegment], output_path: Path):
        """Export as human-readable text."""
        lines = []
        lines.append("Speaker Diarization Results")
        lines.append("=" * 50)
        lines.append("")
        
        for i, segment in enumerate(segments, 1):
            lines.append(f"{i}. [{self._format_time(segment.start_time)} - {self._format_time(segment.end_time)}]")
            lines.append(f"   Speaker: {segment.speaker_id}")
            lines.append(f"   Duration: {segment.duration:.2f}s")
            lines.append(f"   Confidence: {segment.confidence:.2f}")
            lines.append("")
        
        # Add statistics
        stats = self.get_speaker_statistics(segments)
        lines.append("=" * 50)
        lines.append("Speaker Statistics")
        lines.append("=" * 50)
        lines.append("")
        
        for speaker_id, speaker_stats in stats.items():
            lines.append(f"Speaker: {speaker_id}")
            lines.append(f"  Total Duration: {speaker_stats['total_duration']:.2f}s")
            lines.append(f"  Number of Segments: {speaker_stats['num_segments']}")
            lines.append(f"  Average Confidence: {speaker_stats['avg_confidence']:.2f}")
            lines.append("")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"Exported text report to {output_path}")
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS.mmm"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:06.3f}"
    
    def real_time_diarization(self, audio_chunk: np.ndarray, 
                             sr: int,
                             previous_speaker: Optional[str] = None) -> Dict:
        """
        Perform quick speaker identification for real-time streaming.
        
        Args:
            audio_chunk: Audio chunk (should be ~3.5s)
            sr: Sample rate
            previous_speaker: Previous speaker ID for continuity
        
        Returns:
            Dictionary with speaker identification results
        """
        try:
            speaker_id, confidence, _ = self.speaker_predictor.predict_from_audio(audio_chunk, sr)
            
            # Check if speaker changed
            speaker_changed = previous_speaker is not None and speaker_id != previous_speaker
            
            # Determine speaker type
            is_enumerator = self.speaker_predictor.is_enumerator(speaker_id)
            speaker_type = 'enumerator' if is_enumerator else 'respondent'
            
            return {
                'success': True,
                'speaker_id': speaker_id,
                'speaker_type': speaker_type,
                'confidence': confidence,
                'speaker_changed': speaker_changed,
                'is_enumerator': is_enumerator,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def diarize_audio(audio_path: str, output_dir: Optional[str] = None) -> List[DiarizationSegment]:
    """
    Convenience function to perform speaker diarization.
    
    Args:
        audio_path: Path to audio file
        output_dir: Optional directory to save segments
    
    Returns:
        List of DiarizationSegment objects
    """
    service = SpeakerDiarizationService()
    output_path = Path(output_dir) if output_dir else None
    return service.diarize_audio_file(audio_path, save_segments=bool(output_dir), output_dir=output_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python diarization_service.py <audio_file> [output_dir]")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("Starting speaker diarization...")
    segments = diarize_audio(audio_file, output_dir)
    
    print("\n" + "="*50)
    print("Diarization Results:")
    print("="*50)
    
    for i, segment in enumerate(segments, 1):
        print(f"{i}. {segment}")
    
    # Calculate statistics
    service = SpeakerDiarizationService()
    stats = service.get_speaker_statistics(segments)
    
    print("\n" + "="*50)
    print("Speaker Statistics:")
    print("="*50)
    for speaker_id, speaker_stats in stats.items():
        print(f"\nSpeaker: {speaker_id}")
        print(f"  Total Duration: {speaker_stats['total_duration']:.2f}s")
        print(f"  Segments: {speaker_stats['num_segments']}")
        print(f"  Avg Confidence: {speaker_stats['avg_confidence']:.2f}")