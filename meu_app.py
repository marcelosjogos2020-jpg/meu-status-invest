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
# (Mantido como no código original fornecido)
# Lista mockada de tickers comuns da B3 para exemplo
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
# (Mantido como no código original fornecido)
# ...

def carregar_dados():
    # (Mantido como no código original fornecido)
    # ...
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
    # (Mantido como no código original fornecido)
    # ...
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
def buscar_cotacoes(tickers):
    # (Mantido como no código original fornecido)
    # ...
    if not tickers:
        return {}
    # (Yahoo Finance precisa de .SA para B3)
    tickers_sa = [t if t.endswith(('.SA', '-BRL', '=X', '^')) else f"{t}.SA" for t in tickers]
    precos = {}
    try:
        dados = yf.download(tickers=tickers_sa, period="1d", progress=False)
        for t, t_sa in zip(tickers, tickers_sa):
            try:
                # Tratar se houver MultiIndex nas colunas (download de múltiplos ativos)
                if isinstance(dados.columns, pd.MultiIndex):
                    if t_sa in dados.columns.get_level_values(1):
                        df_ticker = dados.xs(t_sa, level=1, axis=1)
                    else:
                        # Fallback se não encontrar o ticker exato
                        df_ticker = dados[t_sa] if t_sa in dados.columns else None
                else:
                    df_ticker = dados[t_sa] if t_sa in dados.columns else dados

                if df_ticker is not None and not df_ticker.empty:
                    # Tentar pegar o fechamento mais recente
                    preco_atual = float(df_ticker['Close'].iloc[-1])
                    precos[t] = preco_atual
                else:
                    precos[t] = None
            except Exception:
                precos[t] = None
        return precos
    except Exception:
        # Fallback se download geral falhar
        return {t: None for t in tickers}

@st.cache_data(ttl=300)
def buscar_historico(ticker):
    # (Mantido como no código original fornecido)
    # ...
    try:
        # Yahoo Finance precisa de .SA para B3
        ticker_sa = ticker if ticker.endswith('.SA') else f"{ticker}.SA"
        hist = yf.Ticker(ticker_sa).history(period="6mo")
        hist.reset_index(inplace=True)
        # Limpar fuso horário se houver, para Plotly
        if hist['Date'].dt.tz is not None:
            hist['Date'] = hist['Date'].dt.tz_localize(None)
        return hist[['Date', 'Close']].rename(columns={'Date': 'Data', 'Close': 'Preço'})
    except Exception:
        return pd.DataFrame() # Retorna vazio se falhar

