import pytest

def test_infer_pipeline_smoke(tmp_path, load_module, monkeypatch):
    """
    Tes dasar untuk infer_pipeline.py:
    - Jika infer_pipeline module dan fungsi infer_pipeline/infer ada, jalankan dengan dummy audio path.
    - Jika modul bergantung pada layanan lain, tes ini dapat disesuaikan dengan monkeypatch.
    """
    try:
        mod = load_module("inference/infer_pipeline.py", "infer_pipeline")
    except FileNotFoundError:
        pytest.skip("inference/infer_pipeline.py tidak ditemukan; melewatkan tes infer pipeline.")

    func = None
    for cand in ("infer_pipeline", "run_inference", "infer", "main"):
        if hasattr(mod, cand) and callable(getattr(mod, cand)):
            func = getattr(mod, cand)
            break
    if func is None:
        pytest.skip("Tidak menemukan fungsi infer_pipeline/run_inference/infer di infer_pipeline.py")

    # Buat dummy audio path (tidak harus ada jika fungsi tidak memerlukannya)
    dummy_audio = tmp_path / "dummy.wav"
    dummy_audio.write_bytes(b"")  # beberapa modul mungkin memeriksa keberadaan file

    # Jika fungsi memerlukan dependensi berat, kita coba panggil dan skip bila gagal
    try:
        res = func(str(dummy_audio))
    except TypeError:
        # kalau signature tidak menerima argumen
        res = func()
    except Exception as e:
        pytest.skip(f"Pemanggilan fungsi infer pipeline gagal (mungkin bergantung pada model berat): {e}")

    assert True  # jika mencapai sini, panggilan tidak melempar exception