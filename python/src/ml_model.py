"""
Módulo de Otimização de Planejamento de Produção (PPCP) com Dashboard Interativo

Este script utiliza Programação Linear para determinar o plano de produção semanal
ótimo e apresenta os resultados em um dashboard web interativo construído com Plotly Dash.

O objetivo é minimizar um custo operacional relativo, ponderando a produção em
horário normal e extra, respeitando restrições que podem ser ajustadas pelo usuário.

"""

import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import logging
from datetime import date, timedelta
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px

# --- 1. CONFIGURAÇÃO INICIAL E DADOS PADRÃO ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

DATA_INICIAL = date(2025, 9, 9)
SEMANAS = [1, 2, 3, 4]

# Demanda de vendas padrão
DEMANDA_VENDAS = {'Tecido Plano': 33000, 'Malharia': 42000}

# Entrega de tecidos padrão
ENTREGA_TECIDOS_PERC = {
    'Tecido Plano': [0.30, 0.20, 0.30, 0.20],
    'Malharia':     [0.40, 0.30, 0.20, 0.10]
}

# Capacidade produtiva SEMANAL e fatores de custo
# INTERPRETAÇÃO DA CAPACIDADE:
# 'cp_min': Representa a capacidade produtiva normal durante a semana (Segunda a Sexta).
# 'cp_max': Representa a capacidade total, incluindo a produção extra que pode ser feita no Sábado.
# A capacidade de hora extra (Sábado) é, portanto, a diferença: cp_max - cp_min.
CAPACIDADE_CORTE = {
    'TX7500 RT Vector A': {'tipo_tecido': ['Tecido Plano'], 'cp_min': 5000, 'cp_max': 6000, 'fator_custo_normal': 100, 'fator_custo_extra': 200},
    'TX7500 RT Vector B': {'tipo_tecido': ['Malharia'],     'cp_min': 9000, 'cp_max': 10800, 'fator_custo_normal': 100, 'fator_custo_extra': 200},
    'TX4500 Milenium': {'tipo_tecido': ['Tecido Plano', 'Malharia'], 'cp_min': 3000, 'cp_max': 3600, 'fator_custo_normal': 100, 'fator_custo_extra': 200}
}

CAPACIDADE_COSTURA = {
    # NOTA: A capacidade desta oficina foi aumentada para tornar o cenário de demanda viável.
    'Dieter Marquart ME': {'tipo_tecido': ['Tecido Plano'], 'cp_min': 4000, 'cp_max': 4800, 'fator_custo_normal': 100, 'fator_custo_extra': 200},
    'Joana Rodrigues Confecções SLU LTDA': {'tipo_tecido': ['Tecido Plano'], 'cp_min': 1000, 'cp_max': 1200,  'fator_custo_normal': 100, 'fator_custo_extra': 200},
    'Alberto Augusto Confecções': {'tipo_tecido': ['Malharia'],     'cp_min': 2500, 'cp_max': 3000, 'fator_custo_normal': 100, 'fator_custo_extra': 200},
    '3T Confecções EPP (Rio do Sul - SC)': {'tipo_tecido': ['Malharia'],     'cp_min': 2500, 'cp_max': 3000, 'fator_custo_normal': 100, 'fator_custo_extra': 200},
    '3T Confecções EPP (Brusque - SC)': {'tipo_tecido': ['Malharia'],     'cp_min': 2500, 'cp_max': 3000,  'fator_custo_normal': 100, 'fator_custo_extra': 200},
    '3T Confecções EPP (Blumenau - SC)': {'tipo_tecido': ['Tecido Plano', 'Malharia'], 'cp_min': 3000, 'cp_max': 3600, 'fator_custo_normal': 100, 'fator_custo_extra': 200}
}


# --- 2. LÓGICA DE OTIMIZAÇÃO (CORE) ---

