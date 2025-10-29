import os
from app import create_app, db
import app.models  # registers models

def recreate_database():
    app = create_app({
        'SQLALCHEMY_DATABASE_URI': os.getenv("DATABASE_URL", "sqlite:///smartcapi.db")
    })
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Done. Database schema created.")

if __name__ == "__main__":
    recreate_database()
