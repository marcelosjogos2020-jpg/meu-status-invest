import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import streamlit.components.v1 as components
import requests
import urllib3
import os
from datetime import datetime

# --- DESLIGANDO ALERTAS DE SEGURANÇA ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Meu Portfólio", page_icon="📈", layout="wide")

# ==========================================
# --- 1. BANCO DE DADOS (CSV) ---
# ==========================================
ARQUIVO_BANCO = "minha_carteira.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO_BANCO):
        df = pd.read_csv(ARQUIVO_BANCO)
        if "Preço Médio" in df.columns:
            df = df.rename(columns={"Preço Médio": "Preço Pago"})
        if "Data da Compra" not in df.columns:
            df["Data da Compra"] = "Antes da Atualização"
        # --- NOVIDADE: Adiciona a coluna Carteira se for um arquivo antigo ---
        if "Carteira" not in df.columns:
            df["Carteira"] = "PRINCIPAL"
        return df.to_dict(orient="records")
    return []

def salvar_dados(dados):
    df = pd.DataFrame(dados)
    df.to_csv(ARQUIVO_BANCO, index=False)
    return df.to_dict(orient="records")

if "carteira" not in st.session_state:
    st.session_state["carteira"] = carregar_dados()

# ==========================================
# --- 2. FUNÇÕES DE DADOS (YFINANCE) ---
# ==========================================
@st.cache_data(ttl=60)
def buscar_cotacao_simples(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}.SA"
        cabecalho = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url, headers=cabecalho, verify=False, timeout=5)
        return float(resposta.json()['chart']['result'][0]['meta']['regularMarketPrice'])
    except:
        return None

@st.cache_data(ttl=300)
def buscar_cotacao_completa(ticker):
    try:
        ticker_sa = ticker if ticker.endswith('.SA') else f"{ticker}.SA"
        acao = yf.Ticker(ticker_sa)
        hist = acao.history(period="5d")
        if len(hist) < 2: return None
            
        preco_atual = hist['Close'].iloc[-1]
        preco_anterior = hist['Close'].iloc[-2]
        abertura = hist['Open'].iloc[-1]
        maxima = hist['High'].iloc[-1]
        minima = hist['Low'].iloc[-1]
        volume = hist['Volume'].iloc[-1]
        
        variacao = preco_atual - preco_anterior
        variacao_pct = (variacao / preco_anterior) * 100
        
        if volume >= 1000000: vol_formatado = f"{volume/1000000:.2f}M"
        elif volume >= 1000: vol_formatado = f"{volume/1000:.2f}K"
        else: vol_formatado = str(volume)
            
        return {
            "preco": preco_atual, "abertura": abertura, "maxima": maxima,
            "minima": minima, "volume": vol_formatado,
            "variacao": variacao, "variacao_pct": variacao_pct
        }
    except: return None

@st.cache_data(ttl=300)
def buscar_destaques_mercado():
    tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'B3SA3.SA', 'ABEV3.SA', 'WEGE3.SA', 'RENT3.SA', 'SUZB3.SA', 'RADL3.SA']
    resultados = []
    try:
        df = yf.download(tickers, period="5d", progress=False)['Close']
        df = df.dropna(axis=1, how='all')
        for ticker in df.columns:
            try:
                s = df[ticker].dropna()
                if len(s) >= 2:
                    p_ant, p_atu = s.iloc[-2], s.iloc[-1]
                    var_pct = ((p_atu - p_ant) / p_ant) * 100
                    resultados.append({"Ativo": ticker.replace(".SA", ""), "Preço": p_atu, "Var%": var_pct})
            except: pass
    except: pass
    res_sort = sorted(resultados, key=lambda x: x["Var%"], reverse=True)
    return res_sort[:4], sorted(res_sort[-4:], key=lambda x: x["Var%"])

@st.cache_data(ttl=3600)
def buscar_historico(ticker):
    try:
        ticker_sa = ticker if ticker.endswith('.SA') else f"{ticker}.SA"
        acao = yf.Ticker(ticker_sa)
        hist = acao.history(period="6mo")
        hist.reset_index(inplace=True)
        if hist['Date'].dt.tz is not None:
            hist['Date'] = hist['Date'].dt.tz_localize(None)
        return hist[['Date', 'Close']].rename(columns={'Date': 'Data', 'Close': 'Preço'})
    except:
        return pd.DataFrame()

