import os
from app import create_app, db
import app.models  # registers models

def init_database():
    app = create_app({
        'SQLALCHEMY_DATABASE_URI': os.getenv("DATABASE_URL", "sqlite:///smartcapi.db")
    })
    with app.app_context():
        db.create_all()
        print("Database initialized (tables created if missing).")

if __name__ == "__main__":
    init_database()
