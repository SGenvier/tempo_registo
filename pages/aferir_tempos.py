import streamlit as st
import pandas as pd
from db.database import SessionLocal
from db.models import Obra, Caixilho, Tempo

st.set_page_config(page_title="Aferir Tempos de Produção", layout="wide")
st.title("📈 Aferição de Tempos de Produção")

with st.form("form_relatorio"):
    st.subheader("🔍 Identificação da Obra")
    nome_obra = st.text_input("Nome da Obra*", max_chars=100)
    fase = st.text_input("Fase*", max_chars=100)
    gerar = st.form_submit_button("Gerar Relatório")

if gerar:
    if not nome_obra or not fase:
        st.error("⚠️ Preencha todos os campos obrigatórios.")
        st.stop()

    db = SessionLocal()
    obra = db.query(Obra).filter(Obra.nome == nome_obra, Obra.fase == fase).first()

    if not obra:
        st.error("❌ Obra não encontrada com esses dados.")
        db.close()
        st.stop()

    caixilhos = db.query(Caixilho).filter_by(obra_id=obra.id).all()

    if not caixilhos:
        st.warning("⚠️ Esta obra não tem caixilhos associados.")
        db.close()
        st.stop()

    st.success(f"✅ Obra '{obra.nome}' com {len(caixilhos)} caixilhos encontrados.")

    # Análise dos tempos por caixilho
    st.divider()
    st.subheader("📊 Tempos de Produção por Caixilho")

    resumo = []
    for cx in caixilhos:
        tempos = db.query(Tempo).filter_by(caixilho_id=cx.id).all()
        if not tempos:
            continue

        estacoes = {t.estacao: str(t.tempo_execucao) for t in tempos}
        total = sum([pd.to_timedelta(t.tempo_execucao.strftime('%H:%M:%S')) for t in tempos])
        resumo.append({
            "Referência": cx.referencia,
            "Corte": estacoes.get("Corte", ""),
            "Mecanização": estacoes.get("Mecanização", ""),
            "Limpeza": estacoes.get("Limpeza", ""),
            "Assemblagem": estacoes.get("Assemblagem", ""),
            "Vidro": estacoes.get("Vidro", ""),
            "Embalamento": estacoes.get("Embalamento", ""),
            "Motorização": estacoes.get("Motorização", ""),
            "Total Execução": str(total),
            "Curvatura": cx.curvatura
        })

    if not resumo:
        st.warning("⚠️ Nenhum tempo de produção registado ainda.")
    else:
        df_relatorio = pd.DataFrame(resumo)
        st.dataframe(df_relatorio, use_container_width=True)

    db.close()
