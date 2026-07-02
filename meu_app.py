import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import streamlit.components.v1 as components
import os
import json
from datetime import datetime

# Configuração para usar o ecrã inteiro
st.set_page_config(page_title="Meu Portfólio", page_icon="📈", layout="wide")

# ==========================================
# --- 1. BANCO DE DADOS (CSV) ---
# ==========================================
ARQUIVO_BANCO = "minha_carteira.csv"

# Carteiras que NÃO entram no cálculo de patrimônio real
# (edite aqui se criar outras carteiras "de acompanhamento")
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
    """True se o ativo deve contar no patrimônio/gráficos globais."""
    return ativo.get("Carteira", "COMPRAS (Real)").upper() not in CARTEIRAS_FORA_DO_PATRIMONIO

# ==========================================
# --- 2. FUNÇÕES DE DADOS (YFINANCE) ---
# ==========================================
# Removido o scraping direto do Yahoo com verify=False: usa yfinance puro,
# que ja cuida de certificado e formato de resposta.

@st.cache_data(ttl=60)
def buscar_cotacao_simples(ticker):
    try:
        ticker_sa = ticker if ticker.endswith(('.SA', '-BRL', '=X', '^')) else f"{ticker}.SA"
        info = yf.Ticker(ticker_sa).fast_info
        preco = info.get("last_price")
        return float(preco) if preco else None
    except Exception:
        return None

