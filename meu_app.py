import streamlit as st
import pandas as pd
import requests
import urllib3
import os
import plotly.express as px
import streamlit.components.v1 as components
from datetime import datetime
import json

# --- DESLIGANDO ALERTAS DE SEGURANÇA ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÃO DO ARQUIVO ---
ARQUIVO_BANCO = "meus_portfolios.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO_BANCO):
        df = pd.read_csv(ARQUIVO_BANCO)
        # Compatibilidade com a versão antiga
        if "Preço Médio" in df.columns:
            df = df.rename(columns={"Preço Médio": "Preço Pago"})
        if "Data da Compra" not in df.columns:
            df["Data da Compra"] = "Antes da Atualização"
        # Se for um arquivo antigo sem a coluna "Carteira", define como "Principal"
        if "Carteira" not in df.columns:
            df["Carteira"] = "Principal"
        return df.to_dict(orient="records")
    return []

def salvar_dados(dados):
    df = pd.DataFrame(dados)
    df.to_csv(ARQUIVO_BANCO, index=False)
    return df.to_dict(orient="records")

def buscar_cotacao_completa(ticker):
    """Agora busca preço atual e variação diária (Estilo Investing.com)"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}.SA"
        cabecalho = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url, headers=cabecalho, verify=False, timeout=5)
        dados = resposta.json()
        meta = dados['chart']['result'][0]['meta']
        
        preco_atual = float(meta['regularMarketPrice'])
        fechamento_anterior = float(meta.get('previousClose', preco_atual))
        
        variacao = preco_atual - fechamento_anterior
        variacao_pct = (variacao / fechamento_anterior) * 100 if fechamento_anterior > 0 else 0
        
        return {
            "preco": preco_atual,
            "variacao": variacao,
            "variacao_pct": variacao_pct
        }
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

# --- INICIALIZAÇÃO DE ESTADO ---
if "dados_globais" not in st.session_state:
    st.session_state["dados_globais"] = carregar_dados()

# Extrair lista de carteiras existentes
carteiras_existentes = list(set([d.get("Carteira", "Principal") for d in st.session_state["dados_globais"]]))
if not carteiras_existentes: 
    carteiras_existentes = ["Principal"]
if "lista_carteiras" not in st.session_state:
    st.session_state["lista_carteiras"] = sorted(carteiras_existentes)

# --- INTERFACE DO APLICATIVO ---
st.set_page_config(page_title="Meu Status Invest", page_icon="📈", layout="wide")

# =====================================================================
# --- BARRA DE COTAÇÕES ROLANTE (TICKER TAPE) ---
# =====================================================================
simbolos_ticker = [
    {"proName": "BMFBOVESPA:IBOV", "title": "Ibovespa"},
    {"proName": "FX_IDC:USDBRL", "title": "Dólar (BRL)"},
]
# Puxa todos os ativos cadastrados em qualquer carteira
ativos_unicos_globais = list(set([ativo["Ticker"] for ativo in st.session_state["dados_globais"]]))
for ativo in ativos_unicos_globais:
    simbolos_ticker.append({"proName": f"BMFBOVESPA:{ativo}", "title": ativo})

ticker_config = {
    "symbols": simbolos_ticker,
    "showSymbolLogo": True,
    "isTransparent": True,
    "displayMode": "adaptive",
    "colorTheme": "dark",
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
components.html(codigo_ticker, height=80)
# =====================================================================

st.title("📈 Meu Portfólio & Acompanhamento")

# --- BARRA LATERAL (GERENCIAMENTO) ---
st.sidebar.header("📁 Gerenciar Carteiras")
nova_carteira = st.sidebar.text_input("Criar nova lista/carteira:", placeholder="Ex: Fundos Imobiliários")
if st.sidebar.button("Criar Carteira"):
    if nova_carteira and nova_carteira not in st.session_state["lista_carteiras"]:
        st.session_state["lista_carteiras"].append(nova_carteira)
        st.sidebar.success(f"'{nova_carteira}' criada com sucesso!")
        st.rerun()

st.sidebar.divider()

st.sidebar.header("➕ Cadastrar Ativo")
carteira_alvo = st.sidebar.selectbox("Em qual carteira adicionar?", st.session_state["lista_carteiras"])
ticker_input = st.sidebar.text_input("Código do Ativo (Ex: PETR4)", value="PETR4").upper().strip()

preco_atual_sidebar = None
if ticker_input:
    with st.sidebar.spinner("Buscando dados..."):
        cotacao_info = buscar_cotacao_completa(ticker_input)
        
    if cotacao_info:
        preco_atual_sidebar = cotacao_info['preco']
        # Mostra a métrica colorida na lateral igual no site
        st.sidebar.metric(label=f"Cotação ({ticker_input})", 
                          value=f"R$ {preco_atual_sidebar:.2f}", 
                          delta=f"{cotacao_info['variacao_pct']:.2f}%")

data_compra_input = st.sidebar.date_input("Data", value=datetime.today())

st.sidebar.caption("💡 Dica: Coloque a quantidade como 0 se quiser apenas colocar o ativo em observação (Watchlist).")
qtd_input = st.sidebar.number_input("Quantidade", min_value=0, value=10)

valor_padrao_preco = float(preco_atual_sidebar) if preco_atual_sidebar else 35.00
preco_medio_input = st.sidebar.number_input("Preço de Entrada (R$)", min_value=0.01, value=valor_padrao_preco, step=0.01)

if qtd_input > 0:
    st.sidebar.info(f"**Total da Ordem: R$ {(qtd_input * preco_medio_input):,.2f}**")
else:
    st.sidebar.info("Modo: Acompanhamento (Sem impacto no patrimônio)")

col_btn1, col_btn2 = st.sidebar.columns(2)

if col_btn1.button("Salvar Ativo"):
    data_str = data_compra_input.strftime("%d/%m/%Y")
    st.session_state["dados_globais"].append({
        "Carteira": carteira_alvo,
        "Ticker": ticker_input,
        "Quantidade": qtd_input,
        "Preço Pago": preco_medio_input,
        "Data da Compra": data_str
    })
    st.session_state["dados_globais"] = salvar_dados(st.session_state["dados_globais"])
    st.sidebar.success(f"Salvo em '{carteira_alvo}'!")
    st.rerun()

if col_btn2.button("Limpar Tudo"):
    st.session_state["dados_globais"] = []
    if os.path.exists(ARQUIVO_BANCO):
        os.remove(ARQUIVO_BANCO)
    st.rerun()

# --- ÁREA PRINCIPAL: SISTEMA DE ABAS (TABS) ---
abas = st.tabs(st.session_state["lista_carteiras"])

# Loop para preencher cada aba com seus respectivos dados
for i, nome_carteira in enumerate(st.session_state["lista_carteiras"]):
    with abas[i]:
        # Filtra os dados apenas para a carteira da aba atual
        dados_carteira = [d for d in st.session_state["dados_globais"] if d.get("Carteira", "Principal") == nome_carteira]
        
        if len(dados_carteira) == 0:
            st.info(f"A carteira '{nome_carteira}' está vazia. Adicione ativos usando o menu lateral.")
            continue
            
        df_ledger = pd.DataFrame(dados_carteira)
        df_ledger["Custo da Operação"] = df_ledger["Quantidade"] * df_ledger["Preço Pago"]
        
        df_agrupado = df_ledger.groupby('Ticker').agg({
            'Quantidade': 'sum',
            'Custo da Operação': 'sum'
        }).reset_index()
        
        df_agrupado['Preço Médio'] = df_agrupado.apply(
            lambda row: row['Custo da Operação'] / row['Quantidade'] if row['Quantidade'] > 0 else 0, axis=1
        )
        
        linhas_tabela = []
        valor_total_investido = 0
        valor_total_atual = 0
        
        with st.spinner(f"Atualizando cotações de {nome_carteira}..."):
            for index, row in df_agrupado.iterrows():
                ticker = row['Ticker']
                qtd_total = row['Quantidade']
                preco_medio = row['Preço Médio']
                custo_total = row['Custo da Operação']
                
                info = buscar_cotacao_completa(ticker)
                
                if info is not None:
                    preco_atual = info['preco']
                    valor_atual_total = qtd_total * preco_atual
                    lucro_prejuizo = valor_atual_total - custo_total if qtd_total > 0 else 0
                    
                    valor_total_investido += custo_total
                    valor_total_atual += valor_atual_total
                    
                    linhas_tabela.append({
                        "Ativo": ticker,
                        "Último": preco_atual,
                        "Variação (R$)": info['variacao'],
                        "Var (%)": info['variacao_pct'] / 100, # Dividido por 100 para o formatador do pandas
                        "Qtd": int(qtd_total),
                        "Preço Médio": preco_medio,
                        "Patrimônio": valor_atual_total,
                        "Lucro/Prej.": lucro_prejuizo
                    })
        
        if linhas_tabela:
            st.subheader(f"Lista de Ativos: {nome_carteira}")
            
            # Formatação no estilo Investing.com
            df_tela = pd.DataFrame(linhas_tabela)
            
            # Função para colorir números (Verde para Positivo, Vermelho para Negativo)
            def colorir_valores(val):
                if isinstance(val, str): return ''
                color = '#00c698' if val > 0 else '#ff4b4b' if val < 0 else 'gray'
                return f'color: {color}; font-weight: bold;'

            tabela_formatada = df_tela.style.format({
                "Último": "R$ {:.2f}",
                "Variação (R$)": "R$ {:.2f}",
                "Var (%)": "{:.2%}",
                "Preço Médio": "R$ {:.2f}",
                "Patrimônio": "R$ {:.2f}",
                "Lucro/Prej.": "R$ {:.2f}"
            }).map(colorir_valores, subset=['Variação (R$)', 'Var (%)', 'Lucro/Prej.'])
            
            st.dataframe(tabela_formatada, use_container_width=True, hide_index=True)
            
            # Resumo da Aba Atual
            if valor_total_investido > 0:
                col1, col2, col3 = st.columns(3)
                resultado = valor_total_atual - valor_total_investido
                rentabilidade = (resultado / valor_total_investido) * 100
                
                col1.metric("Investido nesta Carteira", f"R$ {valor_total_investido:,.2f}")
                col2.metric("Patrimônio Atual", f"R$ {valor_total_atual:,.2f}", f"R$ {resultado:,.2f}")
                col3.metric("Rentabilidade", f"{rentabilidade:,.2f}%")
            
            # Área de Gráficos Específica da Aba
            with st.expander(f"📊 Ver Histórico e Gráficos ({nome_carteira})"):
                ativos_da_aba = df_tela["Ativo"].tolist()
                grafico_escolhido = st.selectbox("Escolha o ativo para ver o gráfico:", ativos_da_aba, key=f"graf_{nome_carteira}")
                
                df_hist = buscar_historico(grafico_escolhido)
                if not df_hist.empty:
                    fig_hist = px.line(df_hist, x="Data", y="Preço", title=f"Histórico de 6 Meses - {grafico_escolhido}")
                    
                    # Linha de Preço Médio (se houver quantidade)
                    preco_medio_ativo = df_tela[df_tela["Ativo"] == grafico_escolhido]["Preço Médio"].values[0]
                    qtd_ativo = df_tela[df_tela["Ativo"] == grafico_escolhido]["Qtd"].values[0]
                    
                    if qtd_ativo > 0:
                        fig_hist.add_hline(y=preco_medio_ativo, line_dash="dash", line_color="#ff4b4b",
                                           annotation_text=f"Preço Médio (R$ {preco_medio_ativo:.2f})",
                                           annotation_position="bottom right",
                                           annotation_font_color="#ff4b4b")
                    
                    fig_hist.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white", xaxis_title="")
                    fig_hist.update_traces(line_color="#00c698")
                    st.plotly_chart(fig_hist, use_container_width=True)
                else:
                    st.warning("Histórico não encontrado.")