# ==========================================
# --- 3. BARRA LATERAL (CRIAR E ESCOLHER CARTEIRAS) ---
# ==========================================
# Descobre quais carteiras já existem no banco de dados
carteiras_existentes = list(set([a.get("Carteira", "PRINCIPAL") for a in st.session_state["carteira"]]))
if "PRINCIPAL" not in carteiras_existentes: carteiras_existentes.insert(0, "PRINCIPAL")
if "WATCHLIST" not in carteiras_existentes: carteiras_existentes.append("WATCHLIST")

st.sidebar.header("🛒 Cadastrar Novo Aporte")

ticker_input = st.sidebar.text_input("Código do Ativo (Ex: PETR4)", value="PETR4").upper().strip()

preco_atual_sidebar = None
if ticker_input:
    with st.sidebar.spinner("Buscando preço..."):
        preco_atual_sidebar = buscar_cotacao_simples(ticker_input)
    if preco_atual_sidebar:
        st.sidebar.metric(label=f"Cotação Atual ({ticker_input})", value=f"R$ {preco_atual_sidebar:.2f}")

data_compra_input = st.sidebar.date_input("Data da Compra", value=datetime.today())
qtd_input = st.sidebar.number_input("Quantidade (0 para editar data)", min_value=0, value=10)

valor_padrao_preco = float(preco_atual_sidebar) if preco_atual_sidebar else 35.00
preco_medio_input = st.sidebar.number_input("Preço da Compra (R$)", min_value=0.01, value=valor_padrao_preco, step=0.01)

# NOVIDADE: Onde o usuário quer salvar essa ação?
carteira_selecionada = st.sidebar.selectbox("Em qual carteira deseja salvar?", carteiras_existentes)

total_simulado = qtd_input * preco_medio_input
st.sidebar.info(f"**Total da Ordem: R$ {total_simulado:,.2f}**")

col_btn1, col_btn2 = st.sidebar.columns(2)

if col_btn1.button("Salvar Ativo"):
    data_str = data_compra_input.strftime("%d/%m/%Y")
    if qtd_input > 0:
        st.session_state["carteira"].append({
            "Ticker": ticker_input, "Quantidade": qtd_input,
            "Preço Pago": preco_medio_input, "Data da Compra": data_str,
            "Carteira": carteira_selecionada # Salva na carteira escolhida
        })
    else:
        for ativo in reversed(st.session_state["carteira"]):
            if ativo["Ticker"] == ticker_input and ativo.get("Carteira", "PRINCIPAL") == carteira_selecionada:
                ativo["Data da Compra"] = data_str
                break
    st.session_state["carteira"] = salvar_dados(st.session_state["carteira"])
    st.sidebar.success(f"{ticker_input} salvo na {carteira_selecionada}!")
    st.rerun()

if col_btn2.button("Limpar Tudo"):
    st.session_state["carteira"] = []
    if os.path.exists(ARQUIVO_BANCO): os.remove(ARQUIVO_BANCO)
    st.rerun()

st.sidebar.divider()
st.sidebar.header("📂 Criar Nova Carteira")
nova_carteira_input = st.sidebar.text_input("Nome da Nova Carteira").upper()
if st.sidebar.button("Criar Carteira", use_container_width=True):
    if nova_carteira_input and nova_carteira_input not in carteiras_existentes:
        # Salva um ativo 'vazio' só para registrar a carteira no banco
        st.session_state["carteira"].append({
            "Ticker": "CAIXA", "Quantidade": 0, "Preço Pago": 0, 
            "Data da Compra": datetime.today().strftime("%d/%m/%Y"), "Carteira": nova_carteira_input
        })
        st.session_state["carteira"] = salvar_dados(st.session_state["carteira"])
        st.sidebar.success(f"Carteira {nova_carteira_input} criada!")
        st.rerun()

# ==========================================
# --- 4. TOPO: LETREIRO OFICIAL TRADINGVIEW ---
# ==========================================
st.title("📈 Meu Portfólio & Acompanhamento")

