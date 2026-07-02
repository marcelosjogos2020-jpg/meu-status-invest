import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import streamlit.components.v1 as components
from datetime import date

# Configuração da página (deve ser a primeira linha do Streamlit)
st.set_page_config(page_title="Meu Portfólio", layout="wide")

# ==========================================
# --- 1. INICIALIZAÇÃO DO SESSION STATE ---
# ==========================================
if "tabela" not in st.session_state:
    st.session_state["tabela"] = []
if "carteiras_tabs" not in st.session_state:
    st.session_state["carteiras_tabs"] = ["COMPRAS", "COMPRAS-FUTURAS"]
if "dados_globais" not in st.session_state:
    st.session_state["dados_globais"] = []

# ==========================================
# --- 2. FUNÇÕES AUXILIARES (DADOS API) ---
# ==========================================
@st.cache_data(ttl=300) # Atualiza a cada 5 minutos
def buscar_cotacao_completa(ticker):
    try:
        ticker_sa = ticker if ticker.endswith('.SA') else f"{ticker}.SA"
        acao = yf.Ticker(ticker_sa)
        hist = acao.history(period="5d")
        if len(hist) < 2:
            return None
            
        preco_atual = hist['Close'].iloc[-1]
        preco_anterior = hist['Close'].iloc[-2]
        abertura = hist['Open'].iloc[-1]
        maxima = hist['High'].iloc[-1]
        minima = hist['Low'].iloc[-1]
        volume = hist['Volume'].iloc[-1]
        
        variacao = preco_atual - preco_anterior
        variacao_pct = (variacao / preco_anterior) * 100
        
        # Formata o volume para 'M' (Milhões) ou 'K' (Milhares)
        if volume >= 1000000:
            vol_formatado = f"{volume/1000000:.2f}M"
        elif volume >= 1000:
            vol_formatado = f"{volume/1000:.2f}K"
        else:
            vol_formatado = str(volume)
            
        return {
            "preco": preco_atual,
            "abertura": abertura,
            "maxima": maxima,
            "minima": minima,
            "volume": vol_formatado,
            "variacao": variacao,
            "variacao_pct": variacao_pct
        }
    except:
        return None

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

@st.cache_data(ttl=300)
def buscar_ibov_dolar():
    try:
        ibov = yf.Ticker("^BVSP").history(period="5d")
        dolar = yf.Ticker("BRL=X").history(period="5d")
        
        ibov_atual = ibov['Close'].iloc[-1]
        ibov_var = ibov_atual - ibov['Close'].iloc[-2]
        ibov_pct = (ibov_var / ibov['Close'].iloc[-2]) * 100
        
        dol_atual = dolar['Close'].iloc[-1]
        dol_var = dol_atual - dolar['Close'].iloc[-2]
        dol_pct = (dol_var / dolar['Close'].iloc[-2]) * 100
        
        return {
            "IBOV": {"preco": ibov_atual, "var": ibov_var, "pct": ibov_pct},
            "USD": {"preco": dol_atual, "var": dol_var, "pct": dol_pct}
        }
    except:
        return None

# ==========================================
# --- 3. MENU LATERAL (ADICIONAR ATIVOS) ---
# ==========================================
with st.sidebar:
    st.header("🛒 Adicionar Ativo")
    novo_ticker = st.text_input("Ticker (ex: BBAS3)").upper()
    novo_qnt = st.number_input("Quantidade", min_value=1, value=10)
    novo_preco = st.number_input("Preço Pago (R$)", min_value=0.01, value=20.00, step=0.1)
    nova_data = st.date_input("Data da Compra", date.today())
    nova_carteira = st.selectbox("Carteira", st.session_state["carteiras_tabs"])
    
    if st.button("Adicionar à Carteira", use_container_width=True):
        if novo_ticker:
            st.session_state["tabela"].append({
                "Ticker": novo_ticker,
                "Quantidade": novo_qnt,
                "Preço Pago": novo_preco,
                "Data da Compra": nova_data.strftime("%d/%m/%Y"),
                "Carteira": nova_carteira
            })
            st.success(f"{novo_ticker} adicionado!")
            st.rerun()

    st.divider()
    st.header("📂 Nova Carteira")
    nova_aba = st.text_input("Nome da Nova Carteira").upper()
    if st.button("Criar Carteira", use_container_width=True):
        if nova_aba and nova_aba not in st.session_state["carteiras_tabs"]:
            st.session_state["carteiras_tabs"].append(nova_aba)
            st.success(f"Carteira {nova_aba} criada!")
            st.rerun()

