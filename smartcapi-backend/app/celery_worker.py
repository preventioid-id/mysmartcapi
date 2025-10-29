from celery import Celery
from celery.schedules import crontab
import config
from feature_extraction import extract_all_datasets
from training.train import train_speaker_model
from services.registration_service import VoiceRegistrationService
from api.database import SessionLocal

# Create Celery app
celery_app = Celery(
    'smartcapi',
    broker=config.REDIS_URL,
    backend=config.REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Jakarta',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
)

@celery_app.task(name='retrain_model')
def retrain_model_task():
    """
    Background task to retrain speaker identification model.
    
    This task:
    1. Extracts features from new voice registrations
    2. Retrains the Random Forest model
    3. Updates model metadata
    4. Marks registrations as processed
    """
    db = SessionLocal()
    
    try:
        print("Starting model retraining task...")
        
        # Check if there are pending retrains
        registration_service = VoiceRegistrationService(db)
        pending = registration_service.get_pending_retrains()
        
        if len(pending) < config.MIN_SAMPLES_FOR_RETRAIN:
            print(f"Not enough samples for retrain. Have {len(pending)}, need {config.MIN_SAMPLES_FOR_RETRAIN}")
            return {
                'status': 'skipped',
                'message': 'Not enough new registrations'
            }
        
        # Extract features
        print("Extracting features from all datasets...")
        extract_all_datasets()
        
        # Train model
        print("Training model...")
        train_speaker_model()
        
        # Mark registrations as processed
        for reg in pending:
            registration_service.mark_retrain_complete(reg['speaker_id'])
        
        print("Model retraining completed successfully")
        
        return {
            'status': 'success',
            'message': f'Model retrained with {len(pending)} new registrations'
        }
    
    except Exception as e:
        print(f"Error during model retraining: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
    
    finally:
        db.close()

@celery_app.task(name='check_and_retrain')
def check_and_retrain_task():
    """
    Periodic task to check for new registrations and trigger retrain if needed.
    
    This task runs periodically (e.g., every hour) and checks if there are
    enough new voice registrations to warrant retraining the model.
    """
    if not config.AUTO_RETRAIN:
        print("Auto-retrain is disabled")
        return {'status': 'skipped', 'message': 'Auto-retrain disabled'}
    
    db = SessionLocal()
    
    try:
        registration_service = VoiceRegistrationService(db)
        pending = registration_service.get_pending_retrains()
        
        if len(pending) >= config.MIN_SAMPLES_FOR_RETRAIN:
            print(f"Triggering auto-retrain with {len(pending)} pending registrations")
            # Trigger retrain task
            retrain_model_task.delay()
            return {
                'status': 'triggered',
                'message': f'Retrain triggered with {len(pending)} registrations'
            }
        else:
            print(f"Not enough registrations for auto-retrain: {len(pending)}/{config.MIN_SAMPLES_FOR_RETRAIN}")
            return {
                'status': 'waiting',
                'message': f'Waiting for more registrations: {len(pending)}/{config.MIN_SAMPLES_FOR_RETRAIN}'
            }
    
    finally:
        db.close()

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    'check-and-retrain-every-hour': {
        'task': 'check_and_retrain',
        'schedule': crontab(minute=0),  # Every hour
    },
}

if __name__ == '__main__':
    celery_app.start()