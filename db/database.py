from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = "sqlite:///./registo_tempos.db"

#if os.path.exists("registo_tempos.db"):
#    
#    os.remove("registo_tempos.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    import db.models  # regitsa todos os modelos
    Base.metadata.create_all(bind=engine)