# ==========================================
# --- 4. TOPO: LETREIRO ROTATIVO (MARQUEE) ---
# ==========================================
indices = buscar_ibov_dolar()
if indices:
    # Montando a string de HTML para o letreiro passando
    html_marquee = """
    <style>
        .ticker-wrap { width: 100%; overflow: hidden; background-color: #1E1E1E; padding: 10px 0; border-radius: 8px; border: 1px solid #333; margin-bottom: 20px;}
        .ticker-text { font-size: 16px; font-family: sans-serif; color: #FFFFFF; font-weight: 500;}
        .positivo { color: #00e676; }
        .negativo { color: #ff4b4b; }
        .divisor { margin: 0 20px; color: #555; }
    </style>
    <div class="ticker-wrap">
        <marquee behavior="scroll" direction="left" scrollamount="6" class="ticker-text">
    """
    
    # Adiciona IBOV
    cor_ibov = "positivo" if indices["IBOV"]["var"] >= 0 else "negativo"
    sinal_ibov = "+" if indices["IBOV"]["var"] >= 0 else ""
    html_marquee += f"<b>IBOV</b> {indices['IBOV']['preco']:,.0f}pts <span class='{cor_ibov}'>{sinal_ibov}{indices['IBOV']['var']:,.0f} ({sinal_ibov}{indices['IBOV']['pct']:.2f}%)</span> <span class='divisor'>|</span> "
    
    # Adiciona DOLAR
    cor_usd = "positivo" if indices["USD"]["var"] >= 0 else "negativo"
    sinal_usd = "+" if indices["USD"]["var"] >= 0 else ""
    html_marquee += f"<b>DÓLAR</b> R$ {indices['USD']['preco']:.4f} <span class='{cor_usd}'>{sinal_usd}{indices['USD']['var']:.4f} ({sinal_usd}{indices['USD']['pct']:.2f}%)</span> <span class='divisor'>|</span> "

    # Adiciona os ativos que o usuário já tem na carteira no letreiro
    ativos_unicos = list(set([d["Ticker"] for d in st.session_state["tabela"]]))
    for ticker in ativos_unicos: 
        info = buscar_cotacao_completa(ticker)
        if info:
            cor_ativo = "positivo" if info["variacao"] >= 0 else "negativo"
            sinal_ativo = "+" if info["variacao"] >= 0 else ""
            html_marquee += f"<b>{ticker}</b> R$ {info['preco']:.2f} <span class='{cor_ativo}'>{sinal_ativo}{info['variacao']:.2f} ({sinal_ativo}{info['variacao_pct']:.2f}%)</span> <span class='divisor'>|</span> "
            
    html_marquee += "</marquee></div>"
    st.markdown(html_marquee, unsafe_allow_html=True)


st.title("📈 Meu Portfólio & Acompanhamento")

# ==========================================
# --- 5. GRÁFICO INTERATIVO TRADINGVIEW  ---
# ==========================================
st.subheader("🌐 Panorama do Mercado e Seus Ativos")

opcoes_grafico = {"Mercado Geral (Ibovespa)": "BMFBOVESPA:IBOV"}
ativos_graf = list(set([ativo["Ticker"] for ativo in st.session_state["tabela"]]))

for ativo in ativos_graf:
    opcoes_grafico[ativo] = f"BMFBOVESPA:{ativo}"

grafico_escolhido = st.selectbox("Qual gráfico você quer ver?", list(opcoes_grafico.keys()))
simbolo_tv = opcoes_grafico[grafico_escolhido]

