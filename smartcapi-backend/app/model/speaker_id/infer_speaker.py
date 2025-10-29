# model/speaker_id/infer_speaker.py
import joblib
import numpy as np
import os

# Build absolute paths to the model and scaler files relative to this script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "random_forest_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "feature_scaler.pkl")

# Load model dan scaler
rf_model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

def identify_speaker(mfcc_features: np.ndarray) -> str:
    """
    Menerima array MFCC (33 fitur) dan mengembalikan ID penutur.
    """
    mfcc_scaled = scaler.transform([mfcc_features])
    speaker_id = rf_model.predict(mfcc_scaled)[0]
    return str(speaker_id)
