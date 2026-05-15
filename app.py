import re
from pathlib import Path
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dados"
PEDIDOS_FILE = DATA_DIR / "dados_pedidos_base_final.xlsx"
CUSTOS_FILE = DATA_DIR / "fatura_do_cartao (Custo Variavel).csv"

st.set_page_config(page_title="Re Leve Ops AI", page_icon="🥗", layout="wide")

CSS = """
<style>
    .main .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    [data-testid="stSidebar"] {background: linear-gradient(180deg, #f7fbf8 0%, #ffffff 100%);}
    .hero {background: linear-gradient(135deg, #0F6B3E 0%, #2c9c67 100%); padding: 26px 30px; border-radius: 22px; color: white; margin-bottom: 18px; box-shadow: 0 10px 28px rgba(15,107,62,.18);}
    .hero h1 {font-size: 2.0rem; margin: 0 0 4px 0; color: white;}
    .hero p {font-size: 1.02rem; margin: 0; opacity: .92;}
    .metric-card {background: #ffffff; border: 1px solid #E3EDE7; border-radius: 18px; padding: 18px 20px; box-shadow: 0 8px 24px rgba(16,24,40,.05); height: 136px;}
    .metric-title {font-size: .88rem; color: #5f6f66; margin-bottom: 8px;}
    .metric-value {font-size: 1.85rem; font-weight: 800; color: #172026; margin-bottom: 5px;}
    .metric-caption {font-size: .82rem; color: #0F6B3E;}
    .panel {background: #ffffff; border: 1px solid #E3EDE7; border-radius: 18px; padding: 16px; box-shadow: 0 8px 24px rgba(16,24,40,.04);}
    .ai-box {background: #F3F8F5; border: 1px solid #C9E7D5; border-radius: 18px; padding: 18px;}
    .alert-box {background: #FFF8EA; border: 1px solid #FFE0A6; border-radius: 16px; padding: 14px 16px; margin-bottom: 10px;}
    .small-muted {color:#667085; font-size:.88rem;}
    div[data-testid="stMetricValue"] {font-size: 1.7rem;}
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

    text = text.replace("R$", "").replace("$", "").replace(" ", "")
    text = text.replace(".", "").replace(",", ".")
    text = re.sub(r"[^0-9.\-]", "", text)

    try:
        number = abs(float(text))
        return -number if neg else number
    except Exception:
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
    df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce").fillna(0)

    df["hora_txt"] = df["hora"].astype(str).str.slice(0, 5)
    df["hora_num"] = pd.to_datetime(
        df["hora_txt"],
        format="%H:%M",
        errors="coerce"
    ).dt.hour

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

    df["dia_semana"] = df["dia_semana"].map(mapa).fillna(df["dia_semana"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)

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
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v):
    return f"{v:.1f}%".replace(".", ",")


pedidos = load_pedidos()
custos = load_custos()

st.title("Re Leve Ops AI")

st.success("Aplicativo carregado com sucesso 🚀")

st.write("Pedidos carregados:", len(pedidos))
st.write("Custos carregados:", len(custos))
