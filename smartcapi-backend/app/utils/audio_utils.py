"""
Audio Processing Utilities untuk SmartCAPI
Menangani preprocessing audio, noise reduction, segmentasi, dll
"""

import os
import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from typing import Tuple, List, Optional, Dict
import noisereduce as nr
from pydub import AudioSegment
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AudioUtils:
    """Utility class untuk processing audio"""
    
    # Default audio parameters
    DEFAULT_SR = 16000  # Sample rate untuk model
    DEFAULT_DURATION = 3.0  # Durasi minimum untuk analisis (detik)
    
    @staticmethod
    def load_audio(
        file_path: str, 
        sr: int = DEFAULT_SR,
        mono: bool = True,
        offset: float = 0.0,
        duration: Optional[float] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Load audio file dengan librosa
        
        Args:
            file_path: Path ke file audio
            sr: Sample rate target
            mono: Convert ke mono jika True
            offset: Start time (detik)
            duration: Durasi yang akan diload (detik)
            
        Returns:
            Tuple (audio_data, sample_rate)
        """
        try:
            audio, sample_rate = librosa.load(
                file_path,
                sr=sr,
                mono=mono,
                offset=offset,
                duration=duration
            )
            
            logger.info(f"Audio loaded: {file_path} | SR: {sample_rate} | Shape: {audio.shape}")
            return audio, sample_rate
            
        except Exception as e:
            logger.error(f"Error loading audio {file_path}: {str(e)}")
            raise
    
    
    @staticmethod
    def save_audio(
        audio: np.ndarray,
        file_path: str,
        sr: int = DEFAULT_SR,
        format: str = 'wav'
    ) -> str:
        """
        Simpan audio ke file
        
        Args:
            audio: Audio data (numpy array)
            file_path: Path output
            sr: Sample rate
            format: Format audio (wav, mp3, dll)
            
        Returns:
            Path file yang tersimpan
        """
        try:
            sf.write(file_path, audio, sr, format=format.upper())
            logger.info(f"Audio saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            raise
    
    
    @staticmethod
    def normalize_audio(audio: np.ndarray, target_db: float = -20.0) -> np.ndarray:
        """
        Normalize audio ke target dB
        
        Args:
            audio: Audio data
            target_db: Target loudness dalam dB
            
        Returns:
            Normalized audio
        """
        try:
            # Hitung RMS
            rms = np.sqrt(np.mean(audio**2))
            
            # Avoid division by zero
            if rms == 0:
                return audio
            
            # Konversi target dB ke linear scale
            target_linear = 10 ** (target_db / 20.0)
            
            # Normalize
            normalized = audio * (target_linear / rms)
            
            # Clip untuk menghindari clipping
            normalized = np.clip(normalized, -1.0, 1.0)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {str(e)}")
            return audio
    
    
    @staticmethod
    def remove_noise(
        audio: np.ndarray,
        sr: int = DEFAULT_SR,
        stationary: bool = True,
        prop_decrease: float = 1.0
    ) -> np.ndarray:
        """
        Noise reduction menggunakan noisereduce library
        
        Args:
            audio: Audio data
            sr: Sample rate
            stationary: Tipe noise (stationary/non-stationary)
            prop_decrease: Proporsi noise reduction (0-1)
            
        Returns:
            Denoised audio
        """
        try:
            # Apply noise reduction
            reduced_noise = nr.reduce_noise(
                y=audio,
                sr=sr,
                stationary=stationary,
                prop_decrease=prop_decrease
            )
            
            logger.info("Noise reduction applied")
            return reduced_noise
            
        except Exception as e:
            logger.error(f"Error removing noise: {str(e)}")
            return audio
    
    
    @staticmethod
    def trim_silence(
        audio: np.ndarray,
        sr: int = DEFAULT_SR,
        top_db: int = 20,
        frame_length: int = 2048,
        hop_length: int = 512
    ) -> np.ndarray:
        """
        Hapus silence di awal dan akhir audio
        
        Args:
            audio: Audio data
            sr: Sample rate
            top_db: Threshold dB untuk silence
            frame_length: Frame length untuk analisis
            hop_length: Hop length
            
        Returns:
            Trimmed audio
        """
        try:
            trimmed, _ = librosa.effects.trim(
                audio,
                top_db=top_db,
                frame_length=frame_length,
                hop_length=hop_length
            )
            
            logger.info(f"Audio trimmed: {len(audio)} -> {len(trimmed)} samples")
            return trimmed
            
        except Exception as e:
            logger.error(f"Error trimming silence: {str(e)}")
            return audio
    
    
    @staticmethod
    def split_audio(
        audio: np.ndarray,
        sr: int = DEFAULT_SR,
        segment_duration: float = 3.0,
        overlap: float = 0.5
    ) -> List[np.ndarray]:
        """
        Split audio menjadi segmen-segmen
        
        Args:
            audio: Audio data
            sr: Sample rate
            segment_duration: Durasi tiap segmen (detik)
            overlap: Overlap antar segmen (detik)
            
        Returns:
            List of audio segments
        """
        try:
            segment_samples = int(segment_duration * sr)
            overlap_samples = int(overlap * sr)
            hop_samples = segment_samples - overlap_samples
            
            segments = []
            
            for start in range(0, len(audio) - segment_samples + 1, hop_samples):
                end = start + segment_samples
                segment = audio[start:end]
                segments.append(segment)
            
            # Handle last segment jika kurang dari segment_duration
            if len(audio) % hop_samples != 0:
                last_segment = audio[-segment_samples:]
                if len(last_segment) == segment_samples:
                    segments.append(last_segment)
            
            logger.info(f"Audio split into {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"Error splitting audio: {str(e)}")
            return [audio]
    
    
    @staticmethod
    def detect_voice_activity(
        audio: np.ndarray,
        sr: int = DEFAULT_SR,
        frame_length: int = 2048,
        hop_length: int = 512,
        energy_threshold: float = 0.01
    ) -> np.ndarray:
        """
        Voice Activity Detection (VAD)
        
        Args:
            audio: Audio data
            sr: Sample rate
            frame_length: Frame length
            hop_length: Hop length
            energy_threshold: Threshold energi untuk voice
            
        Returns:
            Boolean array (True = voice, False = non-voice)
        """
        try:
            # Hitung energy per frame
            energy = librosa.feature.rms(
                y=audio,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # Normalize energy
            energy = energy / np.max(energy)
            
            # Threshold
            voice_activity = energy > energy_threshold
            
            return voice_activity
            
        except Exception as e:
            logger.error(f"Error detecting voice activity: {str(e)}")
            return np.ones(len(audio) // hop_length, dtype=bool)
    
    
    @staticmethod
    def resample_audio(
        audio: np.ndarray,
        orig_sr: int,
        target_sr: int
    ) -> np.ndarray:
        """
        Resample audio ke sample rate berbeda
        
        Args:
            audio: Audio data
            orig_sr: Original sample rate
            target_sr: Target sample rate
            
        Returns:
            Resampled audio
        """
        try:
            if orig_sr == target_sr:
                return audio
            
            resampled = librosa.resample(
                audio,
                orig_sr=orig_sr,
                target_sr=target_sr
            )
            
            logger.info(f"Audio resampled: {orig_sr}Hz -> {target_sr}Hz")
            return resampled
            
        except Exception as e:
            logger.error(f"Error resampling audio: {str(e)}")
            return audio
    
    
    @staticmethod
    def apply_bandpass_filter(
        audio: np.ndarray,
        sr: int = DEFAULT_SR,
        lowcut: float = 300.0,
        highcut: float = 3400.0,
        order: int = 5
    ) -> np.ndarray:
        """
        Apply bandpass filter (untuk voice: 300-3400 Hz)
        
        Args:
            audio: Audio data
            sr: Sample rate
            lowcut: Low cutoff frequency (Hz)
            highcut: High cutoff frequency (Hz)
            order: Filter order
            
        Returns:
            Filtered audio
        """
        try:
            nyquist = 0.5 * sr
            low = lowcut / nyquist
            high = highcut / nyquist
            
            b, a = signal.butter(order, [low, high], btype='band')
            filtered = signal.filtfilt(b, a, audio)
            
            logger.info(f"Bandpass filter applied: {lowcut}-{highcut} Hz")
            return filtered
            
        except Exception as e:
            logger.error(f"Error applying bandpass filter: {str(e)}")
            return audio
    
    
    @staticmethod
    def convert_format(
        input_path: str,
        output_path: str,
        target_format: str = 'wav',
        sr: Optional[int] = None
    ) -> str:
        """
        Convert audio format menggunakan pydub
        
        Args:
            input_path: Input file path
            output_path: Output file path
            target_format: Target format (wav, mp3, dll)
            sr: Target sample rate (optional)
            
        Returns:
            Output file path
        """
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Change sample rate if specified
            if sr:
                audio = audio.set_frame_rate(sr)
            
            # Export
            audio.export(output_path, format=target_format)
            
            logger.info(f"Audio converted: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting audio format: {str(e)}")
            raise
    
    
    @staticmethod
    def get_audio_duration(file_path: str) -> float:
        """
        Dapatkan durasi audio dalam detik
        
        Args:
            file_path: Path ke file audio
            
        Returns:
            Durasi dalam detik
        """
        try:
            audio = AudioSegment.from_file(file_path)
            duration = len(audio) / 1000.0  # Convert ms to seconds
            return duration
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return 0.0
    
    
    @staticmethod
    def get_audio_info(file_path: str) -> Dict[str, any]:
        """
        Dapatkan informasi lengkap audio file
        
        Args:
            file_path: Path ke file audio
            
        Returns:
            Dict dengan info audio
        """
        try:
            audio = AudioSegment.from_file(file_path)
            info = sf.info(file_path)
            
            return {
                "duration": len(audio) / 1000.0,
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "bit_depth": audio.sample_width * 8,
                "format": info.format,
                "subtype": info.subtype,
                "frames": info.frames
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            return {}
    
    
    @staticmethod
    def merge_audio_files(
        file_paths: List[str],
        output_path: str,
        crossfade: int = 0
    ) -> str:
        """
        Merge multiple audio files menjadi satu
        
        Args:
            file_paths: List of audio file paths
            output_path: Output file path
            crossfade: Crossfade duration (ms)
            
        Returns:
            Output file path
        """
        try:
            combined = AudioSegment.empty()
            
            for file_path in file_paths:
                audio = AudioSegment.from_file(file_path)
                
                if len(combined) == 0:
                    combined = audio
                else:
                    if crossfade > 0:
                        combined = combined.append(audio, crossfade=crossfade)
                    else:
                        combined = combined + audio
            
            combined.export(output_path, format='wav')
            
            logger.info(f"Merged {len(file_paths)} audio files -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging audio files: {str(e)}")
            raise
    
    
    @staticmethod
    def preprocess_for_training(
        audio: np.ndarray,
        sr: int = DEFAULT_SR,
        apply_denoise: bool = True,
        apply_normalize: bool = True,
        apply_trim: bool = True
    ) -> np.ndarray:
        """
        Preprocessing pipeline lengkap untuk training
        
        Args:
            audio: Audio data
            sr: Sample rate
            apply_denoise: Apply noise reduction
            apply_normalize: Apply normalization
            apply_trim: Trim silence
            
        Returns:
            Preprocessed audio
        """
        try:
            processed = audio.copy()
            
            # Trim silence
            if apply_trim:
                processed = AudioUtils.trim_silence(processed, sr)
            
            # Denoise
            if apply_denoise:
                processed = AudioUtils.remove_noise(processed, sr)
            
            # Normalize
            if apply_normalize:
                processed = AudioUtils.normalize_audio(processed)
            
            logger.info("Audio preprocessing completed")
            return processed
            
        except Exception as e:
            logger.error(f"Error preprocessing audio: {str(e)}")
            return audio


# Instance untuk digunakan
audio_utils = AudioUtils()