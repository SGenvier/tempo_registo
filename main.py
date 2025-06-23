import streamlit as st
from db.database import init_db

st.set_page_config(page_title="Registo de Tempos de Produção", layout="centered")
init_db()
st.title("📋 Registo de Tempos")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    if st.button("📊 Ver Base de Dados"):
        st.switch_page("pages/base_dados.py")
with col2:
    if st.button("➕ Nova Obra"):
        st.switch_page("pages/registar_obra.py")
with col3:
    if st.button("✏️ Editar Obra"):
        st.switch_page("pages/editar_obra.py")
with col4:
    if st.button("📈 Aferir Tempos"):
        st.switch_page("pages/aferir_tempos.py")

st.markdown("---")
st.info("Selecione uma opção acima.")
