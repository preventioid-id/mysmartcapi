import numpy as np
import joblib
import json
from pathlib import Path
from typing import Tuple, Dict
import config
from utils.audio_utils import load_audio, preprocess_audio
from utils.feature_utils import extract_all_features

class SpeakerPredictor:
    """Predict speaker identity from audio using trained model."""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.metadata = None
        self.enumerator_list = None
        self.load_model()
        self.load_enumerator_list()
    
    def load_model(self, model_path: Path = None,
                   scaler_path: Path = None,
                   metadata_path: Path = None):
        """Load trained model, scaler, and metadata."""
        if model_path is None:
            model_path = config.MODEL_PATH
        if scaler_path is None:
            scaler_path = config.SCALER_PATH
        if metadata_path is None:
            metadata_path = config.METADATA_PATH
        
        try:
            # Load model
            self.model = joblib.load(model_path)
            
            # Load scaler and label encoder
            scaler_data = joblib.load(scaler_path)
            self.scaler = scaler_data['scaler']
            self.label_encoder = scaler_data['label_encoder']
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            
            print("Model loaded successfully")
        except FileNotFoundError as e:
            print(f"Model files not found: {e}")
            print("Please train the model first")
    
    def load_enumerator_list(self, path: Path = None):
        """Load enumerator list mapping."""
        if path is None:
            path = config.ENUMERATOR_LIST_PATH
        
        try:
            with open(path, 'r') as f:
                self.enumerator_list = json.load(f)
        except FileNotFoundError:
            self.enumerator_list = {}
            print("Enumerator list not found, creating empty list")
    
    def predict_from_audio(self, audio: np.ndarray, sr: int = None) -> Tuple[str, float, Dict]:
        """
        Predict speaker from audio signal.
        
        Args:
            audio: Audio signal
            sr: Sample rate
        
        Returns:
            Tuple of (predicted_speaker, confidence, probabilities_dict)
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        # Extract features
        features = extract_all_features(audio, sr)
        features = features.reshape(1, -1)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Get speaker label
        speaker_id = self.label_encoder.inverse_transform([prediction])[0]
        confidence = probabilities[prediction]
        
        # Get all probabilities
        prob_dict = {}
        for i, label in enumerate(self.label_encoder.classes_):
            prob_dict[label] = float(probabilities[i])
        
        return speaker_id, float(confidence), prob_dict
    
    def predict_from_file(self, file_path: str, 
                         preprocess: bool = True) -> Tuple[str, float, Dict]:
        """
        Predict speaker from audio file.
        
        Args:
            file_path: Path to audio file
            preprocess: Whether to preprocess audio
        
        Returns:
            Tuple of (predicted_speaker, confidence, probabilities_dict)
        """
        # Load audio
        if preprocess:
            audio, sr = preprocess_audio(file_path)
        else:
            audio, sr = load_audio(file_path)
        
        return self.predict_from_audio(audio, sr)
    
    def is_enumerator(self, speaker_id: str) -> bool:
        """Check if predicted speaker is a registered enumerator."""
        return speaker_id in self.enumerator_list
    
    def get_enumerator_name(self, speaker_id: str) -> str:
        """Get enumerator name from ID."""
        return self.enumerator_list.get(speaker_id, "Unknown")
    
    def verify_speaker(self, file_path: str, 
                      expected_speaker: str,
                      threshold: float = 0.7) -> Dict:
        """
        Verify if audio matches expected speaker.
        
        Args:
            file_path: Path to audio file
            expected_speaker: Expected speaker ID
            threshold: Confidence threshold for verification
        
        Returns:
            Dictionary with verification results
        """
        speaker_id, confidence, probs = self.predict_from_file(file_path)
        
        is_match = speaker_id == expected_speaker
        is_verified = is_match and confidence >= threshold
        
        return {
            'predicted_speaker': speaker_id,
            'expected_speaker': expected_speaker,
            'confidence': confidence,
            'is_match': is_match,
            'is_verified': is_verified,
            'threshold': threshold,
            'all_probabilities': probs
        }
    
    def get_model_info(self) -> Dict:
        """Get model metadata and information."""
        if self.metadata is None:
            return {}
        
        return {
            'model_version': self.metadata.get('model_version'),
            'trained_at': self.metadata.get('trained_at'),
            'n_classes': self.metadata.get('n_classes'),
            'classes': self.metadata.get('classes'),
            'n_features': self.metadata.get('n_features')
        }

def predict_speaker(audio_file: str) -> Dict:
    """
    Convenience function to predict speaker from audio file.
    
    Args:
        audio_file: Path to audio file
    
    Returns:
        Dictionary with prediction results
    """
    predictor = SpeakerPredictor()
    speaker_id, confidence, probs = predictor.predict_from_file(audio_file)
    
    is_enumerator = predictor.is_enumerator(speaker_id)
    enumerator_name = predictor.get_enumerator_name(speaker_id) if is_enumerator else None
    
    return {
        'speaker_id': speaker_id,
        'confidence': confidence,
        'is_enumerator': is_enumerator,
        'enumerator_name': enumerator_name,
        'probabilities': probs
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python infer_speaker.py <audio_file>")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    result = predict_speaker(audio_file)
    
    print("\nPrediction Result:")
    print(f"Speaker ID: {result['speaker_id']}")
    print(f"Confidence: {result['confidence']:.4f}")
    print(f"Is Enumerator: {result['is_enumerator']}")
    if result['enumerator_name']:
        print(f"Enumerator Name: {result['enumerator_name']}")