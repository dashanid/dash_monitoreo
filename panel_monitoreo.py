## Dash

import dash
from dash import no_update
from dash import Dash, dash_table, dcc, callback, Output, Input, html

## specific dash libreries

import dash_daq as daq
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto

## visualization libreries

import plotly.express as px
import plotly.graph_objects as go

## data manipulation

import pandas as pd

import sqlite3, base64

# time procesing 

import requests

from io import BytesIO, StringIO
import os
from random import randint

import openpyxl

import datetime
from datetime import timedelta


def date_format(date_str):
    if not pd.isna(date_str):
        if type(date_str) == str:
            date = date_str.split(' ')[-1]
            return pd.to_datetime(date, dayfirst = True)
        else:
            return date_str

def preprocess_data(file_bytes):
    dfs = []
    xls = pd.ExcelFile(file_bytes)
    plataformas = []
    for sheet in xls.sheet_names:
        if 'Fechas' in sheet:
            plataformas.append(sheet)
    for plataforma in plataformas:
        ds = pd.read_excel(file_bytes, usecols = 'A:E', header = 3, sheet_name = plataforma)
        ds.dropna(axis = 0, how = 'all', inplace = True)
        ds['Inicio'] = ds['Fecha entrega'].shift(1, fill_value = pd.to_datetime('2023-01-01'))
        # ds['hito'] = ds['MES'].fillna('') + ds['Hito'].fillna('') + ' ' + Plataforma
        dfs.append(ds)
        dfs[-1]['Plataforma'] = plataforma.split(' ')[-1]
        
    dfs_2 = []
    for plataforma in plataformas:
        ds = pd.read_excel('data.xlsx', usecols = 'H:L', header = 3, sheet_name = plataforma)
        ds.dropna(axis = 0, how = 'all', inplace = True)
        ds['hito'] = ds['Hitos de pago ítem 2: Desarrollos'] + ' Desarrollo'
        mask = ds['hito'].notna()
        ds['Plataforma'] = plataforma.split(' ')[-1]
        ds = ds.loc[mask]
        ds['Fecha'] = ds['Fecha'].apply(date_format)
        ds['Inicio'] = ds['Fecha'].shift(1, fill_value = pd.to_datetime('2023-01-01'))
        # ds['Plataforma'] = plataforma.split(' ')[-1]
        dfs_2.append(ds)
    
    df_des = pd.concat(dfs_2)
    df_des.rename(columns = {'Monto a pagar.1': 'Monto a pagar'}, inplace = True)
    df_ini = pd.concat(dfs)
    df_ini['hito'] = df_ini['MES'].fillna('') + df_ini['Hito'].fillna('') 
    df_ini.rename(columns = {'Fecha entrega': 'Fecha'}, inplace = True)
    
    df_merged = pd.concat([df_ini, df_des]).loc[lambda x: ~x['hito'].str.contains('Total', na = False)]
    df_merged['Inicio'] = pd.to_datetime(df_merged['Inicio']).dt.date
    df_merged['Fecha'] = pd.to_datetime(df_merged['Fecha']).dt.date
    
    return df_merged.copy()[['hito', 'Inicio', 'Fecha', 'Monto a pagar', 'Plataforma']]

months = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}


access_token = os.environ['token']

account = 'dashanid'
repository = 'data_monitoreo'
path = 'data.xlsx'

r = requests.get(
    'https://api.github.com/repos/{owner}/{repo}/contents/{path}'.format(
        owner = account, 
        repo = repository, 
        path = path
    ),
    headers={
        'accept': 'application/vnd.github.v3.raw',
        'authorization': 'token {}'.format(access_token)
    }
)

file_bytes = BytesIO(r.content)

df = preprocess_data(file_bytes)

xls = pd.ExcelFile(file_bytes)
plataformas = []
for sheet in xls.sheet_names:
    if 'Fechas' in sheet:
        plataformas.append(sheet)

df_pc = pd.DataFrame([{'Plataforma' : plataforma, 'Documentación' : randint(0,10)} for plataforma in plataformas])

theme = {
    'dark': True,
    'detail': '#007439',
    'primary': '#00EA64',
    'secondary': '#6E6E6E',
}

today = datetime.date.today()


