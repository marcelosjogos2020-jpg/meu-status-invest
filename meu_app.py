import streamlit as st
import pandas as pd
import requests
import urllib3
import os
import plotly.express as px
import streamlit.components.v1 as components
from datetime import datetime
import json # <-- Adicionado para configurar o widget de cotações

# --- DESLIGANDO ALERTAS DE SEGURANÇA ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÃO DO ARQUIVO ---
ARQUIVO_BANCO = "minha_carteira.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO_BANCO):
        df = pd.read_csv(ARQUIVO_BANCO)
        if "Preço Médio" in df.columns:
            df = df.rename(columns={"Preço Médio": "Preço Pago"})
        if "Data da Compra" not in df.columns:
            df["Data da Compra"] = "Antes da Atualização"
        return df.to_dict(orient="records")
    return []

def salvar_dados(dados):
    df = pd.DataFrame(dados)
    df.to_csv(ARQUIVO_BANCO, index=False)
    return df.to_dict(orient="records")

def buscar_cotacao(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}.SA"
        cabecalho = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url, headers=cabecalho, verify=False, timeout=5)
        dados = resposta.json()
        return float(dados['chart']['result'][0]['meta']['regularMarketPrice'])
    except:
        return None

def buscar_historico(ticker):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}.SA?range=6mo&interval=1d"
        cabecalho = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url, headers=cabecalho, verify=False, timeout=5)
        dados = resposta.json()['chart']['result'][0]
        timestamps = dados['timestamp']
        closes = dados['indicators']['quote'][0]['close']
        datas = [datetime.fromtimestamp(ts) for ts in timestamps]
        return pd.DataFrame({'Data': datas, 'Preço': closes})
    except:
        return pd.DataFrame()

if "carteira" not in st.session_state:
    st.session_state["carteira"] = carregar_dados()

# --- INTERFACE DO APLICATIVO ---
st.set_page_config(page_title="Meu Status Invest", page_icon="📈", layout="wide")
st.title("📈 Meu Portfólio em Tempo Real")

# =====================================================================
# --- NOVIDADE: BARRA DE COTAÇÕES ROLANTE (TICKER TAPE) ---
# =====================================================================
# 1. Definimos os índices globais padrão
simbolos_ticker = [
    {"proName": "BMFBOVESPA:IBOV", "title": "Ibovespa"},
    {"proName": "FX_IDC:USDBRL", "title": "Dólar (BRL)"},
    {"proName": "BINANCE:BTCBRL", "title": "Bitcoin (BRL)"}
]

# 2. Adicionamos dinamicamente os ativos que você tem na carteira
if len(st.session_state["carteira"]) > 0:
    ativos_unicos = list(set([ativo["Ticker"] for ativo in st.session_state["carteira"]]))
    for ativo in ativos_unicos:
        simbolos_ticker.append({
            "proName": f"BMFBOVESPA:{ativo}",
            "title": ativo
        })

# 3. Configuramos o JSON do Widget do TradingView
ticker_config = {
    "symbols": simbolos_ticker,
    "showSymbolLogo": True,
    "isTransparent": True,
    "displayMode": "adaptive",
    "colorTheme": "dark", # Troque para "light" se o seu Streamlit for claro
    "locale": "br"
}

codigo_ticker = f"""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {json.dumps(ticker_config)}
  </script>
</div>
"""
# Renderiza a barra na tela com altura de 80 pixels
components.html(codigo_ticker, height=80)
# =====================================================================

st.subheader("🌐 Panorama do Mercado e Seus Ativos")

opcoes_grafico = ["Mercado Geral (Ibovespa)"]
if len(st.session_state["carteira"]) > 0:
    ativos_unicos = list(set([ativo["Ticker"] for ativo in st.session_state["carteira"]]))
    opcoes_grafico.extend(ativos_unicos)

grafico_escolhido = st.selectbox("Qual gráfico você quer ver?", opcoes_grafico)

if grafico_escolhido == "Mercado Geral (Ibovespa)":
    codigo_tradingview = """
    <div class="tradingview-widget-container">
      <div id="tradingview_ibov"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({
      "width": "100%", "height": 400, "symbol": "BMFBOVESPA:IBOV", "interval": "D",
      "timezone": "America/Sao_Paulo", "theme": "dark", "style": "3", "locale": "br",
      "enable_publishing": false, "hide_top_toolbar": false, "hide_legend": false,
      "save_image": false, "container_id": "tradingview_ibov"
    });
      </script>
    </div>
    """
    components.html(codigo_tradingview, height=400)
