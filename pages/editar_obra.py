import streamlit as st
from db.database import SessionLocal
from db.models import Obra, Caixilho, Tempo
from datetime import datetime, date, time as time_default, time

st.set_page_config(page_title="Editar Obra", layout="wide")
db = SessionLocal()
st.title("🛠️ Editar Obra e Caixilhos")

# 1) Cabeçalho
# Obter todas as combinações únicas de (nome, fase)
obras_tuplos = sorted(set((o.nome, o.fase) for o in db.query(Obra).all()))
if not obras_tuplos:
    st.warning("⚠️ Nenhuma obra registada.")
    st.stop()

c1, c2, c3 = st.columns([3,1,1])
obra_fase = c1.selectbox(
    "Obra (Fase)",
    obras_tuplos,
    format_func=lambda t: f"{t[0]} ({t[1]})"
)
semana_atual = c2.number_input("Semana", value=1, min_value=1, max_value=53)
# Encontrar todas as obras com esse nome e fase
obras = db.query(Obra).filter_by(nome=obra_fase[0], fase=obra_fase[1]).all()
obra = obras[0]  # Usar a primeira para editar semana, etc.

if c3.button("Salvar Semana"):
    if obra.semana_embalamento != semana_atual:
        for i in range(5, 1, -1):
            setattr(obra, f"semana_embalamento_{i}", getattr(obra, f"semana_embalamento_{i-1}"))
            setattr(obra, f"alteracao_embalamento_{i}", getattr(obra, f"alteracao_embalamento_{i-1}"))
        obra.semana_embalamento_1 = semana_atual
        obra.alteracao_embalamento_1 = datetime.now()
        obra.semana_embalamento = semana_atual
        db.commit()
        st.success("Semana guardada")
        st.rerun()
    else:
        st.info("A semana de embalamento não foi alterada.")

st.markdown(f"### 🧾 Obra: {obra.nome} — {obra.fase}")

# Botão para adicionar caixilho (toggle)
if st.session_state.get("novo"):
    if st.button("❌ Fechar Novo"):
        st.session_state.pop("novo")
        st.rerun()
else:
    if st.button("➕ Adicionar Caixilho"):
        st.session_state["novo"] = True
        st.session_state.pop("editar", None)
        st.session_state.pop("tempos", None)
        st.rerun()

