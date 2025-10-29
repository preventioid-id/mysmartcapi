from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Note:
# - Import models only inside functions or after app creation to avoid circular imports.