def executar_otimizacao_producao(demanda, capacidade_corte_input, capacidade_costura_input):
    """
    Executa o modelo de otimização com base nos parâmetros fornecidos.
    """
    logging.info("Iniciando o sistema de otimização de produção...")

    # Pré-processamento dos dados
    disponibilidade_tecido = {}
    for tecido, percentuais in ENTREGA_TECIDOS_PERC.items():
        disponibilidade_tecido[tecido] = [sum(percentuais[:i+1]) * demanda[tecido] for i in range(len(SEMANAS))]

    model = LpProblem("Otimizacao_Producao_Textil", LpMinimize)

    # Definição das variáveis de decisão
    corte_vars, costura_vars = {}, {}
    turnos = ['normal', 'extra']
    
    for s in SEMANAS:
        for maq, dados in capacidade_corte_input.items():
            for tecido in dados['tipo_tecido']:
                for turno in turnos:
                    corte_vars[(s, maq, tecido, turno)] = LpVariable(f"Corte_S{s}_{maq}_{tecido}_{turno}", lowBound=0, cat='Integer')
        for of, dados in capacidade_costura_input.items():
            for tecido in dados['tipo_tecido']:
                for turno in turnos:
                    costura_vars[(s, of, tecido, turno)] = LpVariable(f"Costura_S{s}_{of}_{tecido}_{turno}", lowBound=0, cat='Integer')

    # Função Objetivo (Minimizar Custo Operacional Relativo)
    custo_corte = lpSum(
        corte_vars[(s, maq, tecido, 'normal')] * capacidade_corte_input[maq]['fator_custo_normal'] +
        corte_vars[(s, maq, tecido, 'extra')] * capacidade_corte_input[maq]['fator_custo_extra']
        for s, maq, tecido, _ in corte_vars)
    custo_costura = lpSum(
        costura_vars[(s, of, tecido, 'normal')] * capacidade_costura_input[of]['fator_custo_normal'] +
        costura_vars[(s, of, tecido, 'extra')] * capacidade_costura_input[of]['fator_custo_extra']
        for s, of, tecido, _ in costura_vars)
    model += custo_corte + custo_costura, "Custo_Operacional_Total"

    # Restrições
    # A) Atender à demanda
    for tecido, total in demanda.items():
        model += lpSum(costura_vars[(s, of, t, turno)] for s, of, t, turno in costura_vars if t == tecido) >= total, f"Demanda_{tecido.replace(' ', '_')}"

    # B) Capacidade de corte (SEMANAL)
    for s in SEMANAS:
        for maq, dados in capacidade_corte_input.items():
            # A produção em horário NORMAL (Seg-Sex) é limitada pela capacidade normal (cp_min).
            producao_normal = lpSum(corte_vars.get((s, maq, t, 'normal'), 0) for t in dados['tipo_tecido'])
            model += producao_normal <= dados['cp_min'], f"CP_Normal_Corte_S{s}_{maq.replace(' ', '_')}"
            
            # A produção em horário EXTRA (Sábado) tem como limite a capacidade adicional (cp_max - cp_min).
            producao_extra = lpSum(corte_vars.get((s, maq, t, 'extra'), 0) for t in dados['tipo_tecido'])
            model += producao_extra <= (dados['cp_max'] - dados['cp_min']), f"CP_Extra_Corte_S{s}_{maq.replace(' ', '_')}"

    # C) Capacidade de costura (SEMANAL)
    for s in SEMANAS:
        for of, dados in capacidade_costura_input.items():
            # A produção em horário NORMAL (Seg-Sex) é limitada pela capacidade normal (cp_min).
            producao_normal = lpSum(costura_vars.get((s, of, t, 'normal'), 0) for t in dados['tipo_tecido'])
            model += producao_normal <= dados['cp_min'], f"CP_Normal_Costura_S{s}_{of.replace(' ', '_')}"

            # A produção em horário EXTRA (Sábado) tem como limite a capacidade adicional (cp_max - cp_min).
            producao_extra = lpSum(costura_vars.get((s, of, t, 'extra'), 0) for t in dados['tipo_tecido'])
            model += producao_extra <= (dados['cp_max'] - dados['cp_min']), f"CP_Extra_Costura_S{s}_{of.replace(' ', '_')}"

    # D) Disponibilidade de matéria-prima
    for s_idx, s in enumerate(SEMANAS):
        for tecido in demanda.keys():
            model += lpSum(corte_vars.get((semana, maq, t, turno), 0) for semana in range(1, s + 1) for maq in capacidade_corte_input for t in capacidade_corte_input[maq]['tipo_tecido'] if t == tecido for turno in turnos) <= disponibilidade_tecido[tecido][s_idx], f"Disponibilidade_Tecido_{tecido.replace(' ','_')}_S{s}"

    # E) Fluxo de produção (corte -> costura)
    for s in SEMANAS:
        for tecido in demanda.keys():
            total_cortado = lpSum(corte_vars.get((semana, maq, t, turno), 0) for semana in range(1, s + 1) for maq in capacidade_corte_input for t in capacidade_corte_input[maq]['tipo_tecido'] if t == tecido for turno in turnos)
            total_costurado = lpSum(costura_vars.get((semana, of, t, turno), 0) for semana in range(1, s + 1) for of in capacidade_costura_input for t in capacidade_costura_input[of]['tipo_tecido'] if t == tecido for turno in turnos)
            model += total_costurado <= total_cortado, f"Fluxo_Corte_Costura_{tecido.replace(' ', '_')}_S{s}"

    # Resolução
    model.solve()

    # Processamento dos resultados
    if LpStatus[model.status] == 'Optimal':
        resultados = []
        for (s, maq, tecido, turno), var in corte_vars.items():
            if var.value() > 0:
                resultados.append(['Corte', s, maq, tecido, turno, var.value()])
        for (s, of, tecido, turno), var in costura_vars.items():
            if var.value() > 0:
                resultados.append(['Costura', s, of, tecido, turno, var.value()])
        
        df_resultados = pd.DataFrame(resultados, columns=['Setor', 'Semana', 'Recurso', 'Tecido', 'Turno', 'Quantidade (Peças)'])
        return LpStatus[model.status], model.objective.value(), df_resultados
    else:
        return LpStatus[model.status], None, pd.DataFrame()


