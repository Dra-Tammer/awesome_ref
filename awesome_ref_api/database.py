import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_USER = os.getenv("AWESOMEREF_DB_USER", "root")
DB_PASSWORD = os.getenv("AWESOMEREF_DB_PASSWORD", "")
DB_HOST = os.getenv("AWESOMEREF_DB_HOST", "localhost")
DB_PORT = int(os.getenv("AWESOMEREF_DB_PORT", "3306"))
DB_NAME = os.getenv("AWESOMEREF_DB_NAME", "awe_ref")

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
