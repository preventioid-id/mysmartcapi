
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

def train_speaker_model(training_data_path: str, model_output_path: str):
    """
    Trains a speaker recognition model using a RandomForestClassifier.

    Args:
        training_data_path (str): The path to the CSV file containing the training data.
                                  The CSV should have a 'Label' column for speaker IDs
                                  and the rest of the columns as features.
        model_output_path (str): The path to save the trained model (.pkl file).
    """
    if not os.path.exists(training_data_path):
        print(f"Error: Training data not found at {training_data_path}")
        return

    # Load the training data
    data = pd.read_csv(training_data_path)

    # Separate features (X) and labels (y)
    X = data.drop('Label', axis=1)
    y = data['Label']

    # Split data for training and validation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Initialize and train the RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, random_state=42, warm_start=False)
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model accuracy after retraining: {accuracy:.2f}")

    # Save the trained model
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    joblib.dump(model, model_output_path)
    print(f"Model successfully retrained and saved to {model_output_path}")

if __name__ == '__main__':
    # Example usage of the training script
    # This part will not be executed when imported in another script
    
    # Define paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    training_data_csv = os.path.join(project_root, "storage", "features", "voices", "training_data.csv")
    model_path = os.path.join(project_root, "models", "rf_model.pkl")

    # Create a dummy training data file for demonstration
    if not os.path.exists(training_data_csv):
        print("Creating dummy training data...")
        dummy_data = {
            'Label': ['user1', 'user1', 'user2', 'user2'],
            'MFCC_1': [0.1, 0.12, 0.8, 0.82],
            'MFCC_2': [0.2, 0.22, 0.7, 0.72],
            # Add more features as in your feature_extraction.py
        }
        for i in range(3, 34):
            dummy_data[f'MFCC_{i}'] = [0.0] * 4
            
        df = pd.DataFrame(dummy_data)
        os.makedirs(os.path.dirname(training_data_csv), exist_ok=True)
        df.to_csv(training_data_csv, index=False)

    # Train the model
    train_speaker_model(training_data_csv, model_path)
