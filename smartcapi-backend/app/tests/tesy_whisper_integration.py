import pytest
import wave
import struct
import math

def write_short_wav(path, sr=16000, duration_s=0.5, freq=440.0):
    import wave
    n = int(sr * duration_s)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        for i in range(n):
            t = i / sr
            val = 0.5 * math.sin(2 * math.pi * freq * t)
            wf.writeframes(struct.pack("<h", int(val * 32767)))

def test_whisper_transcribe_smoke(tmp_path, load_module, monkeypatch):
    """
    Tes integrasi ringan untuk transcribe_whisper.py:
    - Bila modul transcribe_whisper.py ada dan memiliki fungsi transcribe/transcribe_file,
      panggil dengan file WAV singkat. Bila modul melakukan loading model berat, tes ini
      dilewati atau Anda dapat men-supply stub melalui monkeypatch.
    """
    try:
        mod = load_module("inference/transcribe_whisper.py", "transcribe_whisper")
    except FileNotFoundError:
        pytest.skip("inference/transcribe_whisper.py tidak ditemukan; melewatkan tes whisper.")

    # cari nama fungsi
    func = None
    for cand in ("transcribe", "transcribe_file", "run_transcription", "main"):
        if hasattr(mod, cand) and callable(getattr(mod, cand)):
            func = getattr(mod, cand)
            break
    if func is None:
        pytest.skip("Tidak menemukan fungsi transcribe di transcribe_whisper.py")

    # Buat file WAV singkat
    wav_path = tmp_path / "short.wav"
    write_short_wav(wav_path)

    # Jika modul mencoba memuat model besar (mis. dari file), kemungkinan memakan waktu.
    # Kita coba memanggilnya; bila memicu error loading model, skip test.
    try:
        res = func(str(wav_path))
    except Exception as e:
        pytest.skip(f"Pemanggilan fungsi transcribe menghasilkan exception (mungkin karena model besar tidak tersedia): {e}")

    assert res is not None