from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# CHANGED: SQLite URL -> PostgreSQL URL
DATABASE_URL = "postgresql+psycopg2://postgres:123@127.0.0.1:5433/apartment_rental"

# CHANGED: added pool_pre_ping=True for more stable PostgreSQL connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