@st.cache_data(ttl=60)
def buscar_cotacoes_lote(tickers):
    """Busca varios tickers de uma vez (mais rapido que um a um)."""
    if not tickers:
        return {}
    tickers_sa = [t if t.endswith(('.SA', '-BRL', '=X', '^')) else f"{t}.SA" for t in tickers]
    try:
        dados = yf.download(tickers=tickers_sa, period="1d", progress=False, group_by="ticker")
        precos = {}
        for t, t_sa in zip(tickers, tickers_sa):
            try:
                if len(tickers) == 1:
                    precos[t] = float(dados["Close"].iloc[-1])
                else:
                    precos[t] = float(dados[t_sa]["Close"].iloc[-1])
            except Exception:
                precos[t] = buscar_cotacao_simples(t)  # fallback individual
        return precos
    except Exception:
        return {t: buscar_cotacao_simples(t) for t in tickers}

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
    ticker_input = st.text_input("Código do Ativo (Ex: PETR4)", value="PETR4").upper().strip()

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

    st.divider()
    with st.expander("🗑️ Remover Ativo (Eliminar)"):
        ativos_remover = list(set([a["Ticker"] for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA"]))
        if ativos_remover:
            ativo_para_remover = st.selectbox("Escolha o ativo", ativos_remover)
            carteira_do_ativo = st.selectbox("De qual carteira?", carteiras_existentes, key="rem_cart")
            if st.button("Remover Definitivamente", type="primary", use_container_width=True):
                antes = len(st.session_state["carteira"])
                st.session_state["carteira"] = [a for a in st.session_state["carteira"]
                                                if not (a["Ticker"] == ativo_para_remover and a.get("Carteira", "COMPRAS (Real)") == carteira_do_ativo)]
                removeu = antes != len(st.session_state["carteira"])
                st.session_state["carteira"] = salvar_dados(st.session_state["carteira"])
                if removeu:
                    st.success("Removido!")
                else:
                    st.warning("Não encontrei esse ativo nessa carteira.")
                st.rerun()
        else:
            st.caption("Nenhum ativo para remover.")

# ==========================================
# --- LETREIRO ROTATIVO (COTAÇÕES PASSANDO) ---
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

simbolos_json = json.dumps(simbolos_letreiro)

codigo_letreiro = f"""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {{
  "symbols": {simbolos_json},
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
# --- 4. TOPO: CARTÕES FIXOS ---
# ==========================================
st.title("📈 Meu Portfólio & Acompanhamento")

indices = buscar_indices_topo()

def criar_cartao_html(titulo, valor, variacao, pct, prefixo="", watchlist=False):
    cor = "#00e676" if variacao >= 0 else "#ff4b4b"
    sinal = "+" if variacao >= 0 else ""
    borda = "2px solid #378ADD" if watchlist else "1px solid #2B3040"
    selo = '<div style="color:#378ADD; font-size:11px; margin-bottom:4px;">👁️ WATCHLIST</div>' if watchlist else ""
    # Montado em uma linha so (sem quebras/indentacao) para o st.markdown
    # nunca interpretar como bloco de codigo quando 'selo' fica vazio.
    partes = [
        f'<div style="background-color: #161A25; padding: 15px; border-radius: 8px; border: {borda}; text-align: center; margin-bottom: 15px;">',
        selo,
        f'<div style="color: #A0AEC0; font-size: 14px; font-weight: bold; margin-bottom: 5px;">{titulo}</div>',
        f'<div style="font-size: 22px; font-weight: bold; color: white;">{prefixo}{valor}</div>',
        f'<div style="color: {cor}; font-size: 14px; margin-top: 5px;">{sinal}{variacao:.2f} ({sinal}{pct:.2f}%)</div>',
        '</div>',
    ]
    return "".join(partes)

# Cria uma lista dinâmica com TODOS os cartões que precisam aparecer
cartoes = []
if indices:
    cartoes.append(("Ibovespa", f"{indices['IBOV']['preco']:,.0f}", indices['IBOV']['var'], indices['IBOV']['pct'], "", False))
    cartoes.append(("Dólar", f"{indices['USD']['preco']:.4f}", indices['USD']['var'], indices['USD']['pct'], "R$ ", False))
    cartoes.append(("Bitcoin (BRL)", f"{indices['BTC']['preco']:,.0f}", indices['BTC']['var'], indices['BTC']['pct'], "R$ ", False))

# Ativos com sua carteira de origem, para saber se é watchlist
ativos_com_carteira = {}
for a in st.session_state["carteira"]:
    if a["Ticker"] != "CAIXA":
        ativos_com_carteira[a["Ticker"]] = a.get("Carteira", "COMPRAS (Real)")

ativos_ativos = list(ativos_com_carteira.keys())
precos_lote = buscar_cotacoes_lote(ativos_ativos)

for ticker in ativos_ativos:
    preco = precos_lote.get(ticker)
    if preco:
        is_watch = ativos_com_carteira[ticker].upper() in CARTEIRAS_FORA_DO_PATRIMONIO
        cartoes.append((ticker, f"{preco:.2f}", 0.0, 0.0, "R$ ", is_watch))

# Desenha os cartões no ecrã agrupados de 5 em 5 colunas automaticamente!
if cartoes:
    for i in range(0, len(cartoes), 5):
        cols_topo = st.columns(5)
        for j in range(5):
            if i + j < len(cartoes):
                titulo, valor, var, pct, prefixo, is_watch = cartoes[i+j]
                with cols_topo[j]:
                    st.markdown(criar_cartao_html(titulo, valor, var, pct, prefixo, is_watch), unsafe_allow_html=True)

st.write("")  # Espaçamento

# ==========================================
# --- 5. ESTRUTURA PRINCIPAL (ESQUERDA / DIREITA) ---
# ==========================================
col_esq, col_dir = st.columns([1.2, 1.0], gap="large")

# --- LADO ESQUERDO (Panorama e Gráficos Globais) ---
with col_esq:
    st.subheader("🌐 Panorama do Mercado")

    ativos_reais_grafico = [a["Ticker"] for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA" and eh_patrimonio_real(a)]
    opcoes_grafico = {"Ibovespa": "BMFBOVESPA:IBOV"}
    for ativo in set(ativos_reais_grafico): opcoes_grafico[ativo] = f"BMFBOVESPA:{ativo}"
    grafico_escolhido = st.selectbox("Gráfico Principal:", list(opcoes_grafico.keys()), label_visibility="collapsed")
    simbolo_tv = opcoes_grafico[grafico_escolhido]

    codigo_grafico_avancado = f"""
    <div class="tradingview-widget-container" style="height:400px;width:100%">
      <div id="tradingview_chart" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{"autosize": true, "symbol": "{simbolo_tv}", "interval": "D", "timezone": "America/Sao_Paulo", "theme": "dark", "style": "1", "locale": "br", "enable_publishing": false, "backgroundColor": "#161A25", "gridColor": "rgba(42, 46, 57, 0.06)", "hide_top_toolbar": false, "hide_legend": false, "save_image": false, "container_id": "tradingview_chart"}});
      </script>
    </div>
    """
    components.html(codigo_grafico_avancado, height=400)

    st.divider()
    st.subheader("📊 Distribuição do Patrimônio Global")
    st.caption("Considera apenas carteiras reais — a Watchlist fica de fora.")

    # FILTRO CORRIGIDO: exclui carteiras de watchlist do calculo de patrimonio
    df_global = pd.DataFrame([a for a in st.session_state["carteira"] if a["Ticker"] != "CAIXA" and eh_patrimonio_real(a)])
    if not df_global.empty:
        df_global["Custo da Operação"] = df_global["Quantidade"] * df_global["Preço Pago"]
        df_grp_global = df_global.groupby('Ticker').agg({'Quantidade': 'sum'}).reset_index()

        tickers_global = df_grp_global['Ticker'].tolist()
        precos_global = buscar_cotacoes_lote(tickers_global)

        lista_graf = []
        for _, row in df_grp_global.iterrows():
            preco_atu = precos_global.get(row['Ticker'])
            if preco_atu:
                patrimonio = row['Quantidade'] * preco_atu
                cat = 'FIIs' if row['Ticker'].endswith('11') else 'Ações'
                lista_graf.append({'Ativo': row['Ticker'], 'Patrimônio': patrimonio, 'Categoria': cat})

        if lista_graf:
            df_g = pd.DataFrame(lista_graf)
            c_pie, c_bar = st.columns(2)

            df_pizza = df_g.groupby('Categoria')['Patrimônio'].sum().reset_index()
            fig_pie = px.pie(df_pizza, values='Patrimônio', names='Categoria', hole=0.5, color_discrete_sequence=['#00c698', '#1b4d3e'])
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            c_pie.plotly_chart(fig_pie, use_container_width=True)

            df_g = df_g.sort_values(by="Patrimônio", ascending=False)
            fig_bar = px.bar(df_g, x='Ativo', y='Patrimônio', color='Categoria', text_auto='.2s', color_discrete_map={"Ações": "#1b4d3e", "FIIs": "#00c698"})
            fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            c_bar.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Nenhum ativo em carteira real ainda.")

# --- LADO DIREITO (Abas, Tabela e Evolução) ---
with col_dir:
    abas = st.tabs(carteiras_existentes)

    for i, nome_carteira in enumerate(carteiras_existentes):
        with abas[i]:
            if nome_carteira.upper() in CARTEIRAS_FORA_DO_PATRIMONIO:
                st.caption("👁️ Carteira de acompanhamento — não entra no patrimônio nem nos gráficos globais.")

            dados_aba = [a for a in st.session_state["carteira"] if a.get("Carteira", "COMPRAS (Real)") == nome_carteira and a["Ticker"] != "CAIXA"]

            if not dados_aba:
                st.info("Carteira vazia.")
                continue

            df_ledger = pd.DataFrame(dados_aba)
            df_ledger["Custo"] = df_ledger["Quantidade"] * df_ledger["Preço Pago"]
            df_agrupado = df_ledger.groupby('Ticker').agg({'Quantidade': 'sum', 'Custo': 'sum', 'Data da Compra': 'last'}).reset_index()
            df_agrupado['Preço Médio'] = df_agrupado.apply(lambda r: r['Custo'] / r['Quantidade'] if r['Quantidade'] > 0 else 0, axis=1)

            tickers_aba = df_agrupado['Ticker'].tolist()
            precos_aba = buscar_cotacoes_lote(tickers_aba)

            tabelas = []
            tot_inv, tot_atu = 0, 0

            for _, row in df_agrupado.iterrows():
                tk, qtd, pm, cst, dt = row['Ticker'], row['Quantidade'], row['Preço Médio'], row['Custo'], row['Data da Compra']
                p_atu = precos_aba.get(tk)
                if p_atu:
                    v_atu = qtd * p_atu
                    lucro = v_atu - cst
                    tot_inv += cst
                    tot_atu += v_atu

                    tabelas.append({
                        "Ativo": tk, "Qtd": int(qtd), "Preço Médio": f"R$ {pm:.2f}",
                        "Custo Total": f"R$ {cst:.2f}", "Lucro/Prejuízo": lucro,
                        "Rent. (%)": (lucro/cst)*100 if cst > 0 else 0, "Data": dt
                    })

            if tabelas:
                df_view = pd.DataFrame(tabelas)

                def color_lucro(val):
                    color = '#00e676' if val > 0 else '#ff4b4b'
                    return f'color: {color}; font-weight: bold;'

                styled = df_view.style.format({
                    "Lucro/Prejuízo": "R$ {:+.2f}", "Rent. (%)": "{:+.2f}%"
                }).map(lambda v: color_lucro(v) if isinstance(v, (int, float)) else '', subset=["Lucro/Prejuízo", "Rent. (%)"])

                st.dataframe(styled, use_container_width=True, hide_index=True)

                if nome_carteira.upper() not in CARTEIRAS_FORA_DO_PATRIMONIO:
                    st.markdown("### Resumo Global")
                    c1, c2, c3 = st.columns(3)
                    rent_geral = ((tot_atu - tot_inv) / tot_inv) * 100 if tot_inv > 0 else 0
                    c1.metric("Totalmente Investido", f"R$ {tot_inv:,.2f}")
                    c2.metric("Patrimônio Atual", f"R$ {tot_atu:,.2f}", f"R$ {tot_atu - tot_inv:,.2f}")
                    c3.metric("Rentabilidade Geral", f"{rent_geral:.2f}%")

                st.markdown("### Evolução do Ativo")
                ativo_graf_aba = st.selectbox("Selecione o ativo:", df_agrupado['Ticker'].tolist(), key=f"sel_{nome_carteira}")

                df_hist = buscar_historico(ativo_graf_aba)
                if not df_hist.empty:
                    fig_linha = px.line(df_hist, x='Data', y='Preço')

                    pm_ativo = df_agrupado[df_agrupado['Ticker'] == ativo_graf_aba]['Preço Médio'].values[0]
                    fig_linha.add_hline(y=pm_ativo, line_dash="dash", line_color="#ff4b4b", annotation_text=f"PM: R$ {pm_ativo:.2f}")

                    fig_linha.update_layout(margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=250)
                    fig_linha.update_traces(line_color="#00c698")
                    st.plotly_chart(fig_linha, use_container_width=True)