# Função para garantir tipo time para st.time_input
def to_time(val):
    if val is None:
        return time(0, 0)
    if isinstance(val, time):
        return val
    if isinstance(val, int):
        return time(val // 60, val % 60)
    if isinstance(val, float):
        total_minutes = int(val * 60)
        return time(total_minutes // 60, total_minutes % 60)
    if isinstance(val, str):
        try:
            h, m, *s = map(int, val.split(":"))
            return time(h, m, s[0] if s else 0)
        except Exception:
            return time(0, 0)
    return time(0, 0)

# 2) Listar caixilhos
for cx in db.query(Caixilho).filter(Caixilho.obra_id.in_([o.id for o in obras])).all():
    with st.expander(f"{cx.referencia}"):
        # Botões Editar e Apagar no topo
        col_btn1, col_btn2 = st.columns([1,1])
        editar_click = col_btn1.button("✏️ Editar", key=f"editar_{cx.id}")
        apagar_click = col_btn2.button("🗑️ Apagar", key=f"apagar_{cx.id}")

        if apagar_click:
            db.query(Tempo).filter_by(caixilho_id=cx.id).delete()
            db.delete(cx)
            db.commit()
            st.success("Apagado")
            st.rerun()

        # Toggle do formulário de edição
        if editar_click:
            if st.session_state.get("editar") == cx.id:
                st.session_state.pop("editar")
            else:
                st.session_state["editar"] = cx.id
            st.rerun()

        if st.session_state.get("editar") == cx.id:
            with st.form(f"fn_edit_{cx.id}", clear_on_submit=True):
                st.subheader(f"✏️ Editar Caixilho — {cx.referencia}")

                # PP / Ano PP
                col1, col2 = st.columns(2)
                pp = col1.text_input("PP", value=cx.pp or "")
                ano = col2.text_input("Ano PP", value=cx.ano_pp or "")

                # Referência / Tipologia / Série
                series_opcoes = [
                    "HY PI", "HY STYLE", "HY WIN+", "HY 30", "HY 40", "HY 50", "HY SLIM",
                    "HY WALL", "HY SHUTTER", "HY GUI", "HY SKY", "HY WOOD", "Outra"
                ]
                tipos_por_serie = {
                    "HY GUI": ["Assistência", "Guilhotina"],
                    "HY WALL": ["Assistência", "Fachada"],
                    "HY PI": ["Assistência", "Pivotante"],
                    "HY SHUTTER": ["Assistência", "Harmónio"],
                    "HY STYLE": ["Assistência", "Janela batente", "Janela basculante", "Janela projetante", "Janela oscilo-batente", "Caixilho composto", "Porta batente", "Fixo"],
                    "HY WIN+": ["Assistência", "Janela batente", "Janela basculante", "Janela projetante", "Janela oscilo-batente", "Caixilho composto", "Porta batente", "Fixo"],
                    "HY SKY": ["Assistência", "Claraboia"],
                    "HY 30": ["MONO", "BI", "TRI", "QUADRI", "PENTA", "HEXA", "SEPTA", "OCTA", "NONA",
                              "PK-MONO", "PK-BI", "PK-TRI", "PK-QUADRI", "PK-PENTA", "PK-HEXA", "PK-SEPTA", "PK-OCTA", "PK-NONA"],
                    "HY 40": ["MONO", "BI", "TRI", "QUADRI", "PENTA", "HEXA", "SEPTA", "OCTA", "NONA",
                              "PK-MONO", "PK-BI", "PK-TRI", "PK-QUADRI", "PK-PENTA", "PK-HEXA", "PK-SEPTA", "PK-OCTA", "PK-NONA"],
                    "HY 50": ["MONO", "BI", "TRI", "QUADRI", "PENTA", "HEXA", "SEPTA", "OCTA", "NONA",
                              "PK-MONO", "PK-BI", "PK-TRI", "PK-QUADRI", "PK-PENTA", "PK-HEXA", "PK-SEPTA", "PK-OCTA", "PK-NONA"],
                    "HY SLIM": ["MONO", "BI", "TRI", "QUADRI", "PENTA", "HEXA", "SEPTA", "OCTA", "NONA",
                                "PK-MONO", "PK-BI", "PK-TRI", "PK-QUADRI", "PK-PENTA", "PK-HEXA", "PK-SEPTA", "PK-OCTA", "PK-NONA"],
                }
                col1, col2, col3 = st.columns(3)
                ref = col1.text_input("Referência*", value=cx.referencia)
                serie_default = cx.serie if cx.serie in series_opcoes else series_opcoes[0]
                ser = col3.selectbox("Série*", series_opcoes, index=series_opcoes.index(serie_default))
                tipos = tipos_por_serie.get(ser, ["Assistência"])
                tip = col2.selectbox("Tipologia*", tipos, index=tipos.index(cx.tipologia) if cx.tipologia in tipos else 0)

                # Altura / Largura / M²
                col1, col2, col3 = st.columns(3)
                alt = col1.text_input("Altura (mm)", value=str(cx.altura or ""))
                lar = col2.text_input("Largura (mm)", value=str(cx.largura or ""))

                # Lógica para M²
                try:
                    altura_val = float(alt) if alt else None
                    largura_val = float(lar) if lar else None
                except ValueError:
                    altura_val = largura_val = None

                if cx.m2 is not None:
                    m2 = cx.m2
                elif altura_val is not None and largura_val is not None:
                    m2 = altura_val * largura_val / 1_000_000
                else:
                    m2 = None

                if m2 is not None:
                    col3.markdown(f"**M²:** {m2:.3f}")
                else:
                    col3.markdown("**M²:** -")

                # Nº Folhas / Nº Fixos
                col1, col2 = st.columns(2)
                nf = col1.text_input("Nº Folhas*", value=cx.n_folhas)
                fix = col2.text_input("Nº Fixos*", value=cx.n_fixos or "") if ser in ["HY STYLE", "HY WIN+"] else None

                # Extras condicionais
                extras_cond = ser in ["HY 30", "HY 40", "HY 50", "HY SLIM", "Outra"]
                extras = {
                    "pocket": "Pocket?",
                    "caixa_parede": "Caixa de Parede?",
                    "fecho_prumo": "Fecho Prumo?",
                    "inox": "Inox?"
                } if extras_cond else {}
                extras.update({
                    "mosquiteira": "Mosquiteira?",
                    "alarme": "Alarme?",
                    "ventosa": "Ventosa?",
                    "motorizacao": "Motorização?",
                    "canto": "Canto?",
                    "sdl": "SDL?",
                    "customizacao": "Customização?",
                    "curvatura": "Curvatura?"
                })
                vals = {}
                keys = list(extras.keys())
                for i in range(0, len(keys), 4):
                    cols4 = st.columns(4)
                    for j, key in enumerate(keys[i:i+4]):
                        # Força pocket=True se tipologia começar por PK-
                        if key == "pocket" and tip.startswith("PK-"):
                            vals[key] = True
                            cols4[j].checkbox(extras[key], value=True, disabled=True)
                        else:
                            vals[key] = cols4[j].checkbox(extras[key], value=getattr(cx, key))

                # Nº Motores se motorizado
                if vals.get("motorizacao"):
                    nm = st.number_input("Nº Motores", min_value=1, value=cx.n_motores or 1)
                else:
                    nm = None

                # Data de Caixa
                dc = st.date_input("Data Caixa", value=cx.data_caixa or datetime.today().date())

                # Guardar alterações
                guardar = st.form_submit_button("Guardar")
                if guardar:
                    cx.pp = int(pp) if pp else None
                    cx.ano_pp = int(ano) if ano else None
                    cx.referencia, cx.tipologia, cx.serie = ref, tip, ser
                    cx.altura, cx.largura = float(alt), float(lar)
                    cx.m2 = float(alt) * float(lar) / 1e6
                    cx.n_folhas = nf
                    cx.n_fixos = fix or None
                    cx.data_caixa = dc
                    for k, v in vals.items():
                        setattr(cx, k, v)
                    cx.n_motores = nm
                    db.commit()
                    st.success("Atualizado com sucesso!")
                    st.session_state.pop("editar")
                    st.session_state.pop("unsaved_edits", None)
                    st.rerun()
                else:
                    st.session_state["unsaved_edits"] = True

        # Formulário de tempos (mantém como já tens)
        setores = [
            ("Corte", "Mec"),
            ("Limpeza", "Ass"),
            ("Vidro", "Emb"),
            ("Mot", None)
        ]
        tempos_input = {}
        with st.form(f"ft{cx.id}", clear_on_submit=True):
            st.subheader(f"Tempos: {cx.referencia}")
            for par in setores:
                for setor in par:
                    if setor:
                        with st.container():
                            tempo_obj = db.query(Tempo).filter_by(caixilho_id=cx.id, estacao=setor).first()
                            tempo_valor = to_time(tempo_obj.tempo_execucao) if tempo_obj else time(0, 0)
                            operador_valor = tempo_obj.operador if tempo_obj else ""
                            di = st.date_input(
                                f"Início {setor}",
                                value=tempo_obj.data_inicio if tempo_obj else date.today(),
                                key=f"{cx.id}{setor}in"
                            )
                            df = st.date_input(
                                f"Fim {setor}",
                                value=tempo_obj.data_fim if tempo_obj else date.today(),
                                key=f"{cx.id}{setor}out"
                            )
                            tempo = st.time_input(
                                f"Tempo Execução {setor}",
                                value=tempo_valor,
                                key=f"{cx.id}{setor}tempo"
                            )
                            operador = st.text_input(
                                f"Operador {setor}",
                                value=operador_valor,
                                key=f"{cx.id}{setor}operador"
                            )
                            tempos_input[setor] = (di, df, tempo, operador, tempo_obj)
            if st.form_submit_button("Guardar Tempos"):
                for setor, (di, df, tempo, operador, tempo_obj) in tempos_input.items():
                    if tempo != time_default(0, 0, 0):
                        if tempo_obj:
                            tempo_obj.data_inicio = di
                            tempo_obj.data_fim = df
                            tempo_obj.tempo_execucao = tempo
                            tempo_obj.operador = operador
                        else:
                            novo = Tempo(
                                caixilho_id=cx.id,
                                estacao=setor,
                                data_inicio=di,
                                data_fim=df,
                                tempo_execucao=tempo,
                                operador=operador
                            )
                            db.add(novo)
                    else:
                        if tempo_obj:
                            db.delete(tempo_obj)
                db.commit()
                st.success("Tempos guardados")
                st.session_state.pop("unsaved_edits", None)
                st.rerun()
# 5) Modal Novo Caixilho
if st.session_state.get("novo"):
    with st.form("form_novo_caixilho", clear_on_submit=True):
        st.subheader("➕ Novo Caixilho")

        col1, col2 = st.columns(2)
        pp = col1.text_input("PP")
        ano_pp = col2.text_input("Ano PP")

        col1, col2, col3 = st.columns(3)
        ref = col1.text_input("Referência*", max_chars=100)
        tipologia = col2.text_input("Tipologia*", max_chars=50)
        serie = col3.selectbox("Série*", ["HY PI", "HY STYLE", "HY WIN+", "HY 30", "HY 40", "HY 50", "HY WALL", "HY SHUTTER", "HY GUI", "HY SKY", "HY WOOD"])

        col1, col2, col3 = st.columns(3)
        altura = col1.text_input("Altura")
        largura = col2.text_input("Largura")

        try:
            altura_val = float(altura)
            largura_val = float(largura)
            m2 = altura_val * largura_val / 1_000_000
            col3.markdown(f"**M²:** {m2:.3f}")
        except:
            altura_val = largura_val = m2 = None
            col3.markdown("**M²:** -")

        col1, col2 = st.columns(2)
        n_folhas = col1.text_input("Nº Folhas*", max_chars=10)
        n_fixos = col2.text_input("Nº Fixos*", max_chars=10) if serie in ["HY STYLE", "HY WIN+"] else None

        extras = {
            "pocket": "É Pocket?",
            "caixa_parede": "Caixa de Parede?",
            "mosquiteira": "Mosquiteira?",
            "fecho_prumo": "Fecho Prumo?",
            "inox": "Reforço Inox?",
            "alarme": "Alarme?",
            "ventosa": "Ventosa?",
            "motorizacao": "Motorização?",
            "canto": "Canto?",
            "sdl": "SDL?",
            "customizacao": "Customização?",
            "curvatura": "Curvatura?"
        }

        valores = {}
        keys = list(extras.keys())
        for i in range(0, len(keys), 4):
            cols = st.columns(4)
            for j, key in enumerate(keys[i:i+4]):
                valores[key] = cols[j].checkbox(extras[key])

        n_motores = None
        if valores.get("motorizacao"):
            n_motores = st.number_input("Nº Motores", min_value=1, step=1)

        salvar = st.form_submit_button("Guardar")
        if salvar:
            if ref and tipologia and serie and n_folhas:
                dados = {
                    "referencia": ref,
                    "tipologia": tipologia,
                    "serie": serie,
                    "altura": altura_val,
                    "largura": largura_val,
                    "n_folhas": n_folhas,
                    "n_fixos": n_fixos,
                    "pp": int(pp) if pp else None,
                    "ano_pp": int(ano_pp) if ano_pp else None,
                    "n_motores": n_motores if valores.get("motorizacao") else None
                }
                dados.update(valores)
                novo = Caixilho(obra_id=obra.id, **dados)
                db.add(novo)
                db.commit()
                st.success("✅ Caixilho adicionado.")
                st.session_state.pop("novo")
                st.rerun()
            else:
                st.error("⚠️ Campos obrigatórios em falta.")


db.close()
