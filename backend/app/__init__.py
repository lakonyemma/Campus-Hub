import os
from sqlalchemy import create_engine, text


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def migrate_existing_schema() -> None:
    url = _database_url()
    if not url.startswith("postgresql"):
        return
    engine = create_engine(url, pool_pre_ping=True)
    statements = [
        "ALTER TABLE campus_users ADD COLUMN IF NOT EXISTS university VARCHAR(255)",
        "ALTER TABLE campus_users ADD COLUMN IF NOT EXISTS programme VARCHAR(255)",
        "ALTER TABLE campus_users ADD COLUMN IF NOT EXISTS semester VARCHAR(80)",
        "ALTER TABLE campus_users ADD COLUMN IF NOT EXISTS academic_year VARCHAR(80)",
        "ALTER TABLE campus_users ADD COLUMN IF NOT EXISTS student_number VARCHAR(100)",
        "ALTER TABLE campus_users ADD COLUMN IF NOT EXISTS campus VARCHAR(120)",
    ]
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


migrate_existing_schema()
