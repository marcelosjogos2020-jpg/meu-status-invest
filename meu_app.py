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

# 🚀 RESET TOTAL DE CSS: Cola tudo no topo e gerencia o estilo dos mini-cards
st.markdown("""
    <style>
        /* Esconde o cabeçalho nativo do Streamlit */
        [data-testid="stHeader"] {
            display: none !important;
            height: 0px !important;
            opacity: 0 !important;
        }
        
        /* Zera o padding superior de todos os containers de layout */
        .main .block-container, 
        [data-testid="stAppViewBlockContainer"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlockRoot"] {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }

        /* Remove margens extras do primeiro bloco de elementos */
        [data-testid="stVerticalBlock"] > div:first-child {
            margin-top: 0px !important;
            padding-top: 0px !important;
        }
        
        iframe {
            margin-top: 0px !important;
        }

        /* Estilo dos Mini-Cards Super Compactos do Topo */
        .mini-card {
            background-color: #161A25;
            border: 1px solid #2B3040;
            border-radius: 6px;
            padding: 4px 6px;
            text-align: center;
            margin-bottom: 6px;
            font-family: Arial, sans-serif;
        }
        .mini-card-watch {
            border: 1.5px solid #378ADD !important;
        }
        .card-ticker {
            color: #a0aec0;
            font-size: 10px;
            font-weight: bold;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .card-preco {
            color: #ffffff;
            font-size: 13px;
            font-weight: bold;
            margin: 1px 0;
        }
        .card-var {
            font-size: 9px;
            font-weight: 500;
        }
        .var-positiva { color: #00e676; }
        .var-negativa { color: #ff4b4b; }
    </style>
""", unsafe_allow_html=True)

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
    "GARE11": "GARE Recebíveis Imobiliários FII",
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
    "HSAF11": "HSI Ativos Financeiros FII",
}

def search_tickers(searchterm):
    if not searchterm:
        return []
    termo = searchterm.strip().upper()
    resultados = []
    if len(termo) >= 4:
        resultados.append((f"➕ Usar ativo digitado: {termo}", termo))
    for tk, nome in TICKERS_B3.items():
        if termo in tk or termo in nome.upper():
            if tk != termo:
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
    return None

@st.cache_data(ttl=60)
def buscar_cotacoes_lote(tickers):
    if not tickers:
        return {}
    tickers_sa = [t if t.endswith(('.SA', '-BRL', '=X', '^')) else f"{t}.SA" for t in tickers]
    precos = {}
    try:
        dados = yf.download(tickers=tickers_sa, period="2d", progress=False)
        for t, t_sa in zip(tickers, tickers_sa):
            try:
                if isinstance(dados.columns, pd.MultiIndex):
                    df_ticker = dados.xs(t_sa, level=1, axis=1) if t_sa in dados.columns.get_level_values(1) else dados[t_sa]
                else:
                    df_ticker = dados
                df_ticker = df_ticker.dropna(subset=["Close"])
                if len(df_ticker) >= 2:
                    atual = float(df_ticker["Close"].iloc[-1])
                    anterior = float(df_ticker["Close"].iloc[-2])
                    var = atual - anterior
                    pct = (var / anterior) * 100
                elif len(df_ticker) == 1:
                    atual = float(df_ticker["Close"].iloc[-1])
                    var, pct = 0.0, 0.0
                else:
                    atual = buscar_cotacao_simples(t) or 0.0
                    var, pct = 0.0, 0.0
                precos[t] = {"preco": atual, "var": var, "pct": pct}
            except Exception:
                p = buscar_cotacao_simples(t)
                precos[t] = {"preco": p if p else 0.0, "var": 0.0, "pct": 0.0}
        return precos
    except Exception:
        return {t: {"preco": buscar_cotacao_simples(t) or 0.0, "var": 0.0, "pct": 0.0} for t in tickers}

