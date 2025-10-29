# c:\xampp\htdocs\smartcapi_pwa\smartcapi-backend\app\api\routes\dashboard.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard_summary")
def get_dashboard_summary():
    """
    Menampilkan rekapitulasi hasil wawancara dan status data yang telah dikirim.
    """
    # Placeholder for dashboard summary logic
    return {"interviews_conducted": 10, "data_synced": 8}

@router.get("/dashboard_metrics")
def get_dashboard_metrics():
    """
    Menampilkan metrik agregat wawancara (jumlah responden, durasi, tingkat error transkripsi, dsb).
    """
    # Placeholder for dashboard metrics logic
    return {"total_respondents": 25, "avg_duration": "15 mins", "transcription_error_rate": "5%"}

