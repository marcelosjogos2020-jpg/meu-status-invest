import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import streamlit.components.v1 as components
import os
import json
from datetime import datetime
from streamlit_searchbox import st_searchbox

# Configuração para usar o ecrã inteiro
st.set_page_config(page_title="Meu Portfólio", page_icon="📈", layout="wide")

# ==========================================
# --- 0. LISTA DE TICKERS (B3) PARA BUSCA INTELIGENTE ---
# ==========================================
TICKERS_B3 = {
    "PETR3": "Petrobras ON", "PETR4": "Petrobras PN",
    "VALE3": "Vale ON",
    "ITUB3": "Itaú Unibanco ON", "ITUB4": "Itaú Unibanco PN",
    "BBDC3": "Bradesco ON", "BBDC4": "Bradesco PN",
    "BBAS3": "Banco do Brasil ON",
    "SANB11": "Santander Unit",
    "ABEV3": "Ambev ON",
    "WEGE3": "WEG ON",
    "RENT3": "Localiza ON",
    "SUZB3": "Suzano ON",
    "JBSS3": "JBS ON",
    "GGBR4": "Gerdau PN",
    "CSNA3": "CSN ON",
    "CMIG3": "Cemig ON", "CMIG4": "Cemig PN",
    "CPLE3": "Copel ON", "CPLE6": "Copel PNB",
    "ELET3": "Eletrobras ON", "ELET6": "Eletrobras PNB",
    "EQTL3": "Equatorial ON",
    "ENGI11": "Energisa Unit",
    "TAEE11": "Taesa Unit",
    "CPFE3": "CPFL Energia ON",
    "RADL3": "Raia Drogasil ON",
    "LREN3": "Lojas Renner ON",
    "MGLU3": "Magazine Luiza ON",
    "AMER3": "Americanas ON",
    "VIVT3": "Vivo ON",
    "TIMS3": "TIM ON",
    "B3SA3": "B3 ON",
    "BPAC11": "BTG Pactual Unit",
    "HAPV3": "Hapvida ON",
    "RDOR3": "Rede D'Or ON",
    "GNDI3": "Intermédica ON",
    "CCRO3": "CCR ON",
    "RAIL3": "Rumo ON",
    "EMBR3": "Embraer ON",
    "AZUL4": "Azul PN",
    "GOLL4": "Gol PN",
    "COGN3": "Cogna ON",
    "YDUQ3": "Yduqs ON",
    "MRFG3": "Marfrig ON",
    "BEEF3": "Minerva ON",
    "BRFS3": "BRF ON",
    "NTCO3": "Natura ON",
    "ASAI3": "Assaí ON",
    "PCAR3": "GPA ON",
    "CRFB3": "Carrefour Brasil ON",
    "CYRE3": "Cyrela ON",
    "MRVE3": "MRV ON",
    "EZTC3": "Eztec ON",
    "USIM5": "Usiminas PNA",
    "CSAN3": "Cosan ON",
    "UGPA3": "Ultrapar ON",
    "PRIO3": "PetroRio ON",
    "RRRP3": "3R Petroleum ON",
    "VBBR3": "Vibra Energia ON",
    "SLCE3": "SLC Agrícola ON",
    "SMTO3": "São Martinho ON",
    "KLBN11": "Klabin Unit",
    "DXCO3": "Dexco ON",
    "TOTS3": "Totvs ON",
    "LWSA3": "Locaweb ON",
    "POSI3": "Positivo ON",
    "IRBR3": "IRB Brasil ON",
    "BBSE3": "BB Seguridade ON",
    "PSSA3": "Porto Seguro ON",
    "SBSP3": "Sabesp ON",
    "GARE11": "GGR Covepi Renda FII",
    "VGIA11": "Valora RE III FII",
    "MXRF11": "Maxi Renda FII",
    "HGLG11": "CSHG Logística FII",
    "KNRI11": "Kinea Renda Imobiliária FII",
    "XPML11": "XP Malls FII",
    "VISC11": "Vinci Shopping Centers FII",
    "BCFF11": "BTG Pactual Fundo de Fundos FII",
    "HGRE11": "CSHG Real Estate FII",
    "IRDM11": "Iridium Recebíveis FII",
    "KNCR11": "Kinea Rendimentos Imobiliários FII",
    "RECR11": "REC Recebíveis Imobiliários FII",
    "VILG11": "Vinci Logística FII",
    "BTLG11": "BTG Pactual Logística FII",
    "HFOF11": "Hedge Top FOFII 3 FII",
    "RBRF11": "RBR Alpha FII",
    "PVBI11": "VBI Prime Properties FII",
}

def search_tickers(searchterm):
    if not searchterm:
        return []
    termo = searchterm.strip().upper()
    resultados = []
    for tk, nome in TICKERS_B3.items():
        if termo in tk or termo in nome.upper():
            resultados.append((f"{tk} — {nome}", tk))
    resultados.sort(key=lambda x: (not x[1].startswith(termo), x[1]))
    return resultados[:15]

# ==========================================
# --- 1. BANCO DE DADOS (CSV) ---
# ==========================================
ARQUIVO_BANCO = "minha_carteira.csv"
CARTEIRAS_FORA_DO_PATRIMONIO = {"WATCHLIST"}

def carregar_dados():
    if os.path.exists(ARQUIVO_BANCO):
        df = pd.read_csv(ARQUIVO_BANCO)
        if "Preço Médio" in df.columns:
            df = df.rename(columns={"Preço Médio": "Preço Pago"})
        if "Data da Compra" not in df.columns:
            df["Data da Compra"] = "Antes da Atualização"
        if "Carteira" not in df.columns:
            df["Carteira"] = "COMPRAS (Real)"
        return df.to_dict(orient="records")
    return []

def salvar_dados(dados):
    df = pd.DataFrame(dados)
    df.to_csv(ARQUIVO_BANCO, index=False)
    return df.to_dict(orient="records")

if "carteira" not in st.session_state:
    st.session_state["carteira"] = carregar_dados()

def eh_patrimonio_real(ativo):
    return ativo.get("Carteira", "COMPRAS (Real)").upper() not in CARTEIRAS_FORA_DO_PATRIMONIO

# ==========================================
# --- 2. FUNÇÕES DE DADOS (YFINANCE) ---
# ==========================================
@st.cache_data(ttl=60)
def buscar_cotacao_simples(ticker):
    ticker_sa = ticker if ticker.endswith(('.SA', '-BRL', '=X', '^')) else f"{ticker}.SA"
    try:
        hist = yf.Ticker(ticker_sa).history(period="1d")
        if len(hist) > 0:
            return float(hist['Close'].iloc[-1])
    except Exception:
        pass
    try:
        preco = yf.Ticker(ticker_sa).fast_info.get("last_price")
        if preco:
            return float(preco)
    except Exception:
        pass
    return None

@st.cache_data(ttl=60)
def buscar_cotacoes_lote(tickers):
    if not tickers:
        return {}
    tickers_sa = [t if t.endswith(('.SA', '-BRL', '=X', '^')) else f"{t}.SA" for t in tickers]
    try:
        dados = yf.download(tickers=tickers_sa, period="1d", progress=False, group_by="ticker")
        precos = {}
        for t, t_sa in zip(tickers, tickers_sa):
            try:
                if
