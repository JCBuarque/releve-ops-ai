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
    df = df.rename(columns={"NÂº": "pedido", "Data": "data", "Hora": "hora", "Cliente": "cliente", "Status": "status", "Valor total": "valor_total"})
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce").fillna(0)
    df["hora_txt"] = df["hora"].astype(str).str.slice(0, 5)
    df["hora_num"] = pd.to_datetime(df["hora_txt"], format="%H:%M", errors="coerce").dt.hour
    df["dia_semana"] = df["data"].dt.day_name(locale=None)
    mapa = {"Monday":"Segunda", "Tuesday":"Terça", "Wednesday":"Quarta", "Thursday":"Quinta", "Friday":"Sexta", "Saturday":"Sábado", "Sunday":"Domingo"}
    df["dia_semana"] = df["dia_semana"].map(mapa).fillna(df["dia_semana"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    return df.dropna(subset=["data"])


@st.cache_data(show_spinner=False)
def load_custos():
    df = pd.read_csv(CUSTOS_FILE, sep=None, engine="python", encoding="utf-8")
    df = df.rename(columns={"Data de compra":"data", "Categoria":"categoria", "Descrição":"descricao", "Valor (em R$)":"valor"})
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    df["valor"] = df["valor"].apply(money_to_float)
    df["valor_abs"] = df["valor"].abs()
    df["categoria_limpa"] = np.where(df["categoria"].eq("-"), "Outros", df["categoria"].fillna("Outros"))
    df["fornecedor"] = df["descricao"].fillna("Não identificado").str.title()
    return df.dropna(subset=["data"])


def brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v):
    return f"{v:.1f}%".replace(".", ",")


def build_insights(df, custos):
    daily = df.groupby("data").size()
    hour = df.dropna(subset=["hora_num"]).groupby("hora_num").size()
    weekday = df.groupby("dia_semana").size().sort_values(ascending=False)
    insights = []
    if not weekday.empty:
        top_day = weekday.index[0]
        top_val = weekday.iloc[0]
        avg_day = weekday.mean()
        diff = ((top_val / avg_day) - 1) * 100 if avg_day else 0
        insights.append(f"{top_day} concentra o maior volume de pedidos, com {pct(max(diff, 0))} acima da média semanal.")
    if not hour.empty:
        top_hour = int(hour.idxmax())
        insights.append(f"O horário de maior demanda é por volta de {top_hour:02d}h. Esse período deve orientar produção, atendimento e logística.")
    if len(daily) > 7:
        last7 = daily.tail(7).mean()
        hist = daily.mean()
        delta = ((last7 / hist) - 1) * 100 if hist else 0
        trend = "acima" if delta >= 0 else "abaixo"
        insights.append(f"A média dos últimos 7 dias está {pct(abs(delta))} {trend} da média histórica.")
    if not custos.empty:
        fornecedores = custos[custos["valor"] > 0].groupby("fornecedor")["valor_abs"].sum().sort_values(ascending=False)
        if not fornecedores.empty:
            insights.append(f"O fornecedor com maior peso no custo variável é {fornecedores.index[0]}, somando {brl(fornecedores.iloc[0])} no período analisado.")
    return insights[:4]


pedidos = load_pedidos()
custos = load_custos()

st.sidebar.markdown("## 🌿 Re Leve Ops AI")
st.sidebar.markdown("**Copiloto de Eficiência Operacional**")
st.sidebar.divider()
menu = st.sidebar.radio("Navegação", ["Visão Geral", "Pedidos", "Produção & Demanda", "Custos", "Insights IA", "Plano de Ação"], index=0)
st.sidebar.divider()
st.sidebar.info("Protótipo interativo criado para apoiar a Re Leve Recife em eficiência operacional, previsibilidade e escala.")

min_date = pedidos["data"].min().date()
max_date = pedidos["data"].max().date()
colA, colB = st.columns([1, 2])
with colA:
    date_range = st.date_input("Período dos pedidos", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
else:
    start_date, end_date = pd.to_datetime(min_date), pd.to_datetime(max_date)

f_pedidos = pedidos[(pedidos["data"] >= start_date) & (pedidos["data"] <= end_date)].copy()
f_custos = custos[(custos["data"] >= start_date) & (custos["data"] <= end_date)].copy()

receita = f_pedidos["valor_total"].sum()
total_pedidos = len(f_pedidos)
ticket = receita / total_pedidos if total_pedidos else 0
dias = max((end_date - start_date).days + 1, 1)
media_dia = total_pedidos / dias
custos_pos = f_custos[f_custos["valor"] > 0]["valor_abs"].sum()
margem_estimada = receita - custos_pos

st.markdown("""
<div class='hero'>
  <h1>Dashboard Operacional Re Leve</h1>
  <p>Eficiência operacional com dados, automação e insights de IA para uma operação enxuta escalar com inteligência.</p>
</div>
""", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
for col, title, value, cap in [
    (m1, "Total de pedidos", f"{total_pedidos:,}".replace(",", "."), "Volume operacional no período"),
    (m2, "Faturamento", brl(receita), "Receita bruta dos pedidos"),
    (m3, "Ticket médio", brl(ticket), "Valor médio por pedido"),
    (m4, "Média pedidos/dia", f"{media_dia:.1f}".replace(".", ","), "Base para prever produção"),
]:
    with col:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>{title}</div><div class='metric-value'>{value}</div><div class='metric-caption'>{cap}</div></div>", unsafe_allow_html=True)

st.write("")

if menu == "Visão Geral":
    c1, c2, c3 = st.columns([2, 1.35, 1.1])
    with c1:
        st.subheader("Pedidos por dia")
        daily = f_pedidos.groupby("data").agg(pedidos=("pedido", "count"), receita=("valor_total", "sum")).reset_index()
        fig = px.line(daily, x="data", y="pedidos", markers=True)
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="", yaxis_title="Pedidos")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Pedidos por horário")
        hourly = f_pedidos.dropna(subset=["hora_num"]).groupby("hora_num").size().reset_index(name="pedidos")
        fig = px.bar(hourly, x="hora_num", y="pedidos")
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Hora", yaxis_title="Pedidos")
        st.plotly_chart(fig, use_container_width=True)
    with c3:
        st.markdown("### ✨ Insights da IA")
        st.markdown("<div class='ai-box'>" + "<br><br>".join([f"• {i}" for i in build_insights(f_pedidos, f_custos)]) + "</div>", unsafe_allow_html=True)

    c4, c5, c6 = st.columns([1.2, 1, 1.2])
    with c4:
        st.subheader("Top dias da semana")
        order = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        week = f_pedidos.groupby("dia_semana").size().reindex(order).dropna().reset_index(name="pedidos")
        fig = px.bar(week, x="pedidos", y="dia_semana", orientation="h")
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Pedidos", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with c5:
        st.subheader("Receita por status")
        status = f_pedidos.groupby("status")["valor_total"].sum().reset_index()
        fig = px.pie(status, values="valor_total", names="status", hole=.55)
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with c6:
        st.subheader("Alertas operacionais")
        alerts = [
            "Planejar produção com base nos 3 dias de maior demanda.",
            "Monitorar pedidos nos horários de pico para evitar atraso no atendimento.",
            "Cruzar pedidos e custos para estimar margem por período.",
        ]
        for a in alerts:
            st.markdown(f"<div class='alert-box'>⚠️ {a}</div>", unsafe_allow_html=True)

elif menu == "Pedidos":
    st.subheader("Análise de pedidos")
    c1, c2 = st.columns(2)
    with c1:
        mensal = f_pedidos.groupby("mes").agg(pedidos=("pedido", "count"), receita=("valor_total", "sum")).reset_index()
        fig = px.bar(mensal, x="mes", y="receita", text_auto='.2s', title="Receita mensal")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        clientes = f_pedidos.groupby("cliente").agg(pedidos=("pedido", "count"), receita=("valor_total", "sum")).sort_values("pedidos", ascending=False).head(10).reset_index()
        fig = px.bar(clientes, x="pedidos", y=clientes["cliente"].astype(str), orientation="h", title="Clientes recorrentes (mascarados)")
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(f_pedidos.sort_values("data", ascending=False), use_container_width=True, hide_index=True)

elif menu == "Produção & Demanda":
    st.subheader("Previsão simples de demanda")
    daily = f_pedidos.groupby("data").size().reset_index(name="pedidos")
    daily = daily.sort_values("data")
    media_7 = daily["pedidos"].tail(7).mean() if len(daily) else 0
    media_30 = daily["pedidos"].tail(30).mean() if len(daily) else 0
    base = media_7 if not np.isnan(media_7) and media_7 > 0 else media_30
    forecast_dates = pd.date_range(end_date + timedelta(days=1), periods=7, freq="D")
    forecast = pd.DataFrame({"data": forecast_dates, "previsao": [round(base * x, 0) for x in [1.00, 1.05, .95, 1.10, 1.15, .85, .75]]})
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["data"], y=daily["pedidos"], mode="lines+markers", name="Histórico"))
    fig.add_trace(go.Scatter(x=forecast["data"], y=forecast["previsao"], mode="lines+markers", name="Previsão"))
    fig.update_layout(height=430, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="Pedidos")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Recomendação operacional")
    st.success(f"Planejar produção base de aproximadamente {base:.0f} pedidos/dia, ajustando para cima nos dias historicamente mais fortes.")
    st.dataframe(forecast.assign(previsao=forecast["previsao"].astype(int)), use_container_width=True, hide_index=True)