fig_1 = px.timeline(
    df,
    x_start = "Inicio",
    x_end = "Fecha",
    y = "hito",
    title = "Hitos",
    color = 'Plataforma',
    color_continuous_scale = 'rdylgn',
    range_color = [20,100]
)

fig_2 = px.timeline(
    df,
    x_start = "Inicio",
    x_end = "Fecha",
    y = "hito",
    title = "VPN",
    color = 'Plataforma',
    color_continuous_scale = 'rdylgn',
    range_color = [20,100]
)
fig_1.add_shape(
    go.layout.Shape(
        type="line",
        x0 = today,
        x1 = today,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(color="red", width=2)
    )
)

fig_2.add_shape(
    go.layout.Shape(
        type="line",
        x0 = today,
        x1 = today,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(color="red", width=2)
    )
)

fig_3 = px.pie(
    df_pc,
    values = 'Documentación',
    names = 'Plataforma',
    title = 'Documentación por plataforma'
)

fig_3.update_layout(legend=dict(
    orientation="h",
    # entrywidth=70,
    yanchor="top",
    y=0,
    xanchor="right",
    x=1
))

df_montos = df.loc[lambda x: ~x['Monto a pagar'].isna()]
presupuesto = df_montos['Monto a pagar'].sum()
ejecutado = df_montos.loc[lambda x: x['Fecha'] < today]['Monto a pagar'].sum()
porcentaje_ejecucion = (ejecutado*100)/presupuesto

options = []
for plataforma in plataformas:
    options.append({'label': plataforma.split(' ')[-1], 'value': plataforma.split(' ')[-1]})

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

app.layout = dbc.Container([
    html.Div(className='row', children='Panel de control de licitaciones.',
             style={'textAlign': 'center', 'color': 'black', 'fontSize': 30}),
    
    html.Div(className='row', children=[
        dcc.Dropdown(
            id='seleccion-de-plataforma',
            options = options,
            value='general',
            style={'width': '300px', 'margin-left': '20px'}
        ),
    ]),

    html.Br(),
    html.Br(),
    html.Br(),
    html.Div(
        id = 'pagos-warning'    
    ),
    
    # html.Div(
    #     className = 'row',
    #     children = dbc.Alert([
    #         html.I(className = "bi bi-x-octagon-fill me-2"),
    #         "Las siguientes VPN están vencidas",
    #         ],
    #         color = "danger",
    #         className = "d-flex align-items-center",
    # )),
    
    dbc.Row([
        dbc.Col(
            dcc.Graph(
                figure = fig_1,
                style = {'height': '400px', 'width': '800px'}
            ),
            width = 8
        ),
        dbc.Col([
            html.Br(),
            html.Div(
                children='Ejecución presupuestaria',
                style={'textAlign': 'center', 'color': 'black', 'fontSize': 20}
            ),
            html.Br(),
            html.Center(
                daq.Gauge(
                    showCurrentValue = True,
                    color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
                    min = 0,
                    max = 100,
                    value = porcentaje_ejecucion,
                    units = '%',
                    # label = 'Ejecución Presupuestaria',
                    # color = theme['primary'],
                    id='darktheme-daq-gauge',
                    className='dark-theme-control'
                )
            )
        ],
            width = 4
        )
    ]),
    
    dbc.Row([
        dbc.Col(
            dcc.Graph(
                figure = fig_2,
                style = {'height': '400px', 'width': '800px'}
            ),
            width = 8
        ),
        dbc.Col(
            dcc.Graph(
                figure = fig_3,
                style = {'height': '400px', 'width': '400px'}
            ),
            width = 4
        )
    ]),
    html.Div(className='row', children='Actualización de datos',
             style={'textAlign': 'center', 'color': 'black', 'fontSize': 30}),
    dcc.Upload(
        id = 'upload-data',
        children = html.Div([
            'Para actualizar los datos arrastra o selecciona el archivo'
        ]),
        style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            }
    ),
    html.Div(className='row', children='Planilla de pagos mensual',
             style={'textAlign': 'center', 'color': 'black', 'fontSize': 30}),

    dbc.Row([
        dbc.Col(
            dcc.Dropdown(id = 'date-year',
            options = [
                {'label': today.year - 2, 'value': today.year - 2},
                {'label': today.year - 1, 'value': today.year - 1},
                {'label': today.year, 'value': today.year},
                {'label': today.year + 1, 'value': today.year + 1}
            ],
            value = today.year
        )),
        dbc.Col(
            dcc.Dropdown(id = 'date-month',
            options = [
                {'label': 'Enero', 'value': 'enero'},
                {'label': 'Febrero', 'value': 'febrero'},
                {'label': 'Marzo', 'value': 'marzo'},
                {'label': 'Abril', 'value': 'abril'},
                {'label': 'Mayo', 'value': 'mayo'},
                {'label': 'Junio', 'value': 'junio'},
                {'label': 'Julio', 'value': 'julio'},
                {'label': 'Agosto', 'value': 'agosto'},
                {'label': 'Septiembre', 'value': 'septiembre'},
                {'label': 'Octubre', 'value': 'octubre'},
                {'label': 'Noviembre', 'value': 'noviembre'},
                {'label': 'Diciembre', 'value': 'diciembre'}
            ],
            value = today.year
            ))
    ]),
    dcc.Download(id = 'download'),
    html.Button('Descargar', id = 'btn_download')
])

