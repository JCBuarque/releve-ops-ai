import re
from pathlib import Path
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

PEDIDOS_FILE = DATA_DIR / "dados_pedidos_base_final.xlsx"
CUSTOS_FILE = DATA_DIR / "fatura_do_cartao (Custo Variavel).csv"

st.set_page_config(
    page_title="Re Leve Ops AI",
    page_icon="🥗",
    layout="wide"
)

CSS = """
<style>
    .main .block-container {
        padding-top: 1.6rem;
        padding-bottom: 2rem;
    }

    .hero {
        background: linear-gradient(135deg, #0F6B3E 0%, #2c9c67 100%);
        padding: 26px 30px;
        border-radius: 22px;
        color: white;
        margin-bottom: 18px;
    }

    .hero h1 {
        font-size: 2rem;
        margin: 0;
        color: white;
    }

    .hero p {
        margin-top: 8px;
        opacity: .92;
    }

    .panel {
        background: #ffffff;
        border-radius: 18px;
        padding: 16px;
        border: 1px solid #E3EDE7;
        margin-bottom: 20px;
    }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


def money_to_float(value):
    if pd.isna(value):
        return 0.0

    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()

    neg = "-" in text

    text = (
        text
        .replace("R$", "")
        .replace("$", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
    )

    text = re.sub(r"[^0-9.\-]", "", text)

    try:
        number = abs(float(text))
        return -number if neg else number
    except:
        return 0.0


@st.cache_data(show_spinner=False)
def load_pedidos():

    df = pd.read_excel(PEDIDOS_FILE)

    df = df.rename(columns={
        "NÂº": "pedido",
        "Data": "data",
        "Hora": "hora",
        "Cliente": "cliente",
        "Status": "status",
        "Valor total": "valor_total"
    })

    df["data"] = pd.to_datetime(df["data"], errors="coerce")

    df["valor_total"] = (
        pd.to_numeric(df["valor_total"], errors="coerce")
        .fillna(0)
    )

    df["hora_txt"] = (
        df["hora"]
        .astype(str)
        .str.slice(0, 5)
    )

    df["hora_num"] = (
        pd.to_datetime(
            df["hora_txt"],
            format="%H:%M",
            errors="coerce"
        )
        .dt.hour
    )

    df["dia_semana"] = df["data"].dt.day_name()

    mapa = {
        "Monday": "Segunda",
        "Tuesday": "Terça",
        "Wednesday": "Quarta",
        "Thursday": "Quinta",
        "Friday": "Sexta",
        "Saturday": "Sábado",
        "Sunday": "Domingo"
    }

    df["dia_semana"] = (
        df["dia_semana"]
        .map(mapa)
        .fillna(df["dia_semana"])
    )

    df["mes"] = (
        df["data"]
        .dt.to_period("M")
        .astype(str)
    )

    return df.dropna(subset=["data"])


@st.cache_data(show_spinner=False)
def load_custos():

    df = pd.read_csv(
        CUSTOS_FILE,
        sep=None,
        engine="python",
        encoding="utf-8"
    )

    df = df.rename(columns={
        "Data de compra": "data",
        "Categoria": "categoria",
        "Descrição": "descricao",
        "Valor (em R$)": "valor"
    })

    df["data"] = pd.to_datetime(
        df["data"],
        dayfirst=True,
        errors="coerce"
    )

    df["valor"] = df["valor"].apply(money_to_float)

    df["valor_abs"] = df["valor"].abs()

    df["categoria_limpa"] = np.where(
        df["categoria"].eq("-"),
        "Outros",
        df["categoria"].fillna("Outros")
    )

    df["fornecedor"] = (
        df["descricao"]
        .fillna("Não identificado")
        .str.title()
    )

    return df.dropna(subset=["data"])


def brl(v):
    return (
        f"R$ {v:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


pedidos = load_pedidos()
custos = load_custos()

st.markdown("""
<div class="hero">
    <h1>Re Leve Ops AI</h1>
    <p>Painel operacional e financeiro</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Pedidos",
        f"{len(pedidos):,}".replace(",", ".")
    )

with col2:
    st.metric(
        "Faturamento",
        brl(pedidos["valor_total"].sum())
    )

with col3:
    st.metric(
        "Custos",
        brl(custos["valor_abs"].sum())
    )

st.divider()

col_a, col_b = st.columns(2)

with col_a:

    vendas_dia = (
        pedidos
        .groupby("data")["valor_total"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        vendas_dia,
        x="data",
        y="valor_total",
        title="Faturamento por Dia"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with col_b:

    custos_cat = (
        custos
        .groupby("categoria_limpa")["valor_abs"]
        .sum()
        .reset_index()
    )

    fig2 = px.pie(
        custos_cat,
        names="categoria_limpa",
        values="valor_abs",
        title="Custos por Categoria"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

st.divider()

st.subheader("Pedidos")

st.dataframe(
    pedidos.head(20),
    use_container_width=True
)

st.subheader("Custos")

st.dataframe(
    custos.head(20),
    use_container_width=True
)
