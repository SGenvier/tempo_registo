from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

#DATABASE_URL = "sqlite:///./registo_tempos.db"
db_path = os.environ.get("DB_PATH", "/tmp/tempo_registo.db")
engine = create_engine(f"sqlite:///{db_path}")

#if os.path.exists("registo_tempos.db"):
#    
#    os.remove("registo_tempos.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    import db.models  # regitsa todos os modelos
    Base.metadata.create_all(bind=engine)
