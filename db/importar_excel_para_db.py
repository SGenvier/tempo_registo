import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import pandas as pd
from db.database import SessionLocal, init_db
from db.models import Obra, Caixilho, Tempo
from datetime import time, datetime, date

def to_bool(val):
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        v = val.strip().lower()
        if v in ["falso", "false", "não", "nao", "no", "n", "0"]:
            return False
        if v in ["verdadeiro", "true", "sim", "yes", "y", "1"]:
            return True
    return False

def to_time(val):
    if pd.isna(val):
        return None
    if isinstance(val, time):
        return val
    if isinstance(val, pd.Timedelta):
        # Converte Timedelta para time
        total_seconds = int(val.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hours, minutes, seconds)
    if isinstance(val, str):
        # Aceita formatos "HH:MM:SS" ou "H:MM"
        parts = val.strip().split(":")
        if len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
        elif len(parts) == 2:
            return time(int(parts[0]), int(parts[1]), 0)
        elif val.replace('.', '', 1).isdigit():
            # Se vier como decimal de horas (ex: "1.5")
            h = float(val)
            hours = int(h)
            minutes = int(round((h - hours) * 60))
            return time(hours, minutes, 0)
    if isinstance(val, (int, float)):
        # Se vier como número de horas
        hours = int(val)
        minutes = int(round((val - hours) * 60))
        return time(hours, minutes, 0)
    return None

def to_date(val):
    if pd.isna(val):
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        # Tenta vários formatos comuns
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                continue
    return None

def to_minutes(val):
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, pd.Timedelta):
        return int(val.total_seconds() // 60)
    if isinstance(val, str):
        parts = val.strip().split(":")
        if len(parts) == 3:
            return int(int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60)
        elif len(parts) == 2:
            return int(int(parts[0]) * 60 + int(parts[1]))
        elif val.replace('.', '', 1).isdigit():
            # decimal de horas
            return int(float(val) * 60)
    if isinstance(val, (int, float)):
        # assume horas se for float, minutos se for int
        return int(val * 60) if isinstance(val, float) else int(val)
    return None

# Inicializar a base de dados e sessão
init_db()
db = SessionLocal()

# Carregar o Excel (tudo numa só sheet)
df = pd.read_excel("C:\\Users\\stephane.genvier\\Desktop\\Master Kaizen Alumínio (A REPARAR).xlsx", sheet_name="dbKanbans")

for _, row in df.iterrows():
    nome = row.get("OBRA")
    fase = row.get("FASE")
    if pd.isna(nome) or pd.isna(fase):
        continue

    # 1. Criar sempre uma nova obra
    obra = Obra(nome=nome, fase=fase)
    db.add(obra)
    db.commit()
    obra_id = obra.id

    # 2. Criar sempre um novo caixilho
    caixilho = Caixilho(
        obra_id=obra_id,
        referencia=row.get("REFERENCIA"),
        tipologia=row.get("TIPOLOGIA"),
        serie=row.get("SERIE"),
        pp=row.get("PP"),
        ano_pp=row.get("ANO_PP"),
        m2=row.get("M2"),
        n_folhas=int(row.get("N_FOLHAS")) if pd.notnull(row.get("N_FOLHAS")) else None,
        n_fixos=int(row.get("N_FIXOS")) if pd.notnull(row.get("N_FIXOS")) else None,
        pocket=to_bool(row.get("POCKET")),
        caixa_parede=to_bool(row.get("CAIXA_PAREDE")),
        mosquiteira=to_bool(row.get("MOSQUITEIRA")),
        fecho_prumo=to_bool(row.get("FECHO_PRUMO")),
        inox=to_bool(row.get("INOX")),
        alarme=to_bool(row.get("ALARME")),
        ventosa=to_bool(row.get("VENTOSA")),
        motorizacao=to_bool(row.get("MOTORIZACAO")),
        n_motores=int(row.get("N_MOTORES")) if pd.notnull(row.get("N_MOTORES")) else None,
        canto=to_bool(row.get("CANTO")),
        sdl=to_bool(row.get("SDL")),
        customizacao=to_bool(row.get("CUSTOMIZACAO")),
        curvatura=row.get("CURVATURA"),
        data_caixa=to_date(row.get("DIA_CAIXA")),
        altura=row.get("ALTURA"),
        largura=row.get("LARGURA"),
    )
    db.add(caixilho)
    db.commit()
    caixilho_id = caixilho.id

    # 3. Criar tempos para cada estação, se existirem
    estacoes = [
        ("Corte", "DATA_INICIO_CORTE", "DATA_FIM_CORTE", "TEMPO_EXECUCAO_CORTE", "OPERADOR_C"),
        ("Mec", "DATA_INICIO_MECANIZACAO", "DATA_FIM_MECANIZACAO", "TEMPO_EXECUCAO_MECANIZACAO", "OPERADOR_M"),
        ("Limpeza", "DATA_INICIO_LIMPEZA", "DATA_FIM_LIMPEZA", "TEMPO_EXECUCAO_LIMPEZA", "OPERADOR_L"),
        ("Ass", "DATA_INICIO_ASSEMBLAGEM", "DATA_FIM_ASSEMBLAGEM", "TEMPO_EXECUCAO_ASSEMBLAGEM", "OPERADOR_A"),
        ("Vidro", "DATA_INICIO_VIDRO", "DATA_FIM_VIDRO", "TEMPO_EXECUCAO_VIDRO", "OPERADOR_V"),
    ]
    for estacao, col_inicio, col_fim, col_tempo, col_operador in estacoes:
        if pd.notnull(row.get(col_tempo)):
            tempo = Tempo(
                caixilho_id=caixilho_id,
                estacao=estacao,
                data_inicio=to_date(row.get(col_inicio)),
                data_fim=to_date(row.get(col_fim)),
                tempo_execucao=to_minutes(row.get(col_tempo)),  # <-- aqui!
                operador=row.get(col_operador)
            )
            db.add(tempo)

db.commit()
db.close()
print("Migração concluída!")