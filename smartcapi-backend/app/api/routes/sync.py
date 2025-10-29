# c:\xampp\htdocs\smartcapi_pwa\smartcapi-backend\app\api\routes\sync.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/sync_mobile")
def sync_mobile():
    """
    Menyinkronkan data wawancara offline ke server ketika koneksi kembali tersedia.
    """
    # Placeholder for sync logic
    return {"message": "Sync completed successfully."}