# --- 3. CONSTRUÇÃO DO DASHBOARD INTERATIVO ---

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Otimizador de Produção Têxtil"

# -- Componentes da UI --
def create_capacidade_card(title, data, table_id):
    """Cria um card com uma tabela de dados para edição de capacidade."""
    display_data = []
    for recurso, valores in data.items():
        row = {
            'Recurso': recurso,
            'tipo_tecido_str': ', '.join(valores['tipo_tecido']),
            'cp_min': valores['cp_min'],
            'cp_max': valores['cp_max']
        }
        display_data.append(row)

    df = pd.DataFrame(display_data)
    
    return dbc.Card([
        dbc.CardHeader(html.H5(title)),
        dbc.CardBody([
            dash_table.DataTable(
                id=table_id,
                columns=[
                    {'name': 'Recurso', 'id': 'Recurso', 'type': 'text', 'editable': False},
                    {'name': 'Tipo de Tecido', 'id': 'tipo_tecido_str', 'type': 'text', 'editable': False},
                    {'name': 'Capacidade Semanal (Seg-Sex)', 'id': 'cp_min', 'type': 'numeric'},
                    {'name': 'Capacidade com Sábado (Total)', 'id': 'cp_max', 'type': 'numeric'}
                ],
                data=df.to_dict('records'),
                editable=True,
                style_table={'overflowX': 'auto'}
            )
        ])
    ], className="mb-4")

# -- Layout do App --
app.layout = dbc.Container([
    # Título
    dbc.Row(dbc.Col(html.H1("Dashboard de Otimização de Produção (PPCP)", className="text-center my-4"), width=12)),
    
    # Seção de Inputs
    dbc.Row([
        # Coluna de Demanda e Botão
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Parâmetros de Produção")),
                dbc.CardBody([
                    dbc.Label("Demanda de Tecido Plano (peças):"),
                    dbc.Input(id='demanda-plano', type='number', value=DEMANDA_VENDAS['Tecido Plano']),
                    dbc.Label("Demanda de Malharia (peças):", className="mt-3"),
                    dbc.Input(id='demanda-malharia', type='number', value=DEMANDA_VENDAS['Malharia']),
                    html.Div(
                        dbc.Button("Otimizar Produção", id='run-optimization-btn', color="primary", size="lg", className="w-100"),
                        className="d-grid gap-2 mt-4"
                    )
                ])
            ], className="mb-4")
        ], md=4),
        
        # Coluna das tabelas de capacidade
        dbc.Col([
            create_capacidade_card("Capacidade Semanal de Corte", CAPACIDADE_CORTE, 'table-corte'),
            create_capacidade_card("Capacidade Semanal de Costura", CAPACIDADE_COSTURA, 'table-costura')
        ], md=8)
    ]),

    # Seção de Resultados
    dbc.Row(dbc.Col(html.Hr(), width=12)),
    dbc.Row(dbc.Col(html.H2("Resultados da Otimização", className="text-center my-4"), width=12)),
    
    dbc.Row([
        dbc.Col(
            dcc.Loading(
                id="loading-results",
                type="circle",
                children=[
                    html.Div(id='optimization-summary'),
                    dcc.Graph(id='production-plan-graph'),
                    html.Div(id='production-plan-table')
                ]
            ), 
        width=12)
    ])

], fluid=True)


# --- 4. CALLBACKS PARA INTERATIVIDADE ---

@app.callback(
    [Output('optimization-summary', 'children'),
     Output('production-plan-graph', 'figure'),
     Output('production-plan-table', 'children')],
    [Input('run-optimization-btn', 'n_clicks')],
    [State('demanda-plano', 'value'),
     State('demanda-malharia', 'value'),
     State('table-corte', 'data'),
     State('table-costura', 'data')]
)
def update_optimization_results(n_clicks, demanda_plano, demanda_malharia, data_corte, data_costura):
    if n_clicks is None:
        return "", {}, ""

    # Formatar inputs para a função de otimização
    demanda_input = {'Tecido Plano': demanda_plano, 'Malharia': demanda_malharia}
    
    capacidade_corte_input = {
        row['Recurso']: {'tipo_tecido': CAPACIDADE_CORTE[row['Recurso']]['tipo_tecido'], 
                         'cp_min': row['cp_min'], 'cp_max': row['cp_max'],
                         'fator_custo_normal': CAPACIDADE_CORTE[row['Recurso']]['fator_custo_normal'],
                         'fator_custo_extra': CAPACIDADE_CORTE[row['Recurso']]['fator_custo_extra']}
        for row in data_corte
    }
    
    capacidade_costura_input = {
        row['Recurso']: {'tipo_tecido': CAPACIDADE_COSTURA[row['Recurso']]['tipo_tecido'], 
                         'cp_min': row['cp_min'], 'cp_max': row['cp_max'],
                         'fator_custo_normal': CAPACIDADE_COSTURA[row['Recurso']]['fator_custo_normal'],
                         'fator_custo_extra': CAPACIDADE_COSTURA[row['Recurso']]['fator_custo_extra']}
        for row in data_costura
    }

    # Executar otimização
    status, custo, df_resultados = executar_otimizacao_producao(demanda_input, capacidade_corte_input, capacidade_costura_input)
    
    if status == 'Optimal':
        # 1. Sumário
        summary = dbc.Alert(
            [
                html.H4("Otimização Concluída com Sucesso!", className="alert-heading")
            ],
            color="success"
        )
        
        # 2. Pós-processamento da Tabela de Resultados
        df_tabela_final = pd.DataFrame()
        if not df_resultados.empty:
            def get_cost_factor(row):
                recurso_data = (CAPACIDADE_CORTE if row['Setor'] == 'Corte' else CAPACIDADE_COSTURA).get(row['Recurso'])
                return recurso_data['fator_custo_normal'] if row['Turno'] == 'normal' else recurso_data['fator_custo_extra']

            df_resultados['fator_custo'] = df_resultados.apply(get_cost_factor, axis=1)
            df_resultados['custo_pontos'] = df_resultados['Quantidade (Peças)'] * df_resultados['fator_custo']

            agg_df = df_resultados.groupby(['Setor', 'Semana', 'Recurso', 'Tecido']).agg(
                quantidade_total=('Quantidade (Peças)', 'sum'),
                custo_total_pontos=('custo_pontos', 'sum')
            ).reset_index()
            
            agg_df['Fator Hora Médio (%)'] = (agg_df['custo_total_pontos'] / agg_df['quantidade_total']).round(2)
            
            df_tabela_final = agg_df.rename(columns={'quantidade_total': 'Quantidade (Peças)'})
            df_tabela_final = df_tabela_final[['Setor', 'Semana', 'Recurso', 'Tecido', 'Quantidade (Peças)', 'Fator Hora Médio (%)']]

        # 3. Gráfico (usa os dados originais, pois o px.bar agrega automaticamente)
        fig = px.bar(df_resultados, x="Semana", y="Quantidade (Peças)", color="Recurso",
                     facet_row="Setor", title="Plano de Produção Otimizado por Semana e Recurso",
                     labels={'Quantidade (Peças)': 'Quantidade Produzida (Peças)'},
                     category_orders={"Setor": ["Corte", "Costura"]})
        fig.update_layout(height=600)

        # 4. Tabela (usa o novo dataframe agregado)
        table = dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df_tabela_final.columns],
            data=df_tabela_final.to_dict('records'),
            sort_action="native",
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'minWidth': '100px', 'width': '150px', 'maxWidth': '300px'},
            style_header={'fontWeight': 'bold'}
        )
        
        return summary, fig, table
    else:
        # Mensagem de erro
        summary = dbc.Alert(
            [
                html.H4("Falha na Otimização", className="alert-heading"),
                html.P(f"Não foi possível encontrar uma solução ótima. Status: {status}. Verifique as restrições de capacidade e demanda.", className="mb-0")
            ],
            color="danger"
        )
        return summary, {}, ""


# --- 5. EXECUÇÃO DO SERVIDOR WEB ---

if __name__ == '__main__':
    app.run(debug=True)