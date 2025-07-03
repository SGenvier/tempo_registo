from sqlalchemy import Engine
import streamlit as st
import pandas as pd
from io import BytesIO
from db.database import Base, SessionLocal, init_db
from db.models import Obra, Caixilho, Tempo
from datetime import date
from collections import defaultdict
import re

# --- Funções utilitárias ---
def minutos_para_str(minutos):
    if minutos is None or minutos == "":
        return ""
    try:
        minutos = int(minutos)
    except Exception:
        return ""
    h = minutos // 60
    m = minutos % 60
    return f"{h:02}:{m:02}"

def str_para_minutos(s):
    if not s or not isinstance(s, str):
        return 0
    partes = s.strip().split(":")
    try:
        if len(partes) == 2:
            h, m = map(int, partes)
            return h * 60 + m
        elif len(partes) == 3:
            h, m, s = map(int, partes)
            return h * 60 + m + s // 60  # ou ajusta conforme a tua lógica
        else:
            return int(s)
    except Exception:
        return 0

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
if so_obras:
    query = query.filter(Obra.nome.like("HY%"))
if so_concluidos:
    query = query.filter(
        (Caixilho.data_caixa != None)
        | (db.query(Tempo).filter(Tempo.caixilho_id == Caixilho.id, Tempo.data_inicio != None).exists())
        | (db.query(Tempo).filter(Tempo.caixilho_id == Caixilho.id, Tempo.data_fim != None).exists())
    )

# Obter nomes das obras possíveis, já filtradas
obras_query = db.query(Obra).join(Caixilho)
if so_obras:
    obras_query = obras_query.filter(Obra.nome.like("HY%"))
if so_concluidos:
    obras_query = obras_query.filter(
        (Caixilho.data_caixa != None)
        | (db.query(Tempo).filter(Tempo.caixilho_id == Caixilho.id, Tempo.data_inicio != None).exists())
        | (db.query(Tempo).filter(Tempo.caixilho_id == Caixilho.id, Tempo.data_fim != None).exists())
    )
obras_nomes = set(o.nome for o in obras_query.distinct())

def obra_nome_priority(nome):
    if not nome:
        return (2, "")  # vazio no fim
    nome_upper = nome.upper()
    if nome_upper.startswith("HY"):
        return (0, nome_upper)
    if nome_upper[0].isdigit():
        return (1, nome_upper)
    return (0, nome_upper)

obras_nomes = sorted(obras_nomes, key=obra_nome_priority)

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
    query.order_by(Caixilho.data_caixa.desc()).all()
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
    key=lambda c: -int(c.data_caixa.strftime("%Y%m%d")) if c.data_caixa else 0
)

page_size = 100  # Mostra 100 linhas por página
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
        tempo_val = minutos_para_str(tempo.tempo_execucao) if tempo else ""
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

# --- Edição de caixilhos ---
st.subheader("🛠️ Edição de Caixilhos")
cx_id = st.number_input("ID do Caixilho", min_value=1, step=1, format="%d", key="cx_id_edit")
cx = db.query(Caixilho).filter(Caixilho.id == cx_id).first()

