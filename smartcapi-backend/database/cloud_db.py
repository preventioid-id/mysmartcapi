# smartcapi-backend/app/services/db.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Diubah untuk pengembangan lokal. Pastikan Anda memiliki server PostgreSQL yang berjalan.
# Anda mungkin perlu membuat database bernama 'smartcapi_dev' 
# dan menyesuaikan username dan password di bawah ini.
DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost/smartcapi_dev"

# # Koneksi ke database Azure PostgreSQL (KONFIGURASI ASLI)
# # Format: "postgresql+psycopg2://user:password@host/dbname"
# DATABASE_URL = "postgresql+psycopg2://smartcapi-admin:Pr@y2Jesus@db-smartcapi-prod.postgres.database.azure.com/db-smartcapi-prod"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency untuk digunakan di dalam route API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()