elif menu == "Custos":
    st.subheader("Custos variáveis")
    c1, c2, c3 = st.columns(3)
    c1.metric("Custos positivos", brl(custos_pos))
    c2.metric("Resultado antes de custos fixos", brl(margem_estimada))
    c3.metric("Peso do custo variável", pct((custos_pos / receita * 100) if receita else 0))
    c4, c5 = st.columns(2)
    with c4:
        cat = f_custos[f_custos["valor"] > 0].groupby("categoria_limpa")["valor_abs"].sum().reset_index()
        fig = px.pie(cat, values="valor_abs", names="categoria_limpa", hole=.45, title="Custos por categoria")
        st.plotly_chart(fig, use_container_width=True)
    with c5:
        forn = f_custos[f_custos["valor"] > 0].groupby("fornecedor")["valor_abs"].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(forn, x="valor_abs", y="fornecedor", orientation="h", title="Principais fornecedores")
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(f_custos.sort_values("data", ascending=False), use_container_width=True, hide_index=True)

elif menu == "Insights IA":
    st.subheader("Copiloto de insights operacionais")
    for insight in build_insights(f_pedidos, f_custos):
        st.markdown(f"<div class='ai-box'>✨ {insight}</div><br>", unsafe_allow_html=True)
    pergunta = st.text_area("Pergunte algo para o copiloto", placeholder="Ex.: Quais ações posso tomar para reduzir desperdício nesta semana?")
    if st.button("Gerar resposta"):
        if pergunta.strip():
            st.success("Sugestão: priorize previsão de produção pelos dias de maior demanda, acompanhe fornecedores com maior peso no custo e automatize um relatório semanal com pedidos, ticket médio, custos e alertas.")
        else:
            st.warning("Digite uma pergunta para gerar uma recomendação.")

elif menu == "Plano de Ação":
    st.subheader("Plano para implantação da solução")
    plano = pd.DataFrame([
        ["1. Organizar dados", "Padronizar arquivos de pedidos e custos", "Baixa", "Imediato"],
        ["2. Criar indicadores", "Pedidos/dia, ticket médio, horários de pico e custos", "Média", "1 semana"],
        ["3. Criar dashboard", "Automatizar visão operacional semanal", "Média", "1 semana"],
        ["4. Prever demanda", "Gerar previsão simples para produção", "Alta", "2 semanas"],
        ["5. Automatizar relatório", "Enviar resumo semanal para a empreendedora", "Alta", "2 semanas"],
        ["6. Evoluir IA", "Conectar perguntas e respostas aos dados", "Alta", "3 semanas"],
    ], columns=["Etapa", "Entrega", "Impacto", "Prazo"])
    st.dataframe(plano, use_container_width=True, hide_index=True)
    st.markdown("### Pitch da solução")
    st.info("Criamos um copiloto operacional para transformar dados da Re Leve em decisões rápidas sobre produção, custos e eficiência, reduzindo desperdícios e aumentando a capacidade de escala da operação.")
