import os
import csv
import tempfile
import pytest

def test_train_smoke(tmp_path, load_module):
    """
    Tes 'smoke' untuk modul train.py:
    - Jika modul dan fungsi train ada, jalankan dengan data dummy.
    - Jika tidak, skip.
    """
    try:
        mod = load_module("train.py", "train_module")
    except FileNotFoundError:
        pytest.skip("train.py tidak ditemukan; melewatkan tes training.")

    # Cari fungsi train yang umum
    train_func = None
    for candidate in ("train", "run_training", "train_model", "main"):
        if hasattr(mod, candidate) and callable(getattr(mod, candidate)):
            train_func = getattr(mod, candidate)
            break

    if train_func is None:
        pytest.skip("Tidak menemukan fungsi training yang dikenali di train.py")

    # Buat dataset fitur dummy sebagai CSV (2 baris, 3 fitur + label)
    csv_path = tmp_path / "features_dummy.csv"
    header = ["f1", "f2", "f3", "label"]
    rows = [
        [0.1, 0.2, 0.3, "speaker_a"],
        [0.2, 0.1, 0.4, "speaker_b"],
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    # Panggil fungsi train dengan defensif:
    # Jika signature menerima path, pass path; jika menerima dataframe, lewati.
    try:
        res = train_func(str(csv_path))
    except TypeError:
        # coba tanpa argumen
        res = train_func()

    # Hasil boleh apa saja, tapi tidak boleh menyebabkan exception
    assert True, "Training function executed without raising exception"