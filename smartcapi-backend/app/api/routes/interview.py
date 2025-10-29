# c:\xampp\htdocs\smartcapi_pwa\smartcapi-backend\app\api\routes\interview.py
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
import shutil
import os
from ..services.db import get_db
from ..model import tables
from ..schemas.interview import InterviewCreate

router = APIRouter()

# Definisikan path untuk menyimpan rekaman
UPLOAD_DIRECTORY = "uploads/interviews"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

import datetime

@router.post("/interviews", status_code=201)
def create_interview(
    db: Session = Depends(get_db),
    nama: str = Form(...),
    alamat: str = Form(...),
    tempat_lahir: str = Form(...),
    tanggal_lahir: str = Form(...),
    usia: int = Form(...),
    pendidikan: str = Form(...),
    pekerjaan: str = Form(...),
    hobi: str = Form(...),
    nomor_telepon: str = Form(...),
    alamat_email: str = Form(...),
    duration: int = Form(...),
    mode: str = Form(...),
    has_recording: str = Form(...),
    audio_file: Optional[UploadFile] = File(None)
):
    """
    Menerima data wawancara dari frontend, memvalidasi, dan menyimpannya ke database.
    Termasuk menangani upload file audio jika ada.
    """
    audio_filename = None
    if audio_file and has_recording == '1':
        # Buat nama file yang aman dengan timestamp Python
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        audio_filename = f"recording-{timestamp}.webm"
        file_path = os.path.join(UPLOAD_DIRECTORY, audio_filename)
        
        # Simpan file audio
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

    # Konversi tanggal lahir dari string "dd/mm/yyyy" ke objek date
    try:
        tgl_lahir_obj = datetime.datetime.strptime(tanggal_lahir, "%d/%m/%Y").date()
    except ValueError:
        # Jika format salah, bisa di-handle dengan error atau nilai default
        raise HTTPException(status_code=400, detail="Invalid date format for tanggal_lahir. Use dd/mm/yyyy.")

    # Konversi dan pemetaan data dari form ke model database
    db_interview = tables.Interview(
        user_id=1, # HARDCODED: Asumsi user dengan ID 1
        name=nama,
        alamat=alamat,
        tempat_lahir=tempat_lahir,
        tanggal_lahir=tgl_lahir_obj,
        usia=usia,
        pendidikan=pendidikan,
        pekerjaan=pekerjaan,
        hobi=hobi,
        nomor_telepon=nomor_telepon,
        alamat_email=alamat_email,
        duration=duration,
        mode='dengan Asistensi AI' if mode == 'AI' else 'tanpa Asistensi AI',
        has_recording=True if has_recording == '1' else False,
        recording_path=audio_filename
    )

    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)

    return {"message": "Interview data submitted successfully!", "data": db_interview}


@router.post("/upload_registration_audio")
def upload_registration_audio(audio: UploadFile = File(...)):
    """
    Mengunggah rekaman suara enumerator berdurasi 3–5 menit untuk pembuatan profil suara.
    """
    # Placeholder for upload logic
    return {"message": "Registration audio uploaded successfully.", "filename": audio.filename}

@router.post("/split_registration_audio")
def split_registration_audio():
    """
    Memecah file audio pendaftaran menjadi beberapa segmen (5–10 detik) untuk ekstraksi fitur.
    """
    # Placeholder for splitting logic
    return {"message": "Registration audio split successfully."}

@router.post("/extract_registration_features")
def extract_registration_features():
    """
    Mengekstraksi fitur MFCC dari setiap segmen audio enumerator dan menambahkan ke dataset model.
    """
    # Placeholder for feature extraction logic
    return {"message": "Registration features extracted successfully."}

@router.post("/retrain_speaker_model")
def retrain_speaker_model():
    """
    Melatih ulang model identifikasi penutur dengan data baru dari enumerator yang mendaftar.
    """
    # Placeholder for retraining logic
    return {"message": "Speaker model retraining initiated."}

@router.post("/new_respondent")
def new_respondent():
    """
    Menambahkan data responden baru sebelum wawancara dimulai.
    """
    # Placeholder for adding new respondent
    return {"message": "New respondent added successfully."}

@router.get("/respondent_list")
def get_respondent_list():
    """
    Menampilkan daftar responden yang telah terdaftar pada akun enumerator.
    """
    # Placeholder for getting respondent list
    return [{"id": 1, "name": "Respondent 1"}, {"id": 2, "name": "Respondent 2"}]

@router.post("/start_interview")
def start_interview():
    """
    Membuat sesi wawancara baru dan mengembalikan session_id unik.
    """
    # Placeholder for starting interview
    return {"session_id": "unique_session_id_123"}

@router.post("/upload_audio_interview")
def upload_audio_interview(audio: UploadFile = File(...)):
    """
    Mengirim rekaman wawancara (audio) ke server untuk diproses.
    """
    # Placeholder for upload logic
    return {"message": "Interview audio uploaded successfully.", "filename": audio.filename}

@router.post("/split_audio_interview")
def split_audio_interview():
    """
    Memecah audio wawancara menjadi potongan 5 detik untuk identifikasi penutur dan transkripsi.
    """
    # Placeholder for splitting logic
    return {"message": "Interview audio split successfully."}

@router.post("/speaker_identification")
def speaker_identification():
    """
    Mengidentifikasi suara penutur (enumerator vs responden) dalam setiap segmen audio.
    """
    # Placeholder for speaker identification logic
    return {"message": "Speaker identification complete."}

@router.post("/speech_to_text")
def speech_to_text():
    """
    Mengubah ucapan responden menjadi teks menggunakan model Whisper.
    """
    # Placeholder for speech to text logic
    return {"transcription": "This is the transcribed text."}

@router.post("/align_text_questionnaire")
def align_text_questionnaire():
    """
    Menyelaraskan hasil transkripsi dengan pertanyaan kuesioner aktif.
    """
    # Placeholder for alignment logic
    return {"message": "Text aligned with questionnaire."}

@router.post("/text_summary")
def text_summary():
    """
    Menghasilkan ringkasan isi jawaban responden dengan LLM untuk membantu enumerator.
    """
    # Placeholder for text summary logic
    return {"summary": "This is a summary of the respondent's answers."}

@router.post("/verify_answer")
def verify_answer():
    """
    Enumerator memverifikasi apakah hasil transkripsi sudah sesuai sebelum disubmit.
    """
    # Placeholder for answer verification
    return {"message": "Answer verified."}

@router.post("/submit_answer")
def submit_answer():
    """
    Mengirim hasil wawancara yang telah diverifikasi ke database utama.
    """
    # Placeholder for submitting answer
    return {"message": "Answer submitted successfully."}

@router.get("/interview_result/{session_id}")
def get_interview_result(session_id: str = Path(...)):
    """
    Menampilkan hasil wawancara lengkap (transkripsi, label penutur, dan ringkasan).
    """
    # Placeholder for getting interview result
    return {"session_id": session_id, "transcription": "...", "speaker_labels": "...", "summary": "..."}

@router.get("/audio_history/{enumerator_id}")
def get_audio_history(enumerator_id: str = Path(...)):
    """
    Menampilkan histori rekaman audio yang pernah diunggah oleh enumerator.
    """
    # Placeholder for getting audio history
    return [{"date": "2025-10-19", "file": "audio1.wav"}, {"date": "2025-10-18", "file": "audio2.wav"}]

@router.post("/feedback")
def submit_feedback():
    """
    Menerima umpan balik enumerator terhadap hasil wawancara berbasis AI.
    """
    # Placeholder for submitting feedback
    return {"message": "Feedback submitted successfully."}

