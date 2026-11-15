from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend.app.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Auto-migrate any newly added columns in SQLite
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(generation_jobs)")).fetchall()
            existing_cols = {row[1] for row in result}
            if existing_cols:
                if "rtf" not in existing_cols:
                    conn.execute(text("ALTER TABLE generation_jobs ADD COLUMN rtf FLOAT DEFAULT 0.0"))
                if "chunk_metrics" not in existing_cols:
                    conn.execute(text("ALTER TABLE generation_jobs ADD COLUMN chunk_metrics JSON"))
                if "total_retries" not in existing_cols:
                    conn.execute(text("ALTER TABLE generation_jobs ADD COLUMN total_retries INTEGER DEFAULT 0"))
                if "seed" not in existing_cols:
                    conn.execute(text("ALTER TABLE generation_jobs ADD COLUMN seed INTEGER"))
                conn.commit()
        except Exception:
            pass
