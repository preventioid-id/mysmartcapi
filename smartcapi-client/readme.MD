# SmartCAPI Backend - Python Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env dengan konfigurasi Anda
```

### 3. Run Server

```bash
# Development mode (auto-reload)
python app.py

# atau dengan uvicorn langsung
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Server akan berjalan di: **http://127.0.0.1:8000**

## 📁 Struktur Project

```
backend/
├── app.py                      # Main application
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── .env.example               # Environment template
│
├── models/                    # Database models
│   ├── __init__.py
│   ├── interview.py
│   ├── speaker.py
│   └── transcription.py
│
├── database/
│   ├── cloud_db.py           # Database connection
│   └── sync_manager.py       # Sync logic
│
├── services/
│   ├── sync_service.py       # Batch sync handler
│   └── whisper_service.py    # Transcription service
│
└── uploads/                  # File uploads
    ├── voices/              # Voice registrations
    └── interviews/          # Interview recordings
```

## 🔌 API Endpoints

### Health Check
```http
GET /api/health
HEAD /api/health
```

### Voice Registration
```http
POST /api/register-voice
Content-Type: multipart/form-data

Fields:
- user_name: string
- duration: integer
- audio_file: file
```

### Interview Submission
```http
POST /api/interviews
Content-Type: multipart/form-data

Fields:
- nama, alamat, tempat_lahir, tanggal_lahir
- usia, pendidikan, pekerjaan, hobi
- nomor_telepon, alamat_email
- duration, mode, has_recording
- audio_file: file (optional)
```

### Batch Sync (Service Worker)
```http
POST /api/sync
Content-Type: application/json

Body:
{
  "items": [
    {
      "uuid": "...",
      "sync_status": "pending",
      "timestamp": "...",
      ...
    }
  ]
}
```

## 🧪 Testing Endpoints

### Menggunakan curl:

```bash
# Test health check
curl http://127.0.0.1:8000/api/health

# Test voice registration
curl -X POST http://127.0.0.1:8000/api/register-voice \
  -F "user_name=Test User" \
  -F "duration=10" \
  -F "audio_file=@test.webm"

# Test interview submission
curl -X POST http://127.0.0.1:8000/api/interviews \
  -F "nama=John Doe" \
  -F "alamat=Jakarta" \
  -F "tempat_lahir=Jakarta" \
  -F "tanggal_lahir=01/01/1990" \
  -F "usia=34" \
  -F "pendidikan=SMA" \
  -F "pekerjaan=Developer" \
  -F "hobi=Coding" \
  -F "nomor_telepon=081234567890" \
  -F "alamat_email=john@example.com" \
  -F "duration=300" \
  -F "mode=AI" \
  -F "has_recording=1" \
  -F "audio_file=@recording.webm"
```

### Menggunakan Python:

```python
import requests

# Test health check
response = requests.get('http://127.0.0.1:8000/api/health')
print(response.json())

# Test voice registration
files = {'audio_file': open('test.webm', 'rb')}
data = {'user_name': 'Test User', 'duration': 10}
response = requests.post('http://127.0.0.1:8000/api/register-voice', 
                        files=files, data=data)
print(response.json())
```

## 📊 Monitoring Logs

Saat server berjalan, Anda akan melihat log seperti:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.

✅ Voice registered: Budi Sanjaya - voice_abc123.webm (10s)
✅ Interview submitted: John Doe - Mode: AI - Duration: 300s
🔄 Sync completed: 5 synced, 0 failed
```

## 🔒 Production Deployment

### 1. Update CORS Origins

```python
# app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    # ...
)
```

### 2. Use Production ASGI Server

```bash
pip install gunicorn

gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 3. Setup Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐳 Docker Support (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t smartcapi-backend .
docker run -p 8000:8000 smartcapi-backend
```

## 🆘 Troubleshooting

### Port sudah digunakan
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### CORS Error
- Pastikan origin frontend ada di CORS configuration
- Check browser console untuk detail error

### Upload File Gagal
- Check folder permissions untuk `uploads/`
- Verify `MAX_UPLOAD_SIZE_MB` di konfigurasi

## 📚 Next Steps

1. Implementasi database models di `models/`
2. Setup database connection di `database/cloud_db.py`
3. Implementasi Whisper transcription di `services/whisper_service.py`
4. Add authentication & authorization
5. Setup cloud storage (S3/GCS) untuk production

## 📞 Support

Jika ada pertanyaan atau issue, silakan buka issue di repository atau kontak tim development.