else:
    with st.spinner(f"Buscando histórico de {grafico_escolhido}..."):
        df_hist = buscar_historico(grafico_escolhido)
        if not df_hist.empty:
            compras_ativo = [a for a in st.session_state["carteira"] if a["Ticker"] == grafico_escolhido]
            qtd_total_ativo = sum(a["Quantidade"] for a in compras_ativo)
            custo_total_ativo = sum(a["Quantidade"] * a["Preço Pago"] for a in compras_ativo)
            preco_medio_ativo = custo_total_ativo / qtd_total_ativo if qtd_total_ativo > 0 else 0
            
            fig_hist = px.line(df_hist, x="Data", y="Preço", title=f"Histórico de 6 Meses - {grafico_escolhido}")
            
            # Linha Horizontal (PREÇO MÉDIO FINAL)
            fig_hist.add_hline(y=preco_medio_ativo, line_dash="dash", line_color="#ff4b4b",
                               annotation_text=f"Preço Médio (R$ {preco_medio_ativo:.2f})",
                               annotation_position="bottom right",
                               annotation_font_color="#ff4b4b")
            
            # --- Linhas Verticais com Texto (Qtd + Data) na Vertical ---
            compras_por_data = {}
            for compra in compras_ativo:
                d = compra.get("Data da Compra", "N/A")
                if d not in ["Antes da Atualização", "N/A"]:
                    # Isola apenas a data (sem a hora, se houver) para agrupar no dia
                    dia = d.split(" ")[0]
                    if dia in compras_por_data:
                        compras_por_data[dia] += compra["Quantidade"]
                    else:
                        compras_por_data[dia] = compra["Quantidade"]

            for dia, qtd in compras_por_data.items():
                try:
                    data_formatada = datetime.strptime(dia, "%d/%m/%Y")
                    fig_hist.add_vline(x=data_formatada, line_dash="dot", line_color="#00d4ff",
                                       annotation_text=f"{int(qtd)} cotas em {dia}",
                                       annotation_position="top left",
                                       annotation_textangle=-90, # Deixa o texto escrito de lado (vertical)
                                       annotation_font_color="#00d4ff")
                except:
                    pass
            
            fig_hist.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white", xaxis_title="")
            fig_hist.update_traces(line_color="#00c698")
            
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning("Não foi possível carregar o histórico desse ativo.")

st.divider()

# --- BARRA LATERAL ---
st.sidebar.header("Cadastrar Novo Aporte")

ticker_input = st.sidebar.text_input("Código do Ativo (Ex: PETR4)", value="PETR4").upper().strip()

preco_atual_sidebar = None
if ticker_input:
    with st.sidebar.spinner("Buscando preço..."):
        preco_atual_sidebar = buscar_cotacao(ticker_input)
        
    if preco_atual_sidebar:
        st.sidebar.metric(label=f"Cotação Atual ({ticker_input})", value=f"R$ {preco_atual_sidebar:.2f}")

data_compra_input = st.sidebar.date_input("Data da Compra", value=datetime.today())
qtd_input = st.sidebar.number_input("Quantidade (Coloque 0 se quiser apenas editar a data da última)", min_value=0, value=10)

valor_padrao_preco = float(preco_atual_sidebar) if preco_atual_sidebar else 35.00
preco_medio_input = st.sidebar.number_input("Preço da Compra (R$)", min_value=0.01, value=valor_padrao_preco, step=0.01)

total_simulado = qtd_input * preco_medio_input
st.sidebar.info(f"**Total da Ordem: R$ {total_simulado:,.2f}**")

col_btn1, col_btn2 = st.sidebar.columns(2)

if col_btn1.button("Salvar Ativo"):
    data_str = data_compra_input.strftime("%d/%m/%Y")
    
    if qtd_input > 0:
        st.session_state["carteira"].append({
            "Ticker": ticker_input,
            "Quantidade": qtd_input,
            "Preço Pago": preco_medio_input,
            "Data da Compra": data_str
        })
    else:
        for ativo in reversed(st.session_state["carteira"]):
            if ativo["Ticker"] == ticker_input:
                ativo["Data da Compra"] = data_str
                break
                
    st.session_state["carteira"] = salvar_dados(st.session_state["carteira"])
    st.sidebar.success(f"{ticker_input} salvo no histórico!")
    st.rerun()

if col_btn2.button("Limpar Tudo"):
    st.session_state["carteira"] = []
    if os.path.exists(ARQUIVO_BANCO):
        os.remove(ARQUIVO_BANCO)
    st.rerun()

