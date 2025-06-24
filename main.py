import streamlit as st
from db.database import init_db
import os

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        with st.form("login"):
            st.write("## Login")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            real_password = os.environ.get("TEMPOREGISTO_PASSWORD")
            if submit:
                if real_password and password == real_password:
                    st.session_state["authenticated"] = True
                    st.experimental_rerun()
                else:
                    st.error("Incorrect password")
        st.stop()

check_password()

from db.database import init_db

st.set_page_config(page_title="Registo de Tempos de Produção", layout="centered")
init_db()
st.title("📋 Registo de Tempos")


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
