import os
import sys
import tempfile
import importlib.util
import types
from pathlib import Path

import pytest

def project_root():
    """
    Cari root repository berdasarkan lokasi file tests ini.
    Mengasumsikan struktur:
    <repo-root>/
      smartcapi-backend/
      tests/
    """
    return Path(__file__).resolve().parents[1]

def load_module_from_path(path: Path, name: str) -> types.ModuleType:
    """
    Load a python module from file system path dynamically.
    """
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module

@pytest.fixture(scope="session")
def repo_root():
    return project_root()

@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path

@pytest.fixture(scope="session")
def app_module(repo_root):
    """
    Jika ada smartcapi-backend/app.py, muat modulnya
    dan kembalikan modul. Jika tidak ada, kembalikan None.
    """
    app_path = repo_root / "smartcapi-backend" / "app.py"
    if not app_path.exists():
        pytest.skip("smartcapi-backend/app.py tidak ditemukan; melewatkan tes yang memerlukan app FastAPI.")
    try:
        return load_module_from_path(app_path, "smartcapi_backend_app")
    except Exception as e:
        pytest.skip(f"Gagal memuat app.py: {e}")

@pytest.fixture
def client(app_module):
    """
    Jika app_module memiliki objek FastAPI bernama 'app', buat TestClient.
    Jika tidak ada, skip.
    """
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi TestClient tidak tersedia di environment; melewatkan tes endpoint.")
    fastapi_app = getattr(app_module, "app", None)
    if fastapi_app is None:
        pytest.skip("Tidak menemukan objek 'app' di app.py; melewatkan tes endpoint.")
    return TestClient(fastapi_app)

@pytest.fixture
def load_module(repo_root):
    """
    Fixture helper untuk memuat modul dalam tests menggunakan path relatif ke smartcapi-backend.
    Usage: mod = load_module('feature_extraction.py', 'feature_extraction_module')
    """
    def _loader(rel_path: str, name: str):
        p = repo_root / "smartcapi-backend" / rel_path
        if not p.exists():
            raise FileNotFoundError(f"Module file tidak ditemukan: {p}")
        return load_module_from_path(p, name)
    return _loader