# ==========================================
# --- 3. BARRA LATERAL ---
# ==========================================
# (Mantido como no código original fornecido)
# ...
carteiras_existentes = list(set([a.get("Carteira", "COMPRAS (Real)") for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA"]))
if "COMPRAS (Real)" not in carteiras_existentes: carteiras_existentes.insert(0, "COMPRAS (Real)")
if "WATCHLIST" not in carteiras_existentes: carteiras_existentes.append("WATCHLIST")

with st.sidebar:
    st.header("🛒 Adicionar Ativo")
    #st.subheader("Buscar Ticker na B3")
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
            preco_atual_sidebar = buscar_cotacoes([ticker_input]).get(ticker_input)
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
        # Adicionar ativo ao banco de dados CSV
        data_str = data_compra_input.strftime("%d/%m/%Y")
        if qtd_input > 0:
            st.session_state["carteira"].append({
                "Ticker": ticker_input, "Quantidade": qtd_input, 
                "Preço Pago": preco_medio_input, "Data da Compra": data_str,
                "Carteira": carteira_selecionada
            })
        else:
            # Encontrar o ativo e editar apenas a data se quantidade for 0
            # Isso é uma lógica simples, pode ser melhorada
            for ativo in st.session_state["carteira"]:
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
# (Mantido como no código original fornecido)
# ...

# Obter tickers únicos para o letreiro
ativos_unicos = list(set([a["Ticker"] for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA"]))
# Criar a lista de símbolos para o widget do TradingView
simbolos_letreiro = [
    {"proName": "BMFBOVESPA:IBOV", "title": "Ibovespa"},
    {"proName": "FX_IDC:USDBRL", "title": "Dólar"},
    {"proName": "BINANCE:BTCBRL", "title": "Bitcoin"}
]
# Adicionar até 10 ativos da carteira
for ativo in ativos_unicos[:10]:
    simbolos_letreiro.append({"proName": f"BMFBOVESPA:{ativo}", "title": ativo})

codigo_letreiro = f"""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {{
  "symbols": {json.dumps(simbolos_letreiro)},
  "showSymbolLogo": true,
  "isTransparent": true,
  "displayMode": "adaptive",
  "colorTheme": "dark",
  "locale": "br"
}}
  </script>
</div>
"""
components.html(codigo_letreiro, height=75)

# ==========================================
# --- 4. TOPO: CARTÕES SUPER COMPACTOS (CORREÇÃO PEDIDA) ---
# ==========================================
#st.title("Meu Portfólio & Acompanhamento") # Anterior
st.markdown("### Meu Portfólio & Acompanhamento", unsafe_allow_html=True) # Título de seção menor

# Dados mockados baseados na imagem para recriação precisa
mock_precos = {
    'BBAS3': {'preco': 20.09, 'var': 0.09, 'pct': 0.45},
    'HSAF11': {'preco': 77.89, 'var': -0.42, 'pct': -0.54}
}

# Layout de 4 colunas para mini-cards supercompactos
top_cols = st.columns(4)

# Função para criar um mini-card de ativo supercompacto
def criar_mini_card(ticker, preco, var, pct):
    cor_classe = "var-positiva" if var >= 0 else "var-negativa"
    sinal = "+" if var >= 0 else ""
    card_html = f"""
    <div class="mini-card">
        <div class="card-ticker">{ticker}</div>
        <div class="card-preco">R$ {preco:.2f}</div>
        <div class="card-var {cor_classe}">
            {sinal}{var:.2f} ({sinal}{pct:.2f}%)
        </div>
    </div>
    """
    return card_html

# Adicionar o CSS customizado para os mini-cards
st.markdown("""
    <style>
        .mini-card {
            background-color: #1a1e2b;
            border: 1px solid #2d3345;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            margin-bottom: 10px;
            font-family: Arial, sans-serif;
        }
        .card-ticker {
            color: #a0aec0;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 2px;
        }
        .card-preco {
            color: #ffffff;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 2px;
        }
        .card-var {
            font-size: 11px;
            font-weight: 500;
        }
        .var-positiva {
            color: #00e676;
        }
        .var-negativa {
            color: #ff4b4b;
        }
    </style>
""", unsafe_allow_html=True)

# Preencher os mini-cards nas colunas
with top_cols[0]:
    t = 'BBAS3'
    st.markdown(criar_mini_card(t, mock_precos[t]['preco'], mock_precos[t]['var'], mock_precos[t]['pct']), unsafe_allow_html=True)

with top_cols[1]:
    t = 'HSAF11'
    st.markdown(criar_mini_card(t, mock_precos[t]['preco'], mock_precos[t]['var'], mock_precos[t]['pct']), unsafe_allow_html=True)

# (Deixar top_cols[2] e top_cols[3] vazias ou colocar ativos extras de exemplo para mostrar densidade)


# ==========================================
# --- 5. ESTRUTURA PRINCIPAL (MANTER RESTO) ---
# ==========================================
col_esq, col_dir = st.columns([1.2, 1.0], gap="large")

# --- Coluna da Esquerda (Panorama) ---
with col_esq:
    st.subheader("Panorama do Mercado")
    ticker_grafico = st.selectbox("Selecione o ativo:", ["Ibovespa"] + ativos_unicos, label_visibility="collapsed")
    
    ticker_final = "^BVSP" if ticker_grafico == "Ibovespa" else ticker_grafico
    ticker_final_sa = ticker_final if ticker_final.endswith(('.SA', '^BVSP', '-BRL', '=X')) else f"{ticker_final}.SA"

    # Widget Avançado do TradingView
    try:
        # Mapeamento do ticker yfinance para o símbolo do TradingView
        tv_symbol = "BMFBOVESPA:IBOV" if ticker_grafico == "Ibovespa" else f"BMFBOVESPA:{ticker_final}"
        
        codigo_grafico_tv = f"""
        <div class="tradingview-widget-container" style="height:400px;width:100%">
          <div id="tradingview_chart" style="height:calc(100% - 32px);width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
          "autosize": true,
          "symbol": "{tv_symbol}",
          "interval": "D",
          "timezone": "America/Sao_Paulo",
          "theme": "dark",
          "style": "1",
          "locale": "br",
          "container_id": "tradingview_chart",
          "backgroundColor": "rgba(10, 12, 18, 1)",
          "enable_publishing": false,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "save_image": false,
          "studies": ["MACD@tv-basicstudies", "RSI@tv-basicstudies"],
          "show_popup_button": true,
          "popup_width": "1000",
          "popup_height": "650"
        }});
          </script>
        </div>
        """
        components.html(codigo_grafico_tv, height=400)
    except Exception:
        st.error("Erro ao carregar o gráfico do TradingView.")

# --- Coluna da Direita (Tabela, Resumo, Evolução) ---
with col_dir:
    # 3.2 Tabela de Cotações da Carteira
    # Criar abas para as carteiras
    tabs = st.tabs(carteiras_existentes)
    for i, nome_carteira in enumerate(carteiras_existentes):
        with tabs[i]:
            # Filtrar ativos da carteira atual e buscar cotações
            # (Excluindo o ativo 'CAIXA' da tabela, pois é reserva)
            ativos_carteira = [a for a in st.session_state["carteira"] if a.get("Carteira", "COMPRAS (Real)") == nome_carteira and a["Ticker"] != "CAIXA"]
            
            if ativos_carteira:
                df_ledger = pd.DataFrame(ativos_carteira)
                
                # Consolidar carteira agrupando por Ticker
                df_ledger["Custo"] = df_ledger["Quantidade"] * df_ledger["Preço Pago"]
                df_agrupado = df_ledger.groupby('Ticker').agg({
                    'Quantidade': 'sum',
                    'Custo': 'sum',
                    'Data da Compra': 'last'
                }).reset_index()
                df_agrupado['Preço Médio'] = df_agrupado.apply(lambda r: r['Custo'] / r['Quantidade'] if r['Quantidade'] > 0 else 0, axis=1)

                # Buscar cotações em lote para os ativos desta carteira
                with st.spinner("A atualizar cotações..."):
                    cotacoes_carteira = buscar_cotacoes(df_agrupado['Ticker'].tolist())
                
                # Preparar dados para visualização na tabela
                tabelas_dados = []
                total_investido_aba = 0
                total_atual_aba = 0

                for _, row in df_agrupado.iterrows():
                    tk = row['Ticker']
                    qtd = row['Quantidade']
                    pm = row['Preço Médio']
                    cost_total = row['Custo']
                    data = row['Data da Compra']
                    
                    preco_atual = cotacoes_carteira.get(tk)
                    
                    if preco_atual:
                        valor_atual = qtd * preco_atual
                        lucro_prejuizo = valor_atual - cost_total
                        
                        total_investido_aba += cost_total
                        total_atual_aba += valor_atual
                        
                        tabelas_dados.append({
                            "Ativo": tk, "Qtd": int(qtd), "Preço Médio": f"R$ {pm:.2f}",
                            "Custo Total": f"R$ {cost_total:.2f}",
                            "Lucro/Prejuízo": lucro_prejuizo, # Mantém número para formatação
                            "Rent. (%)": (lucro_prejuizo / cost_total) * 100 if cost_total > 0 else 0, # Mantém número
                            "Data": data
                        })
                    else:
                        # Fallback se não conseguir cotação
                        tabelas_dados.append({
                            "Ativo": tk, "Qtd": int(qtd), "Preço Médio": f"R$ {pm:.2f}",
                            "Custo Total": f"R$ {cost_total:.2f}", "Lucro/Prejuízo": 0.0,
                            "Rent. (%)": 0.0, "Data": data
                        })

                # Exibir a tabela formatada
                if tabelas_dados:
                    df_view = pd.DataFrame(tabelas_dados)
                    styled_df = df_view.style.format({
                        "Lucro/Prejuízo": "R$ {:+.2f}",
                        "Rent. (%)": "{:+.2f}%"
                    }).map(lambda v: 'color: #00e676;' if isinstance(v, (int, float)) and v > 0 else ('color: #ff4b4b;' if isinstance(v, (int, float)) and v < 0 else ''), subset=["Lucro/Prejuízo", "Rent. (%)"])
                    
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                    # 3.3 Resumo Global (se não for Watchlist)
                    # (Lógica simplificada apenas para exemplo)
                    if nome_carteira.upper() not in CARTEIRAS_FORA_DO_PATRIMONIO:
                        st.subheader("Resumo Global")
                        lucro_total_aba = total_atual_aba - total_investido_aba
                        rent_geral_aba = (lucro_total_aba / total_investido_aba) * 100 if total_investido_aba > 0 else 0
                        
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Totalmente Investido", f"R$ {total_investido_aba:,.2f}")
                        c2.metric("Patrimônio Atual", f"R$ {total_atual_aba:,.2f}", f"R$ {lucro_total_aba:,.2f}")
                        c3.metric("Rentabilidade Geral", f"{rent_geral_aba:.2f}%")

                    # 3.4 Evolução do Ativo (Histórico)
                    st.subheader("Evolução do Ativo")
                    ativo_grafico_historico = st.selectbox("Selecione o ativo para histórico:", df_agrupado['Ticker'].tolist(), key=f"sel_{nome_carteira}", label_visibility="collapsed")
                    
                    hist_data = buscar_historico(ativo_grafico_historico)
                    if not hist_data.empty:
                        # Criar gráfico de linha com Plotly
                        fig = px.line(hist_data, x='Data', y='Preço', title=None)
                        # Adicionar linha horizontal do preço médio
                        pm_ativo_aba = df_agrupado[df_agrupado['Ticker'] == ativo_grafico_historico]['Preço Médio'].values[0]
                        fig.add_hline(y=pm_ativo_aba, line_dash="dash", line_color="#ff4b4b", annotation_text=f"PM: R$ {pm_ativo_aba:.2f}")
                        
                        # Formatação do gráfico
                        fig.update_layout(xaxis_title=None, yaxis_title="Preço", margin=dict(t=0, b=0, l=0, r=0))
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há ativos cadastrados nesta carteira.")

# ==========================================
# --- 6. DISTRIBUIÇÃO DO PATRIMÔNIO GLOBAL ---
# ==========================================
# (Mantido como no código original fornecido)
# ...