ativos_tv = ""
if len(st.session_state["carteira"]) > 0:
    ativos_unicos = list(set([a["Ticker"] for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA"]))
    for ativo in ativos_unicos[:10]:
        ativos_tv += f'{{"proName": "BMFBOVESPA:{ativo}", "title": "{ativo}"}},'

codigo_letreiro = f"""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {{
  "symbols": [
    {{"proName": "BMFBOVESPA:IBOV", "title": "Ibovespa"}},
    {{"proName": "FX_IDC:USDBRL", "title": "Dólar"}},
    {{"proName": "BINANCE:BTCBRL", "title": "Bitcoin"}},
    {ativos_tv[:-1]}
  ],
  "showSymbolLogo": true, "isTransparent": true, "displayMode": "adaptive", "colorTheme": "dark", "locale": "br"
}}
  </script>
</div>
"""
components.html(codigo_letreiro, height=75)

# ==========================================
# --- 5. GRÁFICO E RANKING (LADO A LADO) ---
# ==========================================
st.subheader("🌐 Panorama do Mercado e Seus Ativos")

opcoes_grafico = {"Mercado Geral (Ibovespa)": "BMFBOVESPA:IBOV"}
ativos_graf = list(set([ativo["Ticker"] for ativo in st.session_state["carteira"] if ativo["Ticker"] != "CAIXA"]))
for ativo in ativos_graf: opcoes_grafico[ativo] = f"BMFBOVESPA:{ativo}"

grafico_escolhido = st.selectbox("Qual gráfico você quer ver?", list(opcoes_grafico.keys()))
simbolo_tv = opcoes_grafico[grafico_escolhido]

col_grafico, col_ranking = st.columns([1.5, 1.0], gap="large")

with col_grafico:
    codigo_grafico_avancado = f"""
    <div class="tradingview-widget-container" style="height:420px;width:100%">
      <div id="tradingview_chart" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{"autosize": true, "symbol": "{simbolo_tv}", "interval": "D", "timezone": "America/Sao_Paulo", "theme": "dark", "style": "1", "locale": "br", "enable_publishing": false, "backgroundColor": "rgba(19, 23, 34, 1)", "gridColor": "rgba(42, 46, 57, 0.06)", "hide_top_toolbar": false, "hide_legend": false, "save_image": false, "container_id": "tradingview_chart", "toolbar_bg": "#f1f3f6"}});
      </script>
    </div>
    """
    components.html(codigo_grafico_avancado, height=420)

with col_ranking:
    altas, baixas = buscar_destaques_mercado()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h4 style='color: #00e676; margin-bottom: 5px;'>⬆️ Maiores Altas</h4>", unsafe_allow_html=True)
        for item in altas: st.markdown(f"**{item['Ativo']}**: R$ {item['Preço']:.2f} (<span style='color:#00e676'>+{item['Var%']:.2f}%</span>)", unsafe_allow_html=True)
    with c2:
        st.markdown("<h4 style='color: #ff4b4b; margin-bottom: 5px;'>⬇️ Maiores Baixas</h4>", unsafe_allow_html=True)
        for item in baixas: st.markdown(f"**{item['Ativo']}**: R$ {item['Preço']:.2f} (<span style='color:#ff4b4b'>{item['Var%']:.2f}%</span>)", unsafe_allow_html=True)

st.divider()

# ==========================================
# --- 6. ABAS DE CARTEIRAS (TABS) ---
# ==========================================
# Cria as abas visuais com os nomes das carteiras existentes
abas = st.tabs(carteiras_existentes)

# Para cada aba, renderiza os dados daquela carteira
for i, nome_carteira in enumerate(carteiras_existentes):
    with abas[i]:
        st.subheader(f"💼 Posição Consolidada: {nome_carteira}")
        
        # Filtra os dados só dessa carteira (e ignora o ativo falso "CAIXA" usado pra criar abas vazias)
        dados_aba = [a for a in st.session_state["carteira"] if a.get("Carteira", "PRINCIPAL") == nome_carteira and a["Ticker"] != "CAIXA"]
        
        if len(dados_aba) == 0:
            st.info(f"A carteira '{nome_carteira}' está vazia. Cadastre seus ativos no menu lateral escolhendo esta carteira!")
            continue
            
        df_ledger = pd.DataFrame(dados_aba)
        df_ledger["Custo da Operação"] = df_ledger["Quantidade"] * df_ledger["Preço Pago"]
        
        df_agrupado = df_ledger.groupby('Ticker').agg({'Quantidade': 'sum', 'Custo da Operação': 'sum'}).reset_index()
        df_agrupado['Preço Médio'] = df_agrupado.apply(lambda row: row['Custo da Operação'] / row['Quantidade'] if row['Quantidade'] > 0 else 0, axis=1)
        
        tabelas = []
        total_investido, total_atual = 0, 0
        
        with st.spinner(f"Atualizando {nome_carteira}..."):
            for idx, row in df_agrupado.iterrows():
                ticker, qnt, preco_medio, custo = row['Ticker'], row['Quantidade'], row['Preço Médio'], row['Custo da Operação']
                info = buscar_cotacao_completa(ticker)
                
                if info:
                    v_atual = qnt * info['preco']
                    lucro = v_atual - custo
                    total_investido += custo
                    total_atual += v_atual
                    
                    tabelas.append({
                        "Códigos": ticker, "Último": info['preco'],
                        "Abertura": info['abertura'], "Máxima": info['maxima'], "Mínima": info['minima'],
                        "Variação": info['variacao'], "Var%": info['variacao_pct']/100, "Vol.": info['volume'],
                        "Qtd": int(qnt), "Preço Médio": preco_medio, "Patrimônio": v_atual, "Lucro/Prej.": lucro
                    })
                    
        if tabelas:
            df_view = pd.DataFrame(tabelas)
            def style_row(val):
                if pd.isna(val) or val == '': return ''
                color = '#00e676' if val > 0 else '#ff4b4b' 
                return f'color: {color}; font-weight: bold;'
                
            styled = df_view.style.format({
                "Último": "R$ {:.2f}", "Abertura": "R$ {:.2f}", "Máxima": "R$ {:.2f}", "Mínima": "R$ {:.2f}",
                "Variação": "{:+.2f}", "Var%": "{:+.2%}", "Preço Médio": "R$ {:.2f}", "Patrimônio": "R$ {:.2f}", "Lucro/Prej.": "R$ {:+.2f}"
            }).map(lambda v: style_row(v) if isinstance(v, (int, float)) and v != 0 else '', subset=["Variação", "Var%", "Lucro/Prej."])
            
            st.dataframe(styled, use_container_width=True, hide_index=True)
            
            with st.expander("🛒 Ver Histórico Detalhado de Compras (Livro de Ordens)"):
                df_historico_tela = df_ledger[["Data da Compra", "Ticker", "Quantidade", "Preço Pago", "Custo da Operação"]].copy()
                df_historico_tela["Preço Pago"] = df_historico_tela["Preço Pago"].apply(lambda x: f"R$ {x:,.2f}")
                df_historico_tela["Custo da Operação"] = df_historico_tela["Custo da Operação"].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(df_historico_tela, use_container_width=True, hide_index=True)
            
            st.divider()
            col1, col2, col3 = st.columns(3)
            resultado = total_atual - total_investido
            rent = (resultado/total_investido)*100 if total_investido > 0 else 0
            col1.metric("Totalmente Investido", f"R$ {total_investido:,.2f}")
            col2.metric("Patrimônio Atual", f"R$ {total_atual:,.2f}", f"R$ {resultado:,.2f}")
            col3.metric("Rentabilidade da Carteira", f"{rent:.2f}%")
            
            # --- DISTRIBUIÇÃO E GRÁFICOS DESSA CARTEIRA ---
            st.subheader(f"📊 Distribuição ({nome_carteira})")
            col_graf1, col_graf2 = st.columns(2)
            
            # Adiciona a Categoria FIIs vs Ações para os gráficos
            for t in tabelas:
                t['Categoria'] = 'FIIs' if t['Códigos'].endswith('11') else 'Ações'
                
            df_graficos = pd.DataFrame(tabelas)
            
            df_pizza = df_graficos.groupby('Categoria')['Patrimônio'].sum().reset_index()
            fig_pizza = px.pie(df_pizza, values='Patrimônio', names='Categoria', hole=0.4, title="Ações vs FIIs", color_discrete_sequence=['#00c698', '#1b4d3e'])
            col_graf1.plotly_chart(fig_pizza, use_container_width=True)
            
            df_graficos = df_graficos.sort_values(by="Patrimônio", ascending=False)
            fig_barras = px.bar(df_graficos, x='Códigos', y='Patrimônio', color='Categoria', title="Patrimônio por Ativo", text_auto='.2s', color_discrete_map={"Ações": "#1b4d3e", "FIIs": "#00c698"})
            col_graf2.plotly_chart(fig_barras, use_container_width=True)
