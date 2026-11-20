"""Database connection and session management for Project Shikayat Karo."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shikayat_karo.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# For SQLite, check_same_thread=False and timeout=30 allows multi-threaded requests
connect_args = {"check_same_thread": False, "timeout": 30.0} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_database_schema(bind_engine=None):
    """Verifies that all columns declared on models exist in the database,
    adding any missing columns dynamically (e.g. SQLite / PostgreSQL schema evolution).
    """
    from sqlalchemy import inspect, text
    target_engine = bind_engine or engine
    try:
        inspector = inspect(target_engine)
        existing_tables = set(inspector.get_table_names())
        with target_engine.connect() as conn:
            for table_name, table in Base.metadata.tables.items():
                if table_name in existing_tables:
                    existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
                    for col in table.columns:
                        if col.name not in existing_cols:
                            col_type = col.type.compile(target_engine.dialect)
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}"))
                            conn.commit()
    except Exception as e:
        print(f"[Schema Migration Warning] {e}")


def get_db():
    """Dependency that yields a database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