if cx:
    obra = obras_dict.get(cx.obra_id)
    st.write(f"**Obra:** {obra.nome if obra else ''}  \n**Fase:** {obra.fase if obra else ''}")
    st.write("---")

    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        st.text_input("PP", value=cx.pp, key="cx_pp_edit")
    with col2:
        st.text_input("Ano PP", value=cx.ano_pp, key="cx_ano_pp_edit")
    with col3:
        st.text_input("Referência", value=cx.referencia, key="cx_referencia_edit")
    with col1:
        st.text_input("Tipologia", value=cx.tipologia, key="cx_tipologia_edit")
    with col2:
        st.text_input("Série", value=cx.serie, key="cx_serie_edit")
    with col3:
        st.text_input("M2", value=cx.m2, key="cx_m2_edit")
    with col1:
        st.text_input("Nº Folhas", value=cx.n_folhas, key="cx_n_folhas_edit")
    with col2:
        st.text_input("Nº Fixos", value=cx.n_fixos, key="cx_n_fixos_edit")
    with col3:
        st.text_input("Pocket", value=cx.pocket, key="cx_pocket_edit")
    with col1:
        st.text_input("Caixa Parede", value=cx.caixa_parede, key="cx_caixa_parede_edit")
    with col2:
        st.text_input("Mosquiteira", value=cx.mosquiteira, key="cx_mosquiteira_edit")
    with col3:
        st.text_input("Fecho Prumo", value=cx.fecho_prumo, key="cx_fecho_prumo_edit")
    with col1:
        st.text_input("Inox", value=cx.inox, key="cx_inox_edit")
    with col2:
        st.text_input("Alarme", value=cx.alarme, key="cx_alarme_edit")
    with col3:
        st.text_input("Ventosa", value=cx.ventosa, key="cx_ventosa_edit")
    with col1:
        st.text_input("Motorização", value=cx.motorizacao, key="cx_motorizacao_edit")
    with col2:
        st.text_input("Nº Motores", value=cx.n_motores, key="cx_n_motores_edit")
    with col3:
        st.text_input("Canto", value=cx.canto, key="cx_canto_edit")
    with col1:
        st.text_input("SDL", value=cx.sdl, key="cx_sdl_edit")
    with col2:
        st.text_input("Customização", value=cx.customizacao, key="cx_customizacao_edit")
    with col3:
        st.text_input("Curvatura", value=cx.curvatura, key="cx_curvatura_edit")
    with col1:
        st.date_input("Data Caixa", value=cx.data_caixa, key="cx_data_caixa_edit")

    st.write("---")
    st.subheader("Tempos por Estação")
    setores = ["Corte", "Mec", "Limpeza", "Ass", "Vidro", "Emb", "Mot"]
    tempos_estacao = {s: tempos_dict[cx.id].get(s) for s in setores}

    for setor, tempo_obj in tempos_estacao.items():
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**{setor}**")
        with col2:
            if tempo_obj:
                st.text_input(
                    f"Duração {setor} (HH:MM ou HH:MM:SS)",
                    value=tempo_obj.tempo_execucao if tempo_obj and tempo_obj.tempo_execucao else "",
                    key=f"{cx.id}{setor}tempo"
                )
            else:
                st.text_input(
                    f"Duração {setor} (HH:MM ou HH:MM:SS)",
                    value="",
                    key=f"{cx.id}{setor}tempo"
                )

    if st.button("Salvar alterações", key="save_caixilho"):
        # Salvar dados do caixilho
        cx.pp = st.session_state.cx_pp_edit
        cx.ano_pp = st.session_state.cx_ano_pp_edit
        cx.referencia = st.session_state.cx_referencia_edit
        cx.tipologia = st.session_state.cx_tipologia_edit
        cx.serie = st.session_state.cx_serie_edit
        cx.m2 = st.session_state.cx_m2_edit
        cx.n_folhas = st.session_state.cx_n_folhas_edit
        cx.n_fixos = st.session_state.cx_n_fixos_edit
        cx.pocket = st.session_state.cx_pocket_edit
        cx.caixa_parede = st.session_state.cx_caixa_parede_edit
        cx.mosquiteira = st.session_state.cx_mosquiteira_edit
        cx.fecho_prumo = st.session_state.cx_fecho_prumo_edit
        cx.inox = st.session_state.cx_inox_edit
        cx.alarme = st.session_state.cx_alarme_edit
        cx.ventosa = st.session_state.cx_ventosa_edit
        cx.motorizacao = st.session_state.cx_motorizacao_edit
        cx.n_motores = st.session_state.cx_n_motores_edit
        cx.canto = st.session_state.cx_canto_edit
        cx.sdl = st.session_state.cx_sdl_edit
        cx.customizacao = st.session_state.cx_customizacao_edit
        cx.curvatura = st.session_state.cx_curvatura_edit
        cx.data_caixa = st.session_state.cx_data_caixa_edit

        # Salvar tempos por estação
        for setor in setores:
            tempo_str = st.session_state.get(f"{cx.id}{setor}tempo", "")
            tempo_obj = tempos_dict[cx.id].get(setor)
            minutos = str_para_minutos(tempo_str)
            if tempo_obj:
                tempo_obj.tempo_execucao = minutos if minutos > 0 else None
            else:
                if minutos > 0:
                    novo_tempo = Tempo(
                        caixilho_id=cx.id,
                        estacao=setor,
                        tempo_execucao=minutos
                    )
                    db.add(novo_tempo)

        db.commit()
        st.success("Alterações salvas com sucesso!")