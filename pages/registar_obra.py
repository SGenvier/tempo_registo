import streamlit as st
from db.database import SessionLocal
from db.models import Obra, Caixilho, Tempo
from datetime import datetime

st.set_page_config(page_title="Nova Obra", layout="centered")
st.title("➕ Nova Obra")

if st.session_state.get("caixilhos_temp", None) is None:
    st.session_state["caixilhos_temp"] = []

with st.form("form_obra"):
    nome = st.text_input("Nome da Obra*", "")
    fase = st.text_input("Fase*", "")
    semana = st.number_input("Semana de Embalamento", min_value=1, max_value=53, step=1)
    ok = st.form_submit_button("Guardar Obra")

if ok:
    if nome and fase:
        db = SessionLocal()
        if db.query(Obra).filter_by(nome=nome, fase=fase).first():
            st.error("❌ Já existe obra com esse nome+fase.")
        else:
            obra = Obra(nome=nome, fase=fase, semana_embalamento=semana)
            db.add(obra); db.commit(); db.refresh(obra)
            st.success(f"Obra '{nome}' criada.")
            st.session_state["obra_id"] = obra.id
        db.close()
    else:
        st.error("Campos obrigatórios em falta.")
