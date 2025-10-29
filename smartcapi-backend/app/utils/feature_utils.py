"""
Feature Extraction Utilities untuk SmartCAPI
Ekstraksi MFCC dan fitur audio lainnya untuk speaker identification
"""

import numpy as np
import librosa
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureUtils:
    """Utility class untuk ekstraksi fitur audio"""
    
    # Feature extraction parameters
    DEFAULT_N_MFCC = 13
    DEFAULT_N_MELS = 40
    DEFAULT_N_FFT = 2048
    DEFAULT_HOP_LENGTH = 512
    DEFAULT_WIN_LENGTH = 2048
    
    @staticmethod
    def extract_mfcc(
        audio: np.ndarray,
        sr: int = 16000,
        n_mfcc: int = DEFAULT_N_MFCC,
        n_fft: int = DEFAULT_N_FFT,
        hop_length: int = DEFAULT_HOP_LENGTH,
        n_mels: int = DEFAULT_N_MELS
    ) -> np.ndarray:
        """
        Ekstraksi MFCC (Mel-Frequency Cepstral Coefficients)
        
        Args:
            audio: Audio data
            sr: Sample rate
            n_mfcc: Jumlah MFCC coefficients
            n_fft: FFT window size
            hop_length: Hop length
            n_mels: Number of mel bands
            
        Returns:
            MFCC features (n_mfcc, time_frames)
        """
        try:
            mfcc = librosa.feature.mfcc(
                y=audio,
                sr=sr,
                n_mfcc=n_mfcc,
                n_fft=n_fft,
                hop_length=hop_length,
                n_mels=n_mels
            )
            
            return mfcc
            
        except Exception as e:
            logger.error(f"Error extracting MFCC: {str(e)}")
            raise
    
    
    @staticmethod
    def extract_mfcc_stats(
        audio: np.ndarray,
        sr: int = 16000,
        n_mfcc: int = DEFAULT_N_MFCC
    ) -> np.ndarray:
        """
        Ekstraksi MFCC dengan statistik (mean, std, min, max, median)
        Total features: n_mfcc * 5 = 65 features (untuk n_mfcc=13)
        
        Args:
            audio: Audio data
            sr: Sample rate
            n_mfcc: Jumlah MFCC coefficients
            
        Returns:
            Flattened feature vector
        """
        try:
            # Extract MFCC
            mfcc = FeatureUtils.extract_mfcc(audio, sr, n_mfcc)
            
            # Compute statistics across time axis
            mfcc_mean = np.mean(mfcc, axis=1)
            mfcc_std = np.std(mfcc, axis=1)
            mfcc_min = np.min(mfcc, axis=1)
            mfcc_max = np.max(mfcc, axis=1)
            mfcc_median = np.median(mfcc, axis=1)
            
            # Concatenate all statistics
            features = np.concatenate([
                mfcc_mean,
                mfcc_std,
                mfcc_min,
                mfcc_max,
                mfcc_median
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting MFCC stats: {str(e)}")
            raise
    
    
    @staticmethod
    def extract_mfcc_delta(
        audio: np.ndarray,
        sr: int = 16000,
        n_mfcc: int = DEFAULT_N_MFCC
    ) -> np.ndarray:
        """
        Ekstraksi MFCC + Delta + Delta-Delta
        Total features: n_mfcc * 3 = 39 features (untuk n_mfcc=13)
        
        Args:
            audio: Audio data
            sr: Sample rate
            n_mfcc: Jumlah MFCC coefficients
            
        Returns:
            Feature vector dengan MFCC + deltas
        """
        try:
            # Extract MFCC
            mfcc = FeatureUtils.extract_mfcc(audio, sr, n_mfcc)
            
            # Compute deltas
            mfcc_delta = librosa.feature.delta(mfcc)
            mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
            
            # Compute statistics
            mfcc_mean = np.mean(mfcc, axis=1)
            delta_mean = np.mean(mfcc_delta, axis=1)
            delta2_mean = np.mean(mfcc_delta2, axis=1)
            
            # Concatenate
            features = np.concatenate([
                mfcc_mean,
                delta_mean,
                delta2_mean
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting MFCC delta: {str(e)}")
            raise
    
    
    @staticmethod
    def extract_comprehensive_features(
        audio: np.ndarray,
        sr: int = 16000,
        n_mfcc: int = 13
    ) -> np.ndarray:
        """
        Ekstraksi fitur komprehensif untuk speaker identification
        Menghasilkan 33 features:
        - 13 MFCC mean
        - 13 MFCC std
        - 1 Spectral Centroid mean
        - 1 Spectral Bandwidth mean
        - 1 Spectral Rolloff mean
        - 1 Zero Crossing Rate mean
        - 1 RMS Energy mean
        - 1 Chroma mean
        - 1 Tempo
        
        Args:
            audio: Audio data
            sr: Sample rate
            n_mfcc: Jumlah MFCC coefficients
            
        Returns:
            Feature vector (33 features)
        """
        try:
            features = []
            
            # 1. MFCC (mean and std)
            mfcc = FeatureUtils.extract_mfcc(audio, sr, n_mfcc)
            mfcc_mean = np.mean(mfcc, axis=1)
            mfcc_std = np.std(mfcc, axis=1)
            features.extend(mfcc_mean)
            features.extend(mfcc_std)
            
            # 2. Spectral Centroid
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            features.append(np.mean(spectral_centroid))
            
            # 3. Spectral Bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)
            features.append(np.mean(spectral_bandwidth))
            
            # 4. Spectral Rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            features.append(np.mean(spectral_rolloff))
            
            # 5. Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(audio)
            features.append(np.mean(zcr))
            
            # 6. RMS Energy
            rms = librosa.feature.rms(y=audio)
            features.append(np.mean(rms))
            
            # 7. Chroma
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr)
            features.append(np.mean(chroma))
            
            # 8. Tempo
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            features.append(tempo)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error extracting comprehensive features: {str(e)}")
            raise
    
    
    @staticmethod
    def extract_mel_spectrogram(
        audio: np.ndarray,
        sr: int = 16000,
        n_mels: int = 128,
        n_fft: int = DEFAULT_N_FFT,
        hop_length: int = DEFAULT_HOP_LENGTH
    ) -> np.ndarray:
        """
        Ekstraksi Mel Spectrogram
        
        Args:
            audio: Audio data
            sr: Sample rate
            n_mels: Number of mel bands
            n_fft: FFT window size
            hop_length: Hop length
            
        Returns:
            Mel spectrogram
        """
        try:
            mel_spec = librosa.feature.melspectrogram(
                y=audio,
                sr=sr,
                n_mels=n_mels,
                n_fft=n_fft,
                hop_length=hop_length
            )
            
            # Convert to dB scale
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            
            return mel_spec_db
            
        except Exception as e:
            logger.error(f"Error extracting mel spectrogram: {str(e)}")
            raise
    
    
    @staticmethod
    def extract_spectral_features(
        audio: np.ndarray,
        sr: int = 16000
    ) -> Dict[str, float]:
        """
        Ekstraksi berbagai spectral features
        
        Args:
            audio: Audio data
            sr: Sample rate
            
        Returns:
            Dict of spectral features
        """
        try:
            features = {}
            
            # Spectral Centroid
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            features['spectral_centroid_mean'] = np.mean(spectral_centroid)
            features['spectral_centroid_std'] = np.std(spectral_centroid)
            
            # Spectral Bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)
            features['spectral_bandwidth_mean'] = np.mean(spectral_bandwidth)
            features['spectral_bandwidth_std'] = np.std(spectral_bandwidth)
            
            # Spectral Rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            features['spectral_rolloff_mean'] = np.mean(spectral_rolloff)
            features['spectral_rolloff_std'] = np.std(spectral_rolloff)
            
            # Spectral Contrast
            spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
            features['spectral_contrast_mean'] = np.mean(spectral_contrast)
            features['spectral_contrast_std'] = np.std(spectral_contrast)
            
            # Spectral Flatness
            spectral_flatness = librosa.feature.spectral_flatness(y=audio)
            features['spectral_flatness_mean'] = np.mean(spectral_flatness)
            features['spectral_flatness_std'] = np.std(spectral_flatness)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting spectral features: {str(e)}")
            raise
    
    
    @staticmethod
    def extract_prosodic_features(
        audio: np.ndarray,
        sr: int = 16000
    ) -> Dict[str, float]:
        """
        Ekstraksi prosodic features (pitch, energy, rhythm)
        
        Args:
            audio: Audio data
            sr: Sample rate
            
        Returns:
            Dict of prosodic features
        """
        try:
            features = {}
            
            # Pitch (F0) estimation
            pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                features['pitch_mean'] = np.mean(pitch_values)
                features['pitch_std'] = np.std(pitch_values)
                features['pitch_min'] = np.min(pitch_values)
                features['pitch_max'] = np.max(pitch_values)
            else:
                features['pitch_mean'] = 0
                features['pitch_std'] = 0
                features['pitch_min'] = 0
                features['pitch_max'] = 0
            
            # Energy (RMS)
            rms = librosa.feature.rms(y=audio)
            features['energy_mean'] = np.mean(rms)
            features['energy_std'] = np.std(rms)
            
            # Tempo
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            features['tempo'] = tempo
            
            # Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(audio)
            features['zcr_mean'] = np.mean(zcr)
            features['zcr_std'] = np.std(zcr)
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting prosodic features: {str(e)}")
            raise
    
    
    @staticmethod
    def extract_features_from_segments(
        audio: np.ndarray,
        sr: int = 16000,
        segment_duration: float = 3.0,
        overlap: float = 0.5
    ) -> List[np.ndarray]:
        """
        Ekstraksi features dari audio segments
        
        Args:
            audio: Audio data
            sr: Sample rate
            segment_duration: Durasi tiap segmen (detik)
            overlap: Overlap antar segmen (detik)
            
        Returns:
            List of feature vectors
        """
        try:
            from utils.audio_utils import AudioUtils
            
            # Split audio into segments
            segments = AudioUtils.split_audio(audio, sr, segment_duration, overlap)
            
            # Extract features from each segment
            features_list = []
            for segment in segments:
                if len(segment) > sr * 0.5:  # Minimal 0.5 detik
                    features = FeatureUtils.extract_comprehensive_features(segment, sr)
                    features_list.append(features)
            
            return features_list
            
        except Exception as e:
            logger.error(f"Error extracting features from segments: {str(e)}")
            raise
    
    
    @staticmethod
    def normalize_features(
        features: np.ndarray,
        method: str = 'standardize'
    ) -> np.ndarray:
        """
        Normalize feature vector
        
        Args:
            features: Feature vector atau matrix
            method: 'standardize' atau 'minmax'
            
        Returns:
            Normalized features
        """
        try:
            if method == 'standardize':
                # Z-score normalization
                mean = np.mean(features, axis=0)
                std = np.std(features, axis=0)
                std[std == 0] = 1  # Avoid division by zero
                normalized = (features - mean) / std
                
            elif method == 'minmax':
                # Min-max normalization
                min_val = np.min(features, axis=0)
                max_val = np.max(features, axis=0)
                range_val = max_val - min_val
                range_val[range_val == 0] = 1  # Avoid division by zero
                normalized = (features - min_val) / range_val
                
            else:
                normalized = features
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing features: {str(e)}")
            return features
    
    
    @staticmethod
    def compute_feature_statistics(
        features_list: List[np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Compute statistics dari multiple feature vectors
        
        Args:
            features_list: List of feature vectors
            
        Returns:
            Dict dengan mean, std, min, max features
        """
        try:
            features_array = np.array(features_list)
            
            stats = {
                'mean': np.mean(features_array, axis=0),
                'std': np.std(features_array, axis=0),
                'min': np.min(features_array, axis=0),
                'max': np.max(features_array, axis=0),
                'median': np.median(features_array, axis=0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error computing feature statistics: {str(e)}")
            raise


# Instance untuk digunakan
feature_utils = FeatureUtils()