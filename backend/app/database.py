from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class DatabaseManager:
    def __init__(self, db_url: str):
        self.engine = create_engine(
            db_url, connect_args={"check_same_thread": False} # Required for SQLite
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self):
        """Creates database tables."""
        Base.metadata.create_all(bind=self.engine)

    def get_db(self):
        """Dependency generator for FastAPI routes."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

# --- Global Instance ---
# This instance will be imported by other modules.
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
db_manager = DatabaseManager(SQLALCHEMY_DATABASE_URL)
