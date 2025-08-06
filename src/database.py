import sqlalchemy
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = sqlalchemy.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    return SessionLocal()