codigo_grafico_avancado = f"""
<div class="tradingview-widget-container" style="height:450px;width:100%">
  <div id="tradingview_chart" style="height:calc(100% - 32px);width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
  "autosize": true,
  "symbol": "{simbolo_tv}",
  "interval": "D",
  "timezone": "America/Sao_Paulo",
  "theme": "dark",
  "style": "1",
  "locale": "br",
  "enable_publishing": false,
  "backgroundColor": "rgba(19, 23, 34, 1)",
  "gridColor": "rgba(42, 46, 57, 0.06)",
  "hide_top_toolbar": false,
  "hide_legend": false,
  "save_image": false,
  "container_id": "tradingview_chart",
  "toolbar_bg": "#f1f3f6"
}}
  );
  </script>
</div>
"""
components.html(codigo_grafico_avancado, height=450)
st.divider()

# ==========================================
# --- 6. ABAS DAS CARTEIRAS ESTILO INVESTING ---
# ==========================================
abas = st.tabs(st.session_state["carteiras_tabs"])

for i, carteira_nome in enumerate(st.session_state["carteiras_tabs"]):
    with abas[i]:
        st.subheader(f"Lista de Ativos: {carteira_nome}")
        
        carteira_atual = [d for d in st.session_state["tabela"] if d["Carteira"] == carteira_nome]
        
        if not carteira_atual:
            st.info("Carteira vazia. Adicione ativos pelo menu lateral.")
            continue
            
        df = pd.DataFrame(carteira_atual)
        df['Custo Total'] = df['Quantidade'] * df['Preço Pago']
        
        tabelas = []
        total_investido = 0
        total_atual = 0
        
        for idx, row in df.iterrows():
            ticker = row['Ticker']
            qnt = row['Quantidade']
            preco_pago = row['Preço Pago']
            custo = row['Custo Total']
            
            info = buscar_cotacao_completa(ticker)
            if info:
                preco_atual = info['preco']
                v_atual = qnt * preco_atual
                lucro = v_atual - custo
                
                total_investido += custo
                total_atual += v_atual
                
                tabelas.append({
                    "Códigos": ticker,
                    "Último": preco_atual,
                    "Abertura": info['abertura'],
                    "Máxima": info['maxima'],
                    "Mínima": info['minima'],
                    "Variação": info['variacao'],
                    "Var%": info['variacao_pct']/100,
                    "Vol.": info['volume'],
                    "Qtd": int(qnt),
                    "Preço Pago": preco_pago,
                    "Lucro/Prej.": lucro
                })
                
        if tabelas:
            df_view = pd.DataFrame(tabelas)
            
            def style_row(val):
                if pd.isna(val):
                    return ''
                color = '#00e676' if val > 0 else '#ff4b4b' 
                return f'color: {color}; font-weight: bold;'
                
            styled = df_view.style.format({
                "Último": "{:.2f}",
                "Abertura": "{:.2f}",
                "Máxima": "{:.2f}",
                "Mínima": "{:.2f}",
                "Variação": "{:+.2f}",
                "Var%": "{:+.2%}",
                "Preço Pago": "R$ {:.2f}",
                "Lucro/Prej.": "R$ {:+.2f}"
            }).map(
                lambda v: style_row(v) if isinstance(v, (int, float)) and v != 0 else '', 
                subset=["Variação", "Var%", "Lucro/Prej."]
            )
            
            st.dataframe(styled, use_container_width=True, hide_index=True)
            
            # --- Resumo da Carteira ---
            st.write("---")
            col1, col2, col3 = st.columns(3)
            resultado = total_atual - total_investido
            rent = (resultado/total_investido)*100 if total_investido > 0 else 0
            
            col1.metric("Investido nesta Carteira", f"R$ {total_investido:,.2f}")
            col2.metric("Patrimônio Atual", f"R$ {total_atual:,.2f}", f"R$ {resultado:,.2f}")
            col3.metric("Rentabilidade", f"{rent:.2f}%")
            
            # --- Histórico de 6 meses (Expander) ---
            with st.expander(f"📊 Ver Histórico e Gráficos ({carteira_nome})"):
                ativo_grafico = st.selectbox("Escolha o ativo para ver o gráfico de linha:", df['Ticker'].unique(), key=f"graf_{carteira_nome}")
                df_hist = buscar_historico(ativo_grafico)
                if not df_hist.empty:
                    p = px.line(df_hist, x='Data', y='Preço', title=f"Histórico de 6 Meses - {ativo_grafico}")
                    st.plotly_chart(p, use_container_width=True)
