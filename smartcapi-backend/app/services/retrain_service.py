import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import config
from api.database import ModelMetrics
from feature_extraction import FeatureExtractor
from training.train import SpeakerIdentificationTrainer
from services.registration_service import VoiceRegistrationService

class RetrainService:
    """Service for managing model retraining process."""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.feature_extractor = FeatureExtractor()
        self.trainer = SpeakerIdentificationTrainer()
        self.registration_service = VoiceRegistrationService(db)
        self.retrain_history_log = config.RETRAIN_HISTORY_LOG
    
    def check_retrain_needed(self) -> Dict:
        """
        Check if model retrain is needed based on pending registrations.
        
        Returns:
            Dictionary with status and pending count
        """
        pending = self.registration_service.get_pending_retrains()
        
        needs_retrain = len(pending) >= config.MIN_SAMPLES_FOR_RETRAIN
        
        return {
            'needs_retrain': needs_retrain,
            'pending_count': len(pending),
            'threshold': config.MIN_SAMPLES_FOR_RETRAIN,
            'auto_retrain_enabled': config.AUTO_RETRAIN
        }
    
    def extract_new_features(self) -> Dict:
        """
        Extract features from newly registered voice samples.
        
        Returns:
            Dictionary with extraction results
        """
        try:
            print("Extracting features from registration directory...")
            
            # Extract features from registration directory
            df = self.feature_extractor.extract_from_subdirectories(
                config.REGISTRATION_DIR,
                preprocess=True
            )
            
            if df.empty:
                return {
                    'success': False,
                    'message': 'No audio files found in registration directory',
                    'samples_extracted': 0
                }
            
            # Save to enumerator features CSV
            self.feature_extractor.save_features(df, config.FEATURES_ENUMERATOR_CSV)
            
            return {
                'success': True,
                'message': 'Features extracted successfully',
                'samples_extracted': len(df),
                'unique_speakers': len(df['label'].unique())
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Feature extraction failed: {str(e)}',
                'samples_extracted': 0
            }
    
    def combine_all_features(self) -> pd.DataFrame:
        """
        Combine features from all datasets (clean, noisy, enumerator).
        
        Returns:
            Combined DataFrame with all features
        """
        dfs = []
        
        # Load clean features if exists
        if config.FEATURES_CLEAN_CSV.exists():
            df_clean = pd.read_csv(config.FEATURES_CLEAN_CSV)
            dfs.append(df_clean)
            print(f"Loaded {len(df_clean)} samples from clean dataset")
        
        # Load noisy features if exists
        if config.FEATURES_NOISY_CSV.exists():
            df_noisy = pd.read_csv(config.FEATURES_NOISY_CSV)
            dfs.append(df_noisy)
            print(f"Loaded {len(df_noisy)} samples from noisy dataset")
        
        # Load enumerator features if exists
        if config.FEATURES_ENUMERATOR_CSV.exists():
            df_enum = pd.read_csv(config.FEATURES_ENUMERATOR_CSV)
            dfs.append(df_enum)
            print(f"Loaded {len(df_enum)} samples from enumerator dataset")
        
        if not dfs:
            raise ValueError("No feature datasets found")
        
        # Combine all dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates if any
        combined_df = combined_df.drop_duplicates(subset=['filename'], keep='last')
        
        print(f"Total combined samples: {len(combined_df)}")
        print(f"Unique speakers: {len(combined_df['label'].unique())}")
        
        return combined_df
    
    def retrain_model(self, force: bool = False) -> Dict:
        """
        Retrain speaker identification model.
        
        Args:
            force: Force retrain even if not enough new samples
        
        Returns:
            Dictionary with retrain results
        """
        start_time = datetime.now()
        
        try:
            # Check if retrain is needed
            if not force:
                check_result = self.check_retrain_needed()
                if not check_result['needs_retrain']:
                    return {
                        'success': False,
                        'status': 'skipped',
                        'message': f"Not enough new samples. Have {check_result['pending_count']}, need {check_result['threshold']}",
                        'pending_count': check_result['pending_count']
                    }
            
            # Step 1: Extract features from new registrations
            print("Step 1: Extracting features from new registrations...")
            extract_result = self.extract_new_features()
            
            if not extract_result['success']:
                return {
                    'success': False,
                    'status': 'failed',
                    'message': extract_result['message']
                }
            
            # Step 2: Combine all features
            print("Step 2: Combining all feature datasets...")
            combined_df = self.combine_all_features()
            
            # Step 3: Prepare data for training
            print("Step 3: Preparing training data...")
            feature_columns = [col for col in combined_df.columns if col.startswith('mfcc_')]
            X = combined_df[feature_columns].values
            y = combined_df['label'].values
            
            # Step 4: Preprocess data
            print("Step 4: Preprocessing data...")
            X_processed, y_processed = self.trainer.preprocess_data(X, y, fit_encoder=True, fit_scaler=True)
            
            # Step 5: Train model
            print("Step 5: Training Random Forest model...")
            from sklearn.model_selection import train_test_split
            
            X_train, X_test, y_train, y_test = train_test_split(
                X_processed, y_processed, 
                test_size=0.2, 
                random_state=42, 
                stratify=y_processed
            )
            
            self.trainer.train(X_train, y_train, n_estimators=100, max_depth=20)
            
            # Step 6: Evaluate model
            print("Step 6: Evaluating model...")
            train_metrics = self.trainer.evaluate(X_train, y_train)
            test_metrics = self.trainer.evaluate(X_test, y_test)
            
            # Step 7: Save model
            print("Step 7: Saving model...")
            self.trainer.save_model()
            
            # Step 8: Update enumerator list
            print("Step 8: Updating enumerator list...")
            self._update_enumerator_list(combined_df)
            
            # Step 9: Mark registrations as processed
            print("Step 9: Updating registration status...")
            pending = self.registration_service.get_pending_retrains()
            for reg in pending:
                self.registration_service.mark_retrain_complete(reg['speaker_id'])
            
            # Calculate training duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log retrain history
            self._log_retrain(
                train_accuracy=train_metrics['accuracy'],
                test_accuracy=test_metrics['accuracy'],
                n_classes=len(self.trainer.label_encoder.classes_),
                n_samples=len(combined_df),
                duration=duration,
                status='success'
            )
            
            # Save metrics to database
            if self.db:
                self._save_metrics_to_db(train_metrics, test_metrics, len(combined_df))
            
            return {
                'success': True,
                'status': 'completed',
                'message': 'Model retrained successfully',
                'train_accuracy': train_metrics['accuracy'],
                'test_accuracy': test_metrics['accuracy'],
                'n_classes': len(self.trainer.label_encoder.classes_),
                'n_samples': len(combined_df),
                'duration_seconds': duration,
                'new_registrations_processed': len(pending)
            }
        
        except Exception as e:
            # Log failure
            self._log_retrain(
                train_accuracy=0.0,
                test_accuracy=0.0,
                n_classes=0,
                n_samples=0,
                duration=(datetime.now() - start_time).total_seconds(),
                status='failed',
                error_message=str(e)
            )
            
            return {
                'success': False,
                'status': 'failed',
                'message': f'Model retrain failed: {str(e)}'
            }
    
    def _update_enumerator_list(self, df: pd.DataFrame):
        """Update enumerator list JSON with all speakers."""
        enumerator_list = {}
        
        # Group by speaker
        for speaker_id in df['label'].unique():
            speaker_df = df[df['label'] == speaker_id]
            
            enumerator_list[speaker_id] = {
                'speaker_id': speaker_id,
                'n_samples': len(speaker_df),
                'last_updated': datetime.now().isoformat()
            }
        
        # Save to JSON
        with open(config.ENUMERATOR_LIST_PATH, 'w') as f:
            json.dump(enumerator_list, f, indent=2)
        
        print(f"Updated enumerator list with {len(enumerator_list)} speakers")
    
    def _log_retrain(self, train_accuracy: float, test_accuracy: float,
                     n_classes: int, n_samples: int, duration: float,
                     status: str, error_message: str = None):
        """Log retrain history to CSV."""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'n_classes': n_classes,
            'n_samples': n_samples,
            'duration_seconds': duration,
            'error_message': error_message if error_message else ''
        }
        
        # Create or append to CSV
        df = pd.DataFrame([log_data])
        if self.retrain_history_log.exists():
            df.to_csv(self.retrain_history_log, mode='a', header=False, index=False)
        else:
            df.to_csv(self.retrain_history_log, index=False)
    
    def _save_metrics_to_db(self, train_metrics: Dict, test_metrics: Dict, n_samples: int):
        """Save training metrics to database."""
        try:
            metrics = ModelMetrics(
                model_version=self.trainer.metadata.get('model_version', '1.0'),
                accuracy=test_metrics['accuracy'],
                n_classes=self.trainer.metadata.get('n_classes', 0),
                n_samples=n_samples,
                metrics_json=json.dumps({
                    'train_metrics': train_metrics,
                    'test_metrics': test_metrics
                })
            )
            
            self.db.add(metrics)
            self.db.commit()
            print("Metrics saved to database")
        
        except Exception as e:
            print(f"Failed to save metrics to database: {e}")
    
    def get_retrain_history(self, limit: int = 10) -> List[Dict]:
        """
        Get retrain history from log file.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of retrain history records
        """
        if not self.retrain_history_log.exists():
            return []
        
        try:
            df = pd.read_csv(self.retrain_history_log)
            df = df.sort_values('timestamp', ascending=False)
            df = df.head(limit)
            
            return df.to_dict('records')
        
        except Exception as e:
            print(f"Error reading retrain history: {e}")
            return []
    
    def get_model_performance(self) -> Dict:
        """
        Get current model performance metrics.
        
        Returns:
            Dictionary with model performance data
        """
        metadata_path = config.METADATA_PATH
        
        if not metadata_path.exists():
            return {
                'model_exists': False,
                'message': 'Model not trained yet'
            }
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Get latest retrain history
            history = self.get_retrain_history(limit=1)
            latest_retrain = history[0] if history else {}
            
            return {
                'model_exists': True,
                'model_version': metadata.get('model_version'),
                'trained_at': metadata.get('trained_at'),
                'n_classes': metadata.get('n_classes'),
                'n_features': metadata.get('n_features'),
                'classes': metadata.get('classes', []),
                'latest_accuracy': latest_retrain.get('test_accuracy'),
                'latest_retrain': latest_retrain.get('timestamp')
            }
        
        except Exception as e:
            return {
                'model_exists': True,
                'error': f'Failed to load model info: {str(e)}'
            }
    
    def schedule_retrain(self) -> Dict:
        """
        Schedule a retrain task (to be used with Celery).
        
        Returns:
            Dictionary with scheduling result
        """
        from celery_worker import retrain_model_task
        
        # Check if retrain is needed
        check_result = self.check_retrain_needed()
        
        if not check_result['needs_retrain']:
            return {
                'scheduled': False,
                'message': f"Retrain not needed. Pending: {check_result['pending_count']}/{check_result['threshold']}"
            }
        
        # Schedule Celery task
        task = retrain_model_task.delay()
        
        return {
            'scheduled': True,
            'task_id': task.id,
            'message': f"Retrain scheduled with {check_result['pending_count']} pending registrations",
            'pending_count': check_result['pending_count']
        }


def retrain_model(force: bool = False, db: Session = None) -> Dict:
    """
    Convenience function to trigger model retrain.
    
    Args:
        force: Force retrain even if not enough samples
        db: Database session
    
    Returns:
        Retrain result dictionary
    """
    service = RetrainService(db)
    return service.retrain_model(force=force)


def check_and_schedule_retrain(db: Session = None) -> Dict:
    """
    Check if retrain is needed and schedule if necessary.
    
    Args:
        db: Database session
    
    Returns:
        Scheduling result dictionary
    """
    service = RetrainService(db)
    return service.schedule_retrain()


if __name__ == "__main__":
    # Test retrain service
    import sys
    
    force = '--force' in sys.argv
    
    print("Starting model retrain...")
    result = retrain_model(force=force)
    
    print("\n" + "="*50)
    print("Retrain Result:")
    print("="*50)
    for key, value in result.items():
        print(f"{key}: {value}")