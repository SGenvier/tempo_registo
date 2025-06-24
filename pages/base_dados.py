from sqlalchemy import Engine
import streamlit as st
import pandas as pd
from io import BytesIO
from db.database import Base, SessionLocal, init_db
from db.models import Obra, Caixilho, Tempo
from datetime import date
from collections import defaultdict
import re

# Inicializa o banco de dados
init_db()
st.set_page_config(page_title="Base de Dados", layout="wide")
st.title("📊 Base de Dados")

db = SessionLocal()

# --- Ambiente de busca ---
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    so_obras = st.checkbox("Só obras (HY...)", value=False)
with col2:
    so_concluidos = st.checkbox("Só caixilhos concluídos", value=False)

# --- Query base ---
query = db.query(Caixilho).join(Obra)

# Filtro: só obras HY...
if so_obras:
    query = query.filter(Obra.nome.like("HY%"))

# Filtro: só caixilhos concluídos (alguma data de estação preenchida)
if so_concluidos:
    query = query.filter(
        (Caixilho.data_caixa != None)
        | (db.query(Tempo).filter(Tempo.caixilho_id == Caixilho.id, Tempo.data_inicio != None).exists())
        | (db.query(Tempo).filter(Tempo.caixilho_id == Caixilho.id, Tempo.data_fim != None).exists())
    )

# Obter todas as obras possíveis já filtradas
obras_filtradas = db.query(Obra).join(Caixilho).filter(Caixilho.id.in_([c.id for c in query.all()])).distinct().all()
obras_nomes = sorted(set(o.nome for o in obras_filtradas))

# Dropdown de pesquisa de obra
with col3:
    obra_selecionada = st.selectbox(
        "Selecionar obra específica",
        options=[""] + obras_nomes,
        index=0,
        key="obra_select"
    )

if obra_selecionada:
    query = query.filter(Obra.nome == obra_selecionada)

caixilhos = (
    db.query(Caixilho)
    .order_by(Caixilho.data_caixa.desc())
    .limit(100)
    .all()
)
obras_dict = {o.id: o for o in db.query(Obra).all()}
tempos = db.query(Tempo).filter(Tempo.caixilho_id.in_([c.id for c in caixilhos])).all()
tempos_dict = defaultdict(dict)
for t in tempos:
    tempos_dict[t.caixilho_id][t.estacao] = t

# Função de prioridade para ordenação de obras
def obra_priority(nome):
    if not nome:
        return (3, "")
    prefixos = ["HY", "AS", "AG", "AC", "CC", "RD", "CO", "OS", "CA"]
    nome_upper = nome.upper()
    for i, p in enumerate(prefixos):
        if nome_upper.startswith(p):
            return (0, i, nome_upper)
    if re.match(r"^\d", nome_upper):
        return (2, nome_upper)
    return (1, nome_upper)

# Ordenar por prioridade e nome
caixilhos = sorted(
    caixilhos,
    key=lambda c: obra_priority(obras_dict[c.obra_id].nome if c.obra_id in obras_dict else "")
)

page_size = 20
total = len(caixilhos)
num_pages = (total + page_size - 1) // page_size

if "pagina" not in st.session_state:
    st.session_state["pagina"] = 1

col_pag = st.columns([8,1,1,1,8])
with col_pag[1]:
    if st.session_state["pagina"] > 1:
        if st.button("⬅️", key="anterior"):
            st.session_state["pagina"] -= 1
with col_pag[2]:
    st.write(f"{st.session_state['pagina']} / {num_pages}")
with col_pag[3]:
    if st.session_state["pagina"] < num_pages:
        if st.button("➡️", key="seguinte"):
            st.session_state["pagina"] += 1

# Corrigir página se mudar o filtro
if st.session_state["pagina"] > num_pages:
    st.session_state["pagina"] = num_pages
if st.session_state["pagina"] < 1:
    st.session_state["pagina"] = 1

start = (st.session_state["pagina"] - 1) * page_size
end = start + page_size
caixilhos_page = caixilhos[start:end]

# Tabela
linhas = []
for c in caixilhos_page:
    o = obras_dict.get(c.obra_id)
    linha = {
        "Obra": o.nome if o else "",
        "Fase": o.fase if o else "",
        "PP": c.pp,
        "Ano PP": c.ano_pp,
        "Referência": c.referencia,
        "Tipologia": c.tipologia,
        "Série": c.serie,
        "M2": c.m2,
        "Nº Folhas": c.n_folhas,
        "Nº Fixos": c.n_fixos,
        "Pocket": c.pocket,
        "Caixa Parede": c.caixa_parede,
        "Mosquiteira": c.mosquiteira,
        "Fecho Prumo": c.fecho_prumo,
        "Inox": c.inox,
        "Alarme": c.alarme,
        "Ventosa": c.ventosa,
        "Motorização": c.motorizacao,
        "Nº Motores": c.n_motores,
        "Canto": c.canto,
        "SDL": c.sdl,
        "Customização": c.customizacao,
        "Curvatura": c.curvatura,
        "Data Caixa": c.data_caixa,
    }
    for estacao in ["Corte", "Mec", "Limpeza", "Ass", "Vidro", "Emb", "Mot"]:
        tempo = tempos_dict[c.id].get(estacao)
        tempo_val = tempo.tempo_execucao if tempo else ""
        if hasattr(tempo_val, "strftime"):
            tempo_val = tempo_val.strftime("%H:%M:%S")
        elif isinstance(tempo_val, str) and re.match(r"^\d+:\d+(:\d+)?$", tempo_val):
            pass
        linha[f"Tempo {estacao}"] = tempo_val
        linha[f"Operador {estacao}"] = tempo.operador if tempo else ""
    linhas.append(linha)

df_export = pd.DataFrame(linhas)
st.dataframe(df_export, use_container_width=True)

# Exportação do resultado filtrado (não só da página)
linhas_export = []
for c in caixilhos:
    o = obras_dict.get(c.obra_id)
    linha = {
        "Obra": o.nome if o else "",
        "Fase": o.fase if o else "",
        "PP": c.pp,
        "Ano PP": c.ano_pp,
        "Referência": c.referencia,
        "Tipologia": c.tipologia,
        "Série": c.serie,
        "M2": c.m2,
        "Nº Folhas": c.n_folhas,
        "Nº Fixos": c.n_fixos,
        "Pocket": c.pocket,
        "Caixa Parede": c.caixa_parede,
        "Mosquiteira": c.mosquiteira,
        "Fecho Prumo": c.fecho_prumo,
        "Inox": c.inox,
        "Alarme": c.alarme,
        "Ventosa": c.ventosa,
        "Motorização": c.motorizacao,
        "Nº Motores": c.n_motores,
        "Canto": c.canto,
        "SDL": c.sdl,
        "Customização": c.customizacao,
        "Curvatura": c.curvatura,
        "Data Caixa": c.data_caixa,
    }
    for estacao in ["Corte", "Mec", "Limpeza", "Ass", "Vidro", "Emb", "Mot"]:
        tempo = tempos_dict[c.id].get(estacao)
        linha[f"Tempo {estacao}"] = tempo.tempo_execucao if tempo else ""
        linha[f"Operador {estacao}"] = tempo.operador if tempo else ""
    linhas_export.append(linha)

df_full_export = pd.DataFrame(linhas_export)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button(
    label="⬇️ Descarregar base de dados filtrada (Excel)",
    data=to_excel(df_full_export),
    file_name="base_dados_filtrada.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

db.close()

import openpyxl
try:
    pass
except ImportError:
    pass

def init_db():
    import db.models
    Base.metadata.create_all(bind=Engine)