# --- CÁLCULO GERAL DA CARTEIRA E TABELAS ---
if len(st.session_state["carteira"]) > 0:
    st.subheader("Sua Posição Consolidada")
    
    df_ledger = pd.DataFrame(st.session_state["carteira"])
    df_ledger["Custo da Operação"] = df_ledger["Quantidade"] * df_ledger["Preço Pago"]
    
    df_agrupado = df_ledger.groupby('Ticker').agg({
        'Quantidade': 'sum',
        'Custo da Operação': 'sum'
    }).reset_index()
    
    df_agrupado['Preço Médio'] = df_agrupado.apply(
        lambda row: row['Custo da Operação'] / row['Quantidade'] if row['Quantidade'] > 0 else 0, axis=1
    )
    
    dados_brutos = [] 
    valor_total_investido = 0
    valor_total_atual = 0
    
    with st.spinner("Atualizando valores da carteira..."):
        for index, row in df_agrupado.iterrows():
            ticker = row['Ticker']
            qtd_total = row['Quantidade']
            preco_medio = row['Preço Médio']
            custo_total = row['Custo da Operação']
            
            preco_atual = buscar_cotacao(ticker)
            
            if preco_atual is not None:
                valor_atual_total = qtd_total * preco_atual
                lucro_prejuizo = valor_atual_total - custo_total
                rentabilidade = (lucro_prejuizo / custo_total) * 100 if custo_total > 0 else 0
                
                categoria = "FIIs" if ticker.endswith('11') else "Ações"
                
                valor_total_investido += custo_total
                valor_total_atual += valor_atual_total
                
                dados_brutos.append({
                    "Categoria": categoria,
                    "Ativo": ticker,
                    "Qtd Total": int(qtd_total),
                    "Preço Médio": preco_medio,
                    "Preço Atual": preco_atual,
                    "Custo Total": custo_total,
                    "Valor Atual": valor_atual_total,
                    "Lucro/Prejuízo": lucro_prejuizo,
                    "Rentabilidade (%)": rentabilidade
                })
            
    if dados_brutos:
        df_formatado = pd.DataFrame(dados_brutos).copy()
        for col in ["Preço Médio", "Preço Atual", "Custo Total", "Valor Atual", "Lucro/Prejuízo"]:
            df_formatado[col] = df_formatado[col].apply(lambda x: f"R$ {x:,.2f}")
        df_formatado["Rentabilidade (%)"] = df_formatado["Rentabilidade (%)"].apply(lambda x: f"{x:,.2f}%")
        
        st.dataframe(df_formatado.drop(columns=["Categoria"]), use_container_width=True)
        
        with st.expander("🛒 Ver Histórico Detalhado de Compras (Livro de Ordens)"):
            df_historico_tela = df_ledger.copy()
            df_historico_tela = df_historico_tela[["Data da Compra", "Ticker", "Quantidade", "Preço Pago", "Custo da Operação"]]
            df_historico_tela["Preço Pago"] = df_historico_tela["Preço Pago"].apply(lambda x: f"R$ {x:,.2f}")
            df_historico_tela["Custo da Operação"] = df_historico_tela["Custo da Operação"].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(df_historico_tela, use_container_width=True)
        
        st.divider()
        
        st.subheader("Resumo Global")
        col1, col2, col3 = st.columns(3)
        resultado_global = valor_total_atual - valor_total_investido
        
        col1.metric("Totalmente Investido", f"R$ {valor_total_investido:,.2f}")
        col2.metric("Patrimônio Atual", f"R$ {valor_total_atual:,.2f}", f"R$ {resultado_global:,.2f}")
        col3.metric("Rentabilidade Geral", f"{((resultado_global/valor_total_investido)*100 if valor_total_investido > 0 else 0):,.2f} %")
        
        st.divider()
        
        st.subheader("📊 Distribuição do Patrimônio")
        df_graficos = pd.DataFrame(dados_brutos)
        
        col_graf1, col_graf2 = st.columns(2)
        
        df_pizza = df_graficos.groupby('Categoria')['Valor Atual'].sum().reset_index()
        fig_pizza = px.pie(df_pizza, values='Valor Atual', names='Categoria', hole=0.4, 
                           title="Divisão da Carteira", color_discrete_sequence=['#00c698', '#1b4d3e'])
        col_graf1.plotly_chart(fig_pizza, use_container_width=True)
        
        df_graficos = df_graficos.sort_values(by="Valor Atual", ascending=False)
        fig_barras = px.bar(df_graficos, x='Ativo', y='Valor Atual', color='Categoria',
                            title="Patrimônio por Ativo", text_auto='.2s', 
                            color_discrete_map={"Ações": "#1b4d3e", "FIIs": "#00c698"})
        col_graf2.plotly_chart(fig_barras, use_container_width=True)

else:
    st.info("Sua carteira está vazia. Cadastre seus aportes no menu lateral!")
