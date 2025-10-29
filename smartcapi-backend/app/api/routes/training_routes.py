from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
import json
import config
from api.database import get_db, User, ModelMetrics
from api.routes.auth_routes import get_current_user
from services.registration_service import VoiceRegistrationService
from feature_extraction import extract_all_datasets
from training.train import train_speaker_model

router = APIRouter()

# Pydantic models
class RetrainRequest(BaseModel):
    force: bool = False

class RetrainResponse(BaseModel):
    message: str
    status: str
    task_id: Optional[str] = None

class ModelInfo(BaseModel):
    model_version: str
    trained_at: str
    n_classes: int
    n_features: int
    accuracy: Optional[float] = None

# Routes
@router.post("/retrain", response_model=RetrainResponse)
async def trigger_retrain(
    retrain_data: RetrainRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger model retraining.
    
    If force=True, retrain immediately regardless of pending registrations.
    Otherwise, check if there are enough new registrations to warrant retraining.
    """
    if not current_user.is_enumerator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only enumerators can trigger retraining"
        )
    
    registration_service = VoiceRegistrationService(db)
    pending = registration_service.get_pending_retrains()
    
    if not retrain_data.force and len(pending) < config.MIN_SAMPLES_FOR_RETRAIN:
        return {
            "message": f"Not enough new registrations. Need {config.MIN_SAMPLES_FOR_RETRAIN}, have {len(pending)}",
            "status": "skipped"
        }
    
    # Run training in background
    background_tasks.add_task(retrain_model_task, db)
    
    return {
        "message": "Model retraining started",
        "status": "processing",
        "task_id": None  # In production, use Celery task ID
    }

def retrain_model_task(db: Session):
    """Background task to retrain model."""
    try:
        print("Starting model retraining...")
        
        # Extract features from new registrations
        extract_all_datasets()
        
        # Train model
        train_speaker_model()
        
        # Update registration status
        registration_service = VoiceRegistrationService(db)
        pending = registration_service.get_pending_retrains()
        
        for reg in pending:
            registration_service.mark_retrain_complete(reg['speaker_id'])
        
        # Save metrics to database
        metadata_path = config.METADATA_PATH
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metrics = ModelMetrics(
                model_version=metadata.get('model_version'),
                n_classes=metadata.get('n_classes'),
                n_samples=0,  # TODO: Get from training
                metrics_json=json.dumps(metadata)
            )
            db.add(metrics)
            db.commit()
        
        print("Model retraining completed successfully")
    
    except Exception as e:
        print(f"Error during retraining: {e}")

@router.get("/model/info", response_model=ModelInfo)
async def get_model_info(current_user: User = Depends(get_current_user)):
    """Get current model information."""
    metadata_path = config.METADATA_PATH
    
    if not metadata_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not trained yet"
        )
    
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return {
            "model_version": metadata.get('model_version', 'unknown'),
            "trained_at": metadata.get('trained_at', ''),
            "n_classes": metadata.get('n_classes', 0),
            "n_features": metadata.get('n_features', 0)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model info: {str(e)}"
        )

@router.get("/registrations/stats")
async def get_registration_stats(
    current