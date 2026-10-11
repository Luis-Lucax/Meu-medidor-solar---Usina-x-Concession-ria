import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os

# Configuração da Página
st.set_page_config(
    page_title="Gestão Solar & Concessionária",
    page_icon="☀️",
    layout="wide"
)

# Arquivos de Banco de Dados Local (CSV)
DATA_FILE = "leituras_solar.csv"
APPLIANCES_FILE = "eletrodomesticos.csv"
SIM_LOG_FILE = "simulacao_diaria.csv"

def carregar_dados(arquivo, colunas_padrao):
    if os.path.exists(arquivo):
        try:
            return pd.read_csv(arquivo)
        except Exception:
            return pd.DataFrame(columns=colunas_padrao)
    return pd.DataFrame(columns=colunas_padrao)

def salvar_dados(df, arquivo):
    df.to_csv(arquivo, index=False)

# Inicializar DataFrames
df_leituras = carregar_dados(DATA_FILE, [
    "Data", "Turno", "Consumo_03", "Injecao_103", "Geracao_Inversor", "Foto"
])
df_appliances = carregar_dados(APPLIANCES_FILE, [
    "Nome", "Potencia_W", "Horas_Dia"
])
df_sim = carregar_dados(SIM_LOG_FILE, [
    "Data", "Consumo_Estimado_kWh"
])

st.title("☀️ Sistema de Acompanhamento Solar & Concessionária")
st.markdown("Gerencie sua geração fotovoltaica, leituras da concessionária (Cód. 03 e 103), autoconsumo e simulação de eletrodomésticos.")

# Abas do Aplicativo
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📝 Registrar Leitura", 
    "📊 Histórico & Gráficos", 
    "⚡ Simulador de Aparelhos", 
    "📋 Relatórios Detalhados",
    "⚙️ Gerenciar Dados"
])
with aba1:
    st.subheader("Registro Diário de Leituras")
    st.markdown("Insira os dados do medidor da concessionária (relógio) e as informações do aplicativo do inversor.")
    
    with st.form("form_leitura"):
        col1, col2 = st.columns(2)
        with col1:
            data_leitura = st.date_input("Data da Leitura", value=date.today())
            turno = st.selectbox("Turno", ["Manhã (Antes de ligar)", "Noite (Após parar)"])
        with col2:
            consumo_03 = st.number_input("Consumo Rede (Cód. 03 - kWh)", min_value=0.0, format="%.2f")
            injecao_103 = st.number_input("Injeção Rede (Cód. 103 - kWh)", min_value=0.0, format="%.2f")
            
        geracao_inversor = st.number_input("Geração Total do Inversor no Dia (kWh) - Preencher à Noite", min_value=0.0, format="%.2f", value=0.0)
        foto_comprovante = st.file_uploader("Enviar Foto do Visor / Inversor (Opcional)", type=["jpg", "png", "jpeg"])
        
        submitted = st.form_submit_button("Salvar Leitura")
        if submitted:
            nova_linha = pd.DataFrame([{
                "Data": str(data_leitura),
                "Turno": turno,
                "Consumo_03": consumo_03,
                "Injecao_103": injecao_103,
                "Geracao_Inversor": geracao_inversor,
                "Foto": foto_comprovante.name if foto_comprovante else "Nenhuma"
            }])
            df_leituras = pd.concat([df_leituras, nova_linha], ignore_index=True)
            salvar_dados(df_leituras, DATA_FILE)
            st.success("Leitura registrada com sucesso!")

with aba2:
    st.subheader("📊 Histórico e Indicadores de Energia")
    if not df_leituras.empty:
        st.dataframe(df_leituras, use_container_width=True)
        
        # Gráficos interativos com Plotly
        df_plot = df_leituras.copy()
        df_plot['Data'] = pd.to_datetime(df_plot['Data'])
        
        fig = px.line(df_plot, x='Data', y=['Consumo_03', 'Injecao_103', 'Geracao_Inversor'], 
                      title="Evolução de Consumo, Injeção e Geração Solar",
                      labels={"value": "kWh", "variable": "Métrica"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma leitura registrada ainda.")

with aba3:
    st.subheader("⚡ Simulador de Consumo de Eletrodomésticos")
    st.markdown("Cadastre seus aparelhos para estimar o consumo diário e comparar com os dados reais.")
    
    with st.form("form_aparelho"):
        c1, c2, c3 = st.columns(3)
        with c1:
            nome_ap = st.text_input("Nome do Aparelho (ex: Ar Condicionado)")
        with c2:
            pot_ap = st.number_input("Potência (Watts - W)", min_value=0.0, value=1000.0)
        with c3:
            horas_ap = st.number_input("Horas de Uso por Dia", min_value=0.0, max_value=24.0, value=4.0)
            
        add_ap = st.form_submit_button("Adicionar Aparelho")
        if add_ap and nome_ap:
            novo_ap = pd.DataFrame([{"Nome": nome_ap, "Potencia_W": pot_ap, "Horas_Dia": horas_ap}])
            df_appliances = pd.concat([df_appliances, novo_ap], ignore_index=True)
            salvar_dados(df_appliances, APPLIANCES_FILE)
            st.success(f"Aparelho '{nome_ap}' cadastrado!")

    if not df_appliances.empty:
        st.markdown("#### Aparelhos Cadastrados")
        st.dataframe(df_appliances, use_container_width=True)
        
        # Cálculo de consumo estimado
        df_appliances['Consumo_Diario_kWh'] = (df_appliances['Potencia_W'] * df_appliances['Horas_Dia']) / 1000.0
        total_estimado_dia = df_appliances['Consumo_Diario_kWh'].sum()
        
        st.metric("Consumo Total Estimado dos Aparelhos (Por Dia)", f"{total_estimado_dia:.2f} kWh")
    else:
        st.info("Nenhum eletrodoméstico cadastrado.")

with aba4:
    st.subheader("📋 Relatórios Detalhes e Balanço Energético")
    if not df_leituras.empty:
        st.markdown("Aqui você acompanha o balanço entre o que foi gerado pelo inversor e o que passou pela concessionária.")
        # Processamento simplificado para exibição de balanço
        st.dataframe(df_leituras.groupby("Data")[["Consumo_03", "Injecao_103", "Geracao_Inversor"]].sum(), use_container_width=True)
    else:
        st.info("Cadastre leituras para gerar relatórios.")

with aba5:
    st.subheader("⚙️ Gerenciamento de Dados")
    if st.button("Limpar Todos os Registros de Leituras"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.warning("Dados apagados. Recarregue a página.")
