import streamlit as st
import pandas as pd
import requests
import urllib3
import os
import plotly.express as px  # <-- NOVA BIBLIOTECA DE GRÁFICOS INTERATIVOS

# --- DESLIGANDO ALERTAS DE SEGURANÇA ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURAÇÃO DO ARQUIVO ---
ARQUIVO_BANCO = "minha_carteira.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO_BANCO):
        return pd.read_csv(ARQUIVO_BANCO).to_dict(orient="records")
    return []

def salvar_dados(dados):
    df = pd.DataFrame(dados)
    if not df.empty:
        df['Custo Total'] = df['Quantidade'] * df['Preço Médio']
        df_agrupado = df.groupby('Ticker').agg({'Quantidade': 'sum', 'Custo Total': 'sum'}).reset_index()
        df_agrupado['Preço Médio'] = df_agrupado['Custo Total'] / df_agrupado['Quantidade']
        df_agrupado = df_agrupado.drop(columns=['Custo Total'])
        df = df_agrupado
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

if "carteira" not in st.session_state:
    st.session_state["carteira"] = carregar_dados()

# --- INTERFACE DO APLICATIVO ---
st.set_page_config(page_title="Meu Status Invest", page_icon="📈", layout="wide")
st.title("📈 Meu Portfólio em Tempo Real")

st.sidebar.header("Cadastrar Novo Ativo")

ticker_input = st.sidebar.text_input("Código do Ativo (Ex: PETR4)", value="PETR4").upper().strip()

preco_atual_sidebar = None
if ticker_input:
    with st.sidebar.spinner(f"Buscando preço..."):
        preco_atual_sidebar = buscar_cotacao(ticker_input)
        
    if preco_atual_sidebar:
        st.sidebar.metric(label=f"Cotação Atual ({ticker_input})", value=f"R$ {preco_atual_sidebar:.2f}")

qtd_input = st.sidebar.number_input("Quantidade", min_value=1, value=100)

valor_padrao_preco = float(preco_atual_sidebar) if preco_atual_sidebar else 35.00
preco_medio_input = st.sidebar.number_input("Preço da Compra (R$)", min_value=0.01, value=valor_padrao_preco, step=0.01)

# --- NOVIDADE: CÁLCULO DO TOTAL EM TEMPO REAL ANTES DE COMPRAR ---
total_simulado = qtd_input * preco_medio_input
st.sidebar.info(f"**Total da Ordem: R$ {total_simulado:,.2f}**")

col_btn1, col_btn2 = st.sidebar.columns(2)

if col_btn1.button("Salvar Ativo"):
    existe = False
    for ativo in st.session_state["carteira"]:
        if ativo["Ticker"] == ticker_input:
            novo_custo_total = (ativo["Preço Médio"] * ativo["Quantidade"]) + (preco_medio_input * qtd_input)
            ativo["Quantidade"] += qtd_input
            ativo["Preço Médio"] = novo_custo_total / ativo["Quantidade"]
            existe = True
            break
            
    if not existe:
        st.session_state["carteira"].append({
            "Ticker": ticker_input,
            "Quantidade": qtd_input,
            "Preço Médio": preco_medio_input
        })
    
    st.session_state["carteira"] = salvar_dados(st.session_state["carteira"])
    st.sidebar.success(f"{ticker_input} salvo!")
    st.rerun()

if col_btn2.button("Limpar Tudo"):
    st.session_state["carteira"] = []
    if os.path.exists(ARQUIVO_BANCO):
        os.remove(ARQUIVO_BANCO)
    st.rerun()

st.divider()