@app.callback(
    [Output('pagos-warning', 'children'),
     Output('download', 'data')],
    [Input('seleccion-de-plataforma', 'value'),
     Input('upload-data', 'contents'),
     Input('upload-data', 'filename'),
     Input('date-year', 'value'),
     Input('date-month', 'value'),
     Input('btn_download', 'n_clicks')
    ]
)

def update_output(selected_value, data, file_name, year, month, n_clicks):
    df['Fecha'] = pd.to_datetime(df['Fecha'], format = '%Y-%m-%d')
    today_datetime = datetime.datetime.combine(today, datetime.datetime.min.time())
    late_vpn = df.loc[lambda x: (0 < (x['Fecha'] - today_datetime).dt.days) & ((pd.to_datetime(x['Fecha']) -  today_datetime).dt.days < 5)]
    if not late_vpn.empty:
        out = [
        dbc.Alert([
            html.I(className = "bi bi-exclamation-triangle-fill me-2"),
            "Los siguientes hitos están por vencer",
            ],
            color = "warning",
            className = "d-flex align-items-center",
        ),
        dash_table.DataTable(data = late_vpn.to_dict('records'))
        ]
    else:
        out = None

    if data:
        update_github(data, file_name)
    file = None
    
    if n_clicks:
        file = dcc.send_data_frame(generate_file(year, month).to_excel, f'pagos {month}.xlsx')
    return out, file

def update_github(data, file_name):
    try:
        content_type, content_string = data.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(BytesIO(decoded), sheet_name = 'Hoja 1')
        # csv_encoded = df.to_csv(index = False).encode('utf-8')
        auth = Auth.Token(access_token)
        g = Github(auth = auth)
        repo = g.get_repo('dashanid/data_monitoreo')
        contents = repo.get_contents('data.xlsx')
        repo.update_file('data.xlsx', f'modificacion a traves de python con fecha {str(date.today())}',decoded, contents.sha)        
        g.close
    
    except Exception as e:
            print(f"An error occurred: {e}")
            children = [html.Div('Error processing file. Please try again.', style={'color': 'red'})]

    return 

def generate_file(year, month):
    df_filtered = df.copy().loc[lambda x: (x['Fecha'].dt.month == months[month]) & (x['Fecha'].dt.year == year)]
    new_df = pd.DataFrame()
    new_df['Documento'] = ''
    new_df['rut proveedor'] = ''
    new_df['Descripcción Servicio'] = df_filtered['hito'] + ' ' + df_filtered['Plataforma']
    new_df['N°TED solicitante'] = ''
    new_df['Monto USD$'] = ''
    new_df['Monto CLP'] = df_filtered['Monto a pagar']
    new_df['Semama Estimada de pago'] = pd.to_datetime(df_filtered['Fecha']).dt.strftime('%d-%m-%Y')
    new_df['Observaciones'] = ''
    
    return new_df

if __name__ == '__main__':
    app.run_server(debug=True, port = 1919, jupyter_mode="external")
