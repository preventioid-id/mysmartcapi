import os
import wave
import math
import struct
import numpy as np
import pytest

def write_sine_wav(path, duration_s=1.0, sr=16000, freq=440.0, amp=0.5):
    n = int(sr * duration_s)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sr)
        for i in range(n):
            t = i / sr
            val = amp * math.sin(2 * math.pi * freq * t)
            # 16-bit PCM
            packed = struct.pack("<h", int(val * 32767))
            wf.writeframes(packed)

def find_callable(module, names):
    for n in names:
        if hasattr(module, n):
            attr = getattr(module, n)
            if callable(attr):
                return n, attr
    return None, None

def test_extract_mfcc_basic(tmp_path, load_module):
    wav_path = tmp_path / "tone.wav"
    write_sine_wav(wav_path, duration_s=1.0, sr=16000, freq=440.0)

    try:
        mod = load_module("feature_extraction.py", "feature_extraction")
    except FileNotFoundError:
        pytest.skip("feature_extraction.py tidak ditemukan; melewatkan tes fitur.")

    # Cari fungsi yang umum dipakai untuk ekstraksi MFCC
    candidate_names = [
        "extract_mfcc",
        "extract_features",
        "extract_features_from_file",
        "get_mfcc",
        "mfcc_from_file",
        "main",
    ]
    name, func = find_callable(mod, candidate_names)
    if func is None:
        pytest.skip("Tidak menemukan fungsi ekstraksi MFCC yang dikenali di feature_extraction.py")

    # Panggil fungsi dengan perlakuan defensif: bisa menerima path atau bytes
    try:
        res = func(str(wav_path))
    except TypeError:
        # coba passing path object langsung
        res = func(wav_path)

    # Pastikan hasil bukan None dan mengandung fitur
    assert res is not None, f"{name} mengembalikan None"
    # Jika iterable, pastikan ada elemen
    if hasattr(res, "__len__"):
        assert len(res) > 0, f"{name} mengembalikan koleksi kosong"
    else:
        # bila generator, tarik satu elemen
        first = next(iter(res))
        assert first is not None

    # Jika numpy array, pastikan dimensi masuk akal (tidak 0)
    if isinstance(res, np.ndarray):
        assert res.size > 0