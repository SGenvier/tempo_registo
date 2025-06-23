from sqlalchemy import Column, Integer, String, Boolean, Float, Date, Time, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Obra(Base):
    __tablename__ = "obras"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    fase = Column(String, nullable=False)
    semana_embalamento = Column(Integer, nullable=True)
    semana_inicio_corte = Column(Integer, nullable=True)
    semana_embalamento_1 = Column(Integer, nullable=True)
    alteracao_embalamento_1 = Column(DateTime, nullable=True)
    semana_embalamento_2 = Column(Integer, nullable=True)
    alteracao_embalamento_2 = Column(DateTime, nullable=True)
    semana_embalamento_3 = Column(Integer, nullable=True)
    alteracao_embalamento_3 = Column(DateTime, nullable=True)
    semana_embalamento_4 = Column(Integer, nullable=True)
    alteracao_embalamento_4 = Column(DateTime, nullable=True)
    semana_embalamento_5 = Column(Integer, nullable=True)
    alteracao_embalamento_5 = Column(DateTime, nullable=True)
    caixilhos = relationship("Caixilho", back_populates="obra")

class Caixilho(Base):
    __tablename__ = "caixilhos"
    id = Column(Integer, primary_key=True, index=True)
    obra_id = Column(Integer, ForeignKey("obras.id"), nullable=False)
    pp = Column(Integer, nullable=True)
    ano_pp = Column(Integer, nullable=True)
    referencia = Column(String, nullable=True)
    tipologia = Column(String, nullable=True)
    serie = Column(String, nullable=True)
    altura = Column(Float, nullable=True)
    m2 = Column(Float, nullable=True)
    data_caixa = Column(Date, nullable=True)
    largura = Column(Float, nullable=True)
    n_folhas = Column(Integer, nullable=True)
    n_fixos = Column(Integer, nullable=True)
    pocket = Column(Boolean, nullable=True)
    caixa_parede = Column(Boolean, nullable=True)
    mosquiteira = Column(Boolean, nullable=True)
    fecho_prumo = Column(Boolean, nullable=True)
    inox = Column(Boolean, nullable=True)
    alarme = Column(Boolean, nullable=True)
    ventosa = Column(Boolean, nullable=True)
    motorizacao = Column(Boolean, nullable=True)
    n_motores = Column(Integer, nullable=True)
    canto = Column(Boolean, nullable=True)
    sdl = Column(Boolean, nullable=True)
    customizacao = Column(Boolean, nullable=True)
    curvatura = Column(String, nullable=True)

    obra = relationship("Obra", back_populates="caixilhos")
    tempos = relationship("Tempo", back_populates="caixilho")

class Tempo(Base):
    __tablename__ = "tempos"
    id = Column(Integer, primary_key=True, index=True)
    caixilho_id = Column(Integer, ForeignKey("caixilhos.id"), nullable=False)
    estacao = Column(String, nullable=True)
    data_inicio = Column(Date, nullable=True)
    data_fim = Column(Date, nullable=True)
    tempo_execucao = Column(Integer, nullable=True)  # minutos de duração
    operador = Column(String, nullable=True)

    caixilho = relationship("Caixilho", back_populates="tempos")
