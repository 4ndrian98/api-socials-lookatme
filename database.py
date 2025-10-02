import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# carica il file .env
load_dotenv()

import urllib.parse

DB_USER = urllib.parse.quote_plus(os.getenv("POSTGRES_USER"))
DB_PASS = urllib.parse.quote_plus(os.getenv("POSTGRES_PASSWORD"))
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("HOST_DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "lookatme")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