@st.cache_data(ttl=300)
def buscar_indices_topo():
    try:
        ibov = yf.Ticker("^BVSP").history(period="2d")
        dolar = yf.Ticker("BRL=X").history(period="2d")
        btc = yf.Ticker("BTC-BRL").history(period="2d")
        dados = {}
        for nome, hist in [("IBOV", ibov), ("USD", dolar), ("BTC", btc)]:
            if len(hist) >= 2:
                atual = hist['Close'].iloc[-1]
                ant = hist['Close'].iloc[-2]
                var = atual - ant
                pct = (var / ant) * 100
                dados[nome] = {"preco": atual, "var": var, "pct": pct}
        return dados
    except Exception:
        return None

@st.cache_data(ttl=300)
def buscar_destaques_mercado():
    tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'B3SA3.SA', 'ABEV3.SA',
               'WEGE3.SA', 'RENT3.SA', 'SUZB3.SA', 'ELET3.SA', 'RADL3.SA', 'PRIO3.SA',
               'HAPV3.SA', 'MGLU3.SA', 'COGN3.SA', 'USIM5.SA', 'CSNA3.SA', 'GGBR4.SA',
               'JBSS3.SA', 'BBAS3.SA', 'RAIZ4.SA', 'AZZA3.SA', 'EGIE3.SA', 'BEEF3.SA',
               'BRAV3.SA', 'CSMG3.SA']
    resultados = []
    erro_geral = False
    try:
        df = yf.download(tickers, period="5d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            if 'Close' in df.columns.get_level_values(0):
                df_close = df['Close']
            else:
                df_close = df.xs('Close', level=1, axis=1)
        else:
            df_close = df['Close'] if 'Close' in df else df
        df_close = df_close.dropna(axis=1, how='all')
        for ticker in tickers:
            if ticker in df_close.columns:
                s = df_close[ticker].dropna()
                if len(s) >= 2:
                    p_ant, p_atu = float(s.iloc[-2]), float(s.iloc[-1])
                    if p_ant > 0:
                        var_pct = ((p_atu - p_ant) / p_ant) * 100
                        resultados.append({"Ativo": ticker.replace(".SA", ""), "Preço": p_atu, "Var%": var_pct})
    except Exception:
        erro_geral = True
    res_sort = sorted(resultados, key=lambda x: x["Var%"], reverse=True)
    n = len(res_sort)
    corte = min(5, n // 2) if n < 10 else 5
    altas = res_sort[:corte]
    baixas = sorted(res_sort[n - corte:], key=lambda x: x["Var%"]) if corte > 0 else []
    return altas, baixas, erro_geral

@st.cache_data(ttl=3600)
def buscar_historico(ticker):
    try:
        ticker_sa = ticker if ticker.endswith('.SA') else f"{ticker}.SA"
        hist = yf.Ticker(ticker_sa).history(period="6mo")
        hist.reset_index(inplace=True)
        if hist['Date'].dt.tz is not None:
            hist['Date'] = hist['Date'].dt.tz_localize(None)
        return hist[['Date', 'Close']].rename(columns={'Date': 'Data', 'Close': 'Preço'})
    except Exception:
        return pd.DataFrame()

# ==========================================
# --- 3. BARRA LATERAL ---
# ==========================================
carteiras_existentes = list(set([a.get("Carteira", "COMPRAS (Real)") for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA"]))
if "COMPRAS (Real)" not in carteiras_existentes: carteiras_existentes.insert(0, "COMPRAS (Real)")
if "WATCHLIST" not in carteiras_existentes: carteiras_existentes.append("WATCHLIST")

with st.sidebar:
    st.header("🛒 Adicionar Ativo")
    ticker_selecionado = st_searchbox(
        search_tickers,
        placeholder="Digite o código ou nome (ex: CEMIG, PETR4)",
        key="busca_ticker",
        clear_on_submit=False,
    )
    ticker_input = (ticker_selecionado or "").upper().strip()

    preco_atual_sidebar = None
    if ticker_input:
        with st.spinner("A buscar..."):
            preco_atual_sidebar = buscar_cotacao_simples(ticker_input)
        if preco_atual_sidebar:
            st.metric(label=f"Cotação Atual ({ticker_input})", value=f"R$ {preco_atual_sidebar:.2f}")
        else:
            st.warning("Não consegui buscar a cotação agora.")

    qtd_input = st.number_input("Quantidade (0 para editar data)", min_value=0, value=10)
    valor_padrao_preco = float(preco_atual_sidebar) if preco_atual_sidebar else 35.00
    preco_medio_input = st.number_input("Preço da Compra (R$)", min_value=0.01, value=valor_padrao_preco, step=0.01)
    data_compra_input = st.date_input("Data da Compra", value=datetime.today())
    carteira_selecionada = st.selectbox("Carteira", carteiras_existentes)

    if carteira_selecionada.upper() in CARTEIRAS_FORA_DO_PATRIMONIO:
        st.caption("👁️ Esta carteira é só acompanhamento: não entra no cálculo de patrimônio.")

    total_simulado = qtd_input * preco_medio_input
    st.info(f"**Total da Ordem: R$ {total_simulado:,.2f}**")

    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("Adicionar"):
        data_str = data_compra_input.strftime("%d/%m/%Y")
        if qtd_input > 0:
            st.session_state["carteira"].append({
                "Ticker": ticker_input, "Quantidade": qtd_input,
                "Preço Pago": preco_medio_input, "Data da Compra": data_str,
                "Carteira": carteira_selecionada
            })
        else:
            for ativo in reversed(st.session_state["carteira"]):
                if ativo["Ticker"] == ticker_input and ativo.get("Carteira", "COMPRAS (Real)") == carteira_selecionada:
                    ativo["Data da Compra"] = data_str
                    break
        st.session_state["carteira"] = salvar_dados(st.session_state["carteira"])
        st.success("Salvo!")
        st.rerun()

    if col_btn2.button("Limpar Tudo"):
        st.session_state["carteira"] = []
        if os.path.exists(ARQUIVO_BANCO): os.remove(ARQUIVO_BANCO)
        st.rerun()

    st.divider()
    st.header("📂 Nova Carteira")
    nova_carteira_input = st.text_input("Nome da Nova Carteira").upper()
    if st.button("Criar Carteira", use_container_width=True):
        if nova_carteira_input and nova_carteira_input not in carteiras_existentes:
            st.session_state["carteira"].append({
                "Ticker": "CAIXA", "Quantidade": 0, "Preço Pago": 0,
                "Data da Compra": datetime.today().strftime("%d/%m/%Y"), "Carteira": nova_carteira_input
            })
            st.session_state["carteira"] = salvar_dados(st.session_state["carteira"])
            st.success("Criada!")
            st.rerun()

# ==========================================
# --- LETREIRO ROTATIVO ---
# ==========================================
simbolos_letreiro = [
    {"proName": "BMFBOVESPA:IBOV", "title": "Ibovespa"},
    {"proName": "FX_IDC:USDBRL", "title": "Dólar"},
    {"proName": "BINANCE:BTCBRL", "title": "Bitcoin"}
]
if len(st.session_state["carteira"]) > 0:
    ativos_unicos = list(set([a["Ticker"] for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA"]))
    for ativo in ativos_unicos[:10]:
        simbolos_letreiro.append({"proName": f"BMFBOVESPA:{ativo}", "title": ativo})

codigo_letreiro = f"""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {{"symbols": {json.dumps(simbolos_letreiro)}, "showSymbolLogo": true, "isTransparent": true, "displayMode": "adaptive", "colorTheme": "dark", "locale": "br"}}
  </script>
</div>
"""
components.html(codigo_letreiro, height=75)

# ==========================================
# --- 4. TOPO: CARTÕES ULTRA COMPACTOS ---
# ==========================================
st.markdown("### 📊 Meu Portfólio & Acompanhamento")

indices = buscar_indices_topo()

def criar_cartao_html(titulo, valor, variacao, pct, prefixo="", watchlist=False):
    cor = "#00e676" if variacao >= 0 else "#ff4b4b"
    sinal = "+" if variacao >= 0 else ""
    borda = "1.5px solid #378ADD" if watchlist else "1px solid #2B3040"
    nome_exibicao = f"👁️ {titulo}" if watchlist else titulo
    return (
        f'<div class="mini-card {"mini-card-watch" if watchlist else ""}">'
        f'<div class="card-ticker">{nome_exibicao}</div>'
        f'<div class="card-preco">{prefixo}{valor}</div>'
        f'<div class="card-var {"var-positiva" if variacao >= 0 else "var-negativa"}">{sinal}{pct:.2f}%</div>'
        f'</div>'
    )

cartoes = []
if indices:
    if "IBOV" in indices:
        cartoes.append(("Ibovespa", f"{indices['IBOV']['preco']:,.0f}", indices['IBOV']['var'], indices['IBOV']['pct'], "", False))
    if "USD" in indices:
        cartoes.append(("Dólar", f"{indices['USD']['preco']:.4f}", indices['USD']['var'], indices['USD']['pct'], "R$ ", False))
    if "BTC" in indices:
        cartoes.append(("Bitcoin", f"{indices['BTC']['preco']:,.0f}", indices['BTC']['var'], indices['BTC']['pct'], "R$ ", False))

ativos_com_carteira = {}
for a in st.session_state["carteira"]:
    if a["Ticker"] != "CAIXA":
        ativos_com_carteira[a["Ticker"]] = a.get("Carteira", "COMPRAS (Real)")

ativos_ativos = list(ativos_com_carteira.keys())
precos_lote = buscar_cotacoes_lote(ativos_ativos)

for ticker in ativos_ativos:
    info = precos_lote.get(ticker)
    if info and info["preco"]:
        is_watch = ativos_com_carteira[ticker].upper() in CARTEIRAS_FORA_DO_PATRIMONIO
        cartoes.append((ticker, f"{info['preco']:.2f}", info['var'], info['pct'], "R$ ", is_watch))

COLUNAS_POR_LINHA = 10  # 🚀 Ajustado para 10 colunas para deixar os cards ainda menores horizontalmente
if cartoes:
    for i in range(0, len(cartoes), COLUNAS_POR_LINHA):
        cols_topo = st.columns(COLUNAS_POR_LINHA)
        for j in range(COLUNAS_POR_LINHA):
            if i + j < len(cartoes):
                titulo, valor, var, pct, prefixo, is_watch = cartoes[i+j]
                with cols_topo[j]:
                    st.markdown(criar_cartao_html(titulo, valor, var, pct, prefixo, is_watch), unsafe_allow_html=True)

# ==========================================
# --- 5. ESTRUTURA PRINCIPAL NIVELADA ---
# ==========================================
col_esq, col_dir = st.columns([1.2, 1.0], gap="large")

with col_esq:
    st.subheader("🌐 Panorama do Mercado")
    ativos_reais_grafico = [a["Ticker"] for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA" and eh_patrimonio_real(a)]
    opcoes_grafico = {"Ibovespa": "BMFBOVESPA:IBOV"}
    for ativo in set(ativos_reais_grafico): opcoes_grafico[ativo] = f"BMFBOVESPA:{ativo}"
    grafico_escolhido = st.selectbox("Gráfico Principal:", list(opcoes_grafico.keys()), label_visibility="collapsed")
    
    codigo_grafico_avancado = f"""
    <div class="tradingview-widget-container" style="height:400px;width:100%">
      <div id="tradingview_chart" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{"autosize": true, "symbol": "{opcoes_grafico[grafico_escolhido]}", "interval": "D", "timezone": "America/Sao_Paulo", "theme": "dark", "style": "1", "locale": "br", "container_id": "tradingview_chart", "backgroundColor": "#161A25"}});
      </script>
    </div>
    """
    components.html(codigo_grafico_avancado, height=400)

    st.divider()
    st.subheader("📊 Distribuição do Patrimônio Global")
    df_global = pd.DataFrame([a for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA" and eh_patrimonio_real(a)])
    if not df_global.empty:
        df_grp_global = df_global.groupby('Ticker').agg({'Quantidade': 'sum'}).reset_index()
        precos_global = buscar_cotacoes_lote(df_grp_global['Ticker'].tolist())
        lista_graf = []
        for _, row in df_grp_global.iterrows():
            g_info = precos_global.get(row['Ticker'])
            if g_info and g_info['preco']:
                patrimonio = row['Quantidade'] * g_info['preco']
                cat = 'FIIs' if row['Ticker'].endswith('11') else 'Ações'
                lista_graf.append({'Ativo': row['Ticker'], 'Patrimônio': patrimonio, 'Categoria': cat})
        if lista_graf:
            df_g = pd.DataFrame(lista_graf)
            c_pie, c_bar = st.columns(2)
            fig_pie = px.pie(df_g.groupby('Categoria')['Patrimônio'].sum().reset_index(), values='Patrimônio', names='Categoria', hole=0.5, color_discrete_sequence=['#00c698', '#1b4d3e'])
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            c_pie.plotly_chart(fig_pie, use_container_width=True)
            
            fig_bar = px.bar(df_g.sort_values(by="Patrimônio", ascending=False), x='Ativo', y='Patrimônio', color='Categoria', text_auto='.2s', color_discrete_map={"Ações": "#1b4d3e", "FIIs": "#00c698"})
            fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', font_color="white")
            c_bar.plotly_chart(fig_bar, use_container_width=True)

with col_dir:
    # 🚀 Nivelado perfeitamente com o início do Panorama do Mercado à esquerda
    abas = st.tabs(carteiras_existentes)
    for i, nome_carteira in enumerate(carteiras_existentes):
        with abas[i]:
            dados_aba = [a for a in st.session_state["carteira"] if a.get("Carteira", "COMPRAS (Real)") == nome_carteira and a["Ticker"] != "CAIXA"]
            if not dados_aba:
                st.info("Carteira vazia.")
                continue

            df_ledger = pd.DataFrame(dados_aba)
            df_ledger["Custo"] = df_ledger["Quantidade"] * df_ledger["Preço Pago"]
            df_agrupado = df_ledger.groupby('Ticker').agg({'Quantidade': 'sum', 'Custo': 'sum', 'Data da Compra': 'last'}).reset_index()
            df_agrupado['Preço Médio'] = df_agrupado.apply(lambda r: r['Custo'] / r['Quantidade'] if r['Quantidade'] > 0 else 0, axis=1)

            precos_aba = buscar_cotacoes_lote(df_agrupado['Ticker'].tolist())
            tabelas, tot_inv, tot_atu = [], 0, 0

            for _, row in df_agrupado.iterrows():
                tk, qtd, pm, cst, dt = row['Ticker'], row['Quantidade'], row['Preço Médio'], row['Custo'], row['Data da Compra']
                inf_aba = precos_aba.get(tk)
                if inf_aba and inf_aba['preco']:
                    v_atu = qtd * inf_aba['preco']
                    lucro = v_atu - cst
                    tot_inv += cst
                    tot_atu += v_atu
                    tabelas.append({"Ativo": tk, "Qtd": int(qtd), "Preço Médio": f"R$ {pm:.2f}", "Custo Total": f"R$ {cst:.2f}", "Lucro/Prejuízo": lucro, "Rent. (%)": (lucro/cst)*100 if cst > 0 else 0, "Data": dt})

            if tabelas:
                df_view = pd.DataFrame(tabelas)
                styled = df_view.style.format({"Lucro/Prejuízo": "R$ {:+.2f}", "Rent. (%)": "{:+.2f}%"}).map(lambda v: f"color: {'#00e676' if v > 0 else '#ff4b4b'}; font-weight: bold;" if isinstance(v, (int, float)) else '', subset=["Lucro/Prejuízo", "Rent. (%)"])
                st.dataframe(styled, use_container_width=True, hide_index=True)

                if nome_carteira.upper() not in CARTEIRAS_FORA_DO_PATRIMONIO:
                    st.markdown("### Resumo Global")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Totalmente Investido", f"R$ {tot_inv:,.2f}")
                    c2.metric("Patrimônio Atual", f"R$ {tot_atu:,.2f}", f"R$ {tot_atu - tot_inv:,.2f}")
                    c3.metric("Rentabilidade Geral", f"{(((tot_atu - tot_inv) / tot_inv) * 100 if tot_inv > 0 else 0):.2f}%")

                st.markdown("### Evolução do Ativo")
                ativo_graf_aba = st.selectbox("Selecione o ativo:", df_agrupado['Ticker'].tolist(), key=f"sel_{nome_carteira}")
                df_hist = buscar_historico(ativo_graf_aba)
                
                if not df_hist.empty:
                    fig_linha = px.line(df_hist, x='Data', y='Preço')
                    pm_ativo = df_agrupado[df_agrupado['Ticker'] == ativo_graf_aba]['Preço Médio'].values[0]
                    fig_linha.add_hline(y=pm_ativo, line_dash="dash", line_color="#ff4b4b", annotation_text=f"PM: R$ {pm_ativo:.2f}")

                    compras_ativo = df_ledger[df_ledger['Ticker'] == ativo_graf_aba]
                    for _, compra in compras_ativo.iterrows():
                        try:
                            dt_plotly = datetime.strptime(compra['Data da Compra'], "%d/%m/%Y").strftime("%Y-%m-%d")
                            qtd = compra['Quantidade']
                            p_pago = compra['Preço Pago']
                            if qtd > 0:
                                fig_linha.add_vline(
                                    x=dt_plotly, 
                                    line_dash="dot", 
                                    line_color="#378ADD",
                                    annotation_text=f" {int(qtd)} un @ R$ {p_pago:.2f}",
                                    annotation_position="top right"
                                )
                        except Exception:
                            pass

                    fig_linha.update_layout(margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=250)
                    fig_linha.update_traces(line_color="#00c698")
                    st.plotly_chart(fig_linha, use_container_width=True)

    # --- PAINEL: MAIORES ALTAS E BAIXAS ---
    st.markdown("<br>", unsafe_allow_html=True)
    altas, baixas, _ = buscar_destaques_mercado()
    html_painel = """<style>.market-panel { background-color: #161A25; border: 1px solid #2B3040; border-radius: 8px; padding: 20px; display: flex; gap: 20px; margin-top: 10px; } .market-col { flex: 1; } .market-col:first-child { border-right: 1px solid #2B3040; padding-right: 20px; } .market-title { font-size: 16px; font-weight: bold; margin-bottom: 15px; } .title-up { color: #00e676; } .title-down { color: #ff4b4b; } .market-row { display: flex; justify-content: space-between; padding: 8px 0; font-size: 15px; } .m-ticker { color: #2196F3; font-weight: bold; } .m-var-up { color: #00e676; font-weight: bold; } .m-var-down { color: #ff4b4b; font-weight: bold; } .btn-mais { display: block; text-align: center; background-color: #0066cc; color: white !important; padding: 12px; border-radius: 30px; text-decoration: none; font-weight: bold; margin-top: 20px; }</style><div class="market-panel"><div class="market-col"><div class="market-title title-up">⬆️ Maiores altas</div>"""
    if altas:
        for item in altas: html_painel += f"<div class='market-row'><span class='m-ticker'>{item['Ativo']}</span><span class='m-var-up'>+{item['Var%']:.2f}%</span><span style='color:white;'>R$ {item['Preço']:.2f}</span></div>"
    html_painel += """</div><div class="market-col"><div class="market-title title-down">⬇️ Maiores baixas</div>"""
    if baixas:
        for item in baixas: html_painel += f"<div class='market-row'><span class='m-ticker'>{item['Ativo']}</span><span class='m-var-down'>{item['Var%']:.2f}%</span><span style='color:white;'>R$ {item['Preço']:.2f}</span></div>"
    html_painel += """</div></div><a href="https://statusinvest.com.br/acoes/alta-e-baixa" target="_blank" class="btn-mais">Ver mais cotações</a>"""
    st.markdown(html_painel, unsafe_allow_html=True)
