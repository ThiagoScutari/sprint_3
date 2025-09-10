# === IMPORTS ===
import os
import logging
from datetime import datetime

import pandas as pd
import plotly.express as px
from db_manager import DatabaseManager


# === CONFIGURAÇÕES ===
PASTA_SAIDA = 'output'
os.makedirs(PASTA_SAIDA, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


# === CARREGAMENTO DE DADOS ===
def carregar_dados(db: DatabaseManager) -> pd.DataFrame:
    try:
        leituras = db.buscar_leituras()
        df = pd.DataFrame(leituras, columns=[
            'id', 'codMaquina', 'ordemProducao', 'dataHora', 'distancia', 'folhas'
        ])
        df['dataHora'] = pd.to_datetime(df['dataHora'], errors='coerce')
        df = df.dropna(subset=['dataHora'])  # Remove inválidas
        return df
    except Exception as e:
        logging.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


# === ANÁLISE ===
def folhas_por_ordem(df: pd.DataFrame) -> pd.DataFrame:
    resumo = df.groupby(['ordemProducao', 'codMaquina']).agg({
        'dataHora': ['min', 'max'],
        'folhas': 'max'
    }).reset_index()
    resumo.columns = ['ordemProducao', 'codMaquina', 'inicio', 'fim', 'total_folhas']
    return resumo.sort_values(by='inicio')


def produtividade_por_maquina(df: pd.DataFrame) -> pd.DataFrame:
    # Calcular produtividade por ordem + máquina
    resumo = df.groupby(['ordemProducao', 'codMaquina']).agg({
        'dataHora': ['min', 'max'],
        'folhas': 'max'
    }).reset_index()
    
    resumo.columns = ['ordemProducao', 'codMaquina', 'inicio', 'fim', 'folhas']
    resumo['tempo_horas'] = (resumo['fim'] - resumo['inicio']).dt.total_seconds() / 3600
    resumo = resumo[resumo['tempo_horas'] > 0]

    # Agora agregamos POR MÁQUINA
    agregada = resumo.groupby('codMaquina').agg({
        'folhas': 'sum',
        'tempo_horas': 'sum'
    }).reset_index()

    agregada['folhas_por_hora'] = agregada['folhas'] / agregada['tempo_horas']

    return agregada



def folhas_por_dia(df: pd.DataFrame) -> pd.DataFrame:
    df['data'] = df['dataHora'].dt.date
    folhas_dia = df.groupby(['data', 'codMaquina', 'ordemProducao'])['folhas'].max().reset_index()
    return folhas_dia.sort_values(by=['data', 'codMaquina', 'ordemProducao'])


# === EXPORTAÇÃO ===
def exportar_para_csv(df: pd.DataFrame, nome_arquivo: str):
    caminho = os.path.join(PASTA_SAIDA, nome_arquivo)
    try:
        df.to_csv(caminho, index=False, sep=';', encoding='utf-8')
        logging.info(f"CSV exportado com sucesso: {caminho}")
    except Exception as e:
        logging.error(f"Erro ao exportar CSV: {e}")


def exportar_para_json(df: pd.DataFrame, nome_arquivo: str):
    caminho = os.path.join(PASTA_SAIDA, nome_arquivo)
    try:
        df.to_json(caminho, orient='records', indent=4, date_format='iso')
        logging.info(f"JSON exportado com sucesso: {caminho}")
    except Exception as e:
        logging.error(f"Erro ao exportar JSON: {e}")


# === VISUALIZAÇÃO (PLOTLY) ===
def plot_folhas_por_ordem_plotly(df: pd.DataFrame):
    df['op_maquina'] = df['ordemProducao'] + " (" + df['codMaquina'] + ")"

    fig = px.bar(
        df,
        x='op_maquina',
        y='total_folhas',
        color='codMaquina',
        title='Total de Folhas por Ordem de Produção e Máquina',
        labels={'op_maquina': 'OP + Máquina', 'total_folhas': 'Folhas'},
        text='total_folhas'
    )
    fig.update_layout(xaxis_tickangle=-30)
    fig.show()


def plot_produtividade_maquina_plotly(df: pd.DataFrame):
    fig = px.bar(
        df,
        x='codMaquina',
        y='folhas_por_hora',
        color='codMaquina',
        title='Produtividade Média por Máquina (Folhas/Hora)',
        labels={'codMaquina': 'Máquina', 'folhas_por_hora': 'Folhas/Hora'},
        text='folhas_por_hora'
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.show()


def plot_folhas_por_dia_plotly(df: pd.DataFrame):
    df_grouped = df.groupby(['data', 'codMaquina'])['folhas'].sum().reset_index()
    fig = px.line(
        df_grouped,
        x='data',
        y='folhas',
        color='codMaquina',
        title='Folhas por Dia por Máquina',
        labels={'data': 'Data', 'folhas': 'Folhas', 'codMaquina': 'Máquina'},
        markers=True
    )
    fig.update_xaxes(dtick="D", tickformat="%d/%m")
    fig.show()