if len(st.session_state["carteira"]) > 0:
    st.subheader("Sua Carteira Atualizada")
    
    dados_brutos = [] # Guarda os números puros para os gráficos
    valor_total_investido = 0
    valor_total_atual = 0
    
    with st.spinner("Atualizando valores da carteira..."):
        for ativo in st.session_state["carteira"]:
            preco_atual = buscar_cotacao(ativo['Ticker'])
            
            if preco_atual is not None:
                custo_total = ativo["Quantidade"] * ativo["Preço Médio"]
                valor_atual_total = ativo["Quantidade"] * preco_atual
                lucro_prejuizo = valor_atual_total - custo_total
                rentabilidade = (lucro_prejuizo / custo_total) * 100 if custo_total > 0 else 0
                
                # Regra simples para separar: Se termina em 11, geralmente é FII.
                categoria = "FIIs" if ativo['Ticker'].endswith('11') else "Ações"
                
                valor_total_investido += custo_total
                valor_total_atual += valor_atual_total
                
                dados_brutos.append({
                    "Categoria": categoria,
                    "Ativo": ativo["Ticker"],
                    "Qtd": int(ativo["Quantidade"]),
                    "Preço Médio": ativo['Preço Médio'],
                    "Preço Atual": preco_atual,
                    "Custo Total": custo_total,
                    "Valor Atual": valor_atual_total,
                    "Lucro/Prejuízo": lucro_prejuizo,
                    "Rentabilidade (%)": rentabilidade
                })
            
    if dados_brutos:
        # Formatando a tabela para ficar bonita na tela
        df_formatado = pd.DataFrame(dados_brutos).copy()
        for col in ["Preço Médio", "Preço Atual", "Custo Total", "Valor Atual", "Lucro/Prejuízo"]:
            df_formatado[col] = df_formatado[col].apply(lambda x: f"R$ {x:,.2f}")
        df_formatado["Rentabilidade (%)"] = df_formatado["Rentabilidade (%)"].apply(lambda x: f"{x:,.2f}%")
        
        # Oculta a coluna "Categoria" da tabela para ficar mais limpo
        st.dataframe(df_formatado.drop(columns=["Categoria"]), use_container_width=True)
        
        st.divider()
        
        # --- PAINEL GLOBAL ---
        st.subheader("Resumo Global")
        col1, col2, col3 = st.columns(3)
        resultado_global = valor_total_atual - valor_total_investido
        
        col1.metric("Totalmente Investido", f"R$ {valor_total_investido:,.2f}")
        col2.metric("Patrimônio Atual", f"R$ {valor_total_atual:,.2f}", f"R$ {resultado_global:,.2f}")
        col3.metric("Rentabilidade Geral", f"{((resultado_global/valor_total_investido)*100 if valor_total_investido > 0 else 0):,.2f} %")
        
        st.divider()
        
        # --- NOVIDADE: SESSÃO DE GRÁFICOS ---
        st.subheader("📊 Distribuição do Patrimônio")
        df_graficos = pd.DataFrame(dados_brutos)
        
        col_graf1, col_graf2 = st.columns(2)
        
        # Gráfico 1: Ações vs FIIs (Gráfico de Rosca)
        df_pizza = df_graficos.groupby('Categoria')['Valor Atual'].sum().reset_index()
        fig_pizza = px.pie(df_pizza, values='Valor Atual', names='Categoria', hole=0.4, 
                           title="Divisão da Carteira", color_discrete_sequence=['#00c698', '#1b4d3e'])
        col_graf1.plotly_chart(fig_pizza, use_container_width=True)
        
        # Gráfico 2: Valor por Ativo (Gráfico de Barras)
        df_graficos = df_graficos.sort_values(by="Valor Atual", ascending=False)
        fig_barras = px.bar(df_graficos, x='Ativo', y='Valor Atual', color='Categoria',
                            title="Patrimônio por Ativo", text_auto='.2s', 
                            color_discrete_map={"Ações": "#1b4d3e", "FIIs": "#00c698"})
        col_graf2.plotly_chart(fig_barras, use_container_width=True)

else:
    st.info("Sua carteira está vazia. Cadastre seus ativos no menu lateral!")