# -*- coding: utf-8 -*-
# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import requests
import time
import datetime
import dateutil.parser
import os
import yaml
import random
import numpy as np
import matplotlib.pyplot as plt
import folium
from folium import plugins
import plotly.graph_objects as go  # or plotly.express as px
from datetime import date
import re
# --- CSS FORMATTING
main_colors = {
    'main-blue': '#343a40',
    'medium-blue-grey': 'rgb(77, 79, 91)',
    'superdark-green': 'rgb(41, 56, 55)',
    'dark-green': 'rgb(57, 81, 85)',
    'medium-green': 'rgb(93, 113, 120)',
    'light-green': 'rgb(186, 218, 212)',
    'pink-red': 'rgb(255, 101, 131)',
    'dark-pink-red': 'rgb(247, 80, 99)',
    'white': 'rgb(251, 251, 252)',
    'light-grey': 'rgb(208, 206, 206)'
}
main_container = {
    # 'margin': '0 auto',
    'margin-top': '30px',
    # 'background-color': main_colors['medium-green'],
}
color_red = {
    # 'background-color': main_colors['dark-pink-red'],
}
color_green = {
    # 'background-color': main_colors['medium-green'],
}
s_card_box ={
    "maxHeight": "150px",
    "overflow": "auto",
    "font-size":" 9px",

}
s_button = {
    'margin-left': '15px',
    'min-width': '100px',
    'float': 'left',
    'font-weight': ' 400',
    'color':  main_colors['white'],
    'text-align': ' center',
    'vertical-align': ' middle',
    '-webkit-user-select': ' none',
    '-moz-user-select': ' none',
    '-ms-user-select': ' none',
    'user-select': ' none',
    'border': ' 1px solid transparent',
    # 'padding': ' .375rem .75rem',
    'font-size': ' 1rem',
    # 'line-height': ' 1.5',
    'border-radius': ' .25rem',
    'background-color': main_colors['main-blue'],
    'border-color': '#343a40',
}
# isMapEmpty = True
def get(url, params=None, extend=True):
    global base_url, token
    set_token()
    if extend == True:
        url = base_url + url
    headers = {'Content-Type': 'application/json',
               'Authorization': f'Token {token}'}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response
def post(url, params=None, extend=True):
    global base_url, token
    set_token()
    if extend == True:
        url = base_url + url
    headers = {'Content-Type': 'application/json',
               'Authorization': f'Token {token}'}
    response = requests.post(url, headers=headers, data=params, timeout=10)
    response.raise_for_status()
    return response
def set_token():
    global token
    global token_timestamp
    try:
        token_timestamp
    except NameError:
        token_timestamp = 0
    if token_timestamp == 0:
        param = {
            'username': cfg['username'],
            'password': cfg['password']
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        url = cfg['authurl']
        res = requests.post(url, data=param)
        res.raise_for_status()
        token_timestamp = time.time()
        token = res.json()['token']
def splitlotlan(row):
    row['lon'] = row['location']['longitude']
    row['lat'] = row['location']['latitude']
    if row['lat'] == 37.4219983 and row['lon'] == -122.084:
        return None
    return row
# fig = px.line_mapbox(df, lat="lat", lon="lon", color="identifier", zoom=3, height=500)
#
# fig.update_layout(mapbox_style="stamen-terrain", mapbox_zoom=4, mapbox_center_lat = 41,
#     margin={"r":0,"t":0,"l":0,"b":0})
#
# fig.show()
dict_ambulances = {}
def init_dict_ambulances(start, end):
    ambulances = get_ambulances()
    for amb in ambulances:
        if amb["id"] not in dict_ambulances.keys():
            color_sample = generate_new_color()
            dict_ambulances[amb["id"]] = {
                "name": amb["identifier"], "dict_calls": [], "ambulance_color": color_sample}
        data = get(
            f'ambulance/{amb["id"]}/updates/?filter={start}T15:00:00.000Z,{end}T15:00:00.000Z').json()
        for d in data:  # insert at beginning, since api call gives us positions from newest to oldest
            dict_ambulances[amb["id"]]["dict_calls"].insert(
                0, {"location": d["location"], "timestamp": d["timestamp"]})
def get_ambulances():
    global cfg
    global base_url
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    SERVER = 'UCSD'
    cfg = cfg[SERVER]
    base_url = cfg['url']
    res = get('ambulance')
    ambulances = res.json()
    return ambulances
def get_ambulance_colors(ambulances):
    colors = list(main_colors.values())
    color_map = {}
    i = 0  # cycle through all main colors
    for ambulance in ambulances:
        id = ambulance['id']
        if id not in color_map:
            color_map[id] = colors[i]
            if i < len(colors) - 1:
                i += 1
            else:
                i = 0
    return color_map
def find_center():
    center = {'lon': 0, 'lat': 0}
    total_sum_long = 0
    total_sum_lat = 0
    total_calls_long = 0
    total_calls_lat = 0
    for id in dict_ambulances.keys():
        for call in dict_ambulances[id]['dict_calls']:
            total_sum_long += call['location']['longitude']
            total_sum_lat += call['location']['latitude']
            total_calls_long += 1
            total_calls_lat += 1
    mean_long = total_sum_long/total_calls_long
    mean_lat = total_sum_lat/total_calls_lat
    center['lon'] = mean_long
    center['lat'] = mean_lat
    return center


def get_fig(start, end, show_trace=False):
    # isMapEmpty = False
    ambulances = get_ambulances()
    ids = [ambulance['id'] for ambulance in ambulances]
    init_dict_ambulances(start, end)
    # app.logger.info(dict_ambulances[ambulances[4]['id']])
    vehicles = {}
    df = pd.DataFrame()
    for ambulance in ambulances:
        id = ambulance['id']
        # data = get(f'ambulance/{id}/updates/').json()#'?filter=2019-10-01T15:00:00.000Z,2020-10-30T15:00:00.000Z').json()
        data = get(
            f'ambulance/{id}/updates/?filter={start}T15:00:00.000Z,{end}T15:00:00.000Z').json()
        # app.logger.info(len(data))
        # if len(data) == 0:
        #     isMapEmpty = True
            # return
        data = [{'id': id, 'identifier': ambulance['identifier'], **item}
                for item in data]
        # if len(data) != 0:
        # app.logger.info(data[0])
        df = df.append(pd.DataFrame(data))
        # app.logger.info(df)
        # print(data)
        vehicles[id] = {'ambulance': ambulance, 'data': data}


    df = df.apply(splitlotlan, axis=1).dropna()
    data = df
    data['timestamp'] = pd.to_datetime(data.timestamp)
    data = data.sort_values(by='timestamp', ascending=True).reset_index()
    center = {'lon': data['lon'].mean(), 'lat': data['lat'].mean()}
    fig = go.Figure()
    # app.logger.info(data.loc[:5:5, 'id'])
    color_map = get_ambulance_colors(ambulances)
    # app.logger.info(data.shape[0])
    stepsize = 1
    if(data.shape[0] > 50):
        stepsize = data.shape[0]//50
    # b = a.loc[a['id']==10, 'lon']
    # app.logger.info(data)
    for step in range(0, data.shape[0], stepsize):
        # colors = [color_map[id] for id in data.loc[step-stepsize:step:1, 'id']]
        # app.logger.info(data.loc[:step:stepsize, 'id'])
        # app.logger.info(colors)
        a = data.loc[:step:1]
        amb_name = a['id']
        unique_ids = a.id.unique()
        # app.logger.info(a)
        # app.logger.info("number of ambulances in iter {}: {}".format(step, len(unique_ids)))
        lons = []
        lats = []
        colors = []
        texts = []
        # timestamps = []
        # app.logger.info(a.iloc[-1]['timestamp'])
        for id in unique_ids:
            lons.append(a.loc[a['id']==id, 'lon'].iloc[-1])
            lats.append(a.loc[a['id']==id, 'lat'].iloc[-1])
            texts.append(a.loc[a['id']==id, 'identifier'].iloc[-1] + " {}".format(a.loc[a['id']==id, 'timestamp'].iloc[-1]))
            # colors.append(color_map[id])
            colors.append(dict_ambulances[id]["ambulance_color"])
        fig.add_trace(
            go.Scattermapbox(
                visible=False,
                mode="markers",
                lon=lons,
                lat=lats,
                text=texts,
                showlegend=False,
                marker=go.scattermapbox.Marker(symbol='circle', color=colors, size=20),
            )
        )
        #  marker = {'size': 20, 'symbol':   "airport", 'color':dict_ambulances[id]['ambulance_color'] },
        # marker={'size': 10, 'color':dict_ambulances[id]['ambulance_color']}
    # for id in dict_ambulances.keys():
    #     # for step in range(2, data.shape[0], 5):
    #     for i in range(0, len(dict_ambulances[id]['dict_calls']), 50): # need to fix later
    #         sublist = dict_ambulances[id]['dict_calls'][:i]
    #         sublist_long = [location['location']['longitude'] for location in sublist]
    #         sublist_lat = [location['location']['latitude'] for location in sublist]
    #         fig.add_trace(
    #             go.Scattermapbox(
    #                 visible=False,
    #                 mode="markers",
    #                 lon=sublist_long,
    #                 lat=sublist_lat,
    #                 marker={'size': 10, 'color':dict_ambulances[id]['ambulance_color']}))
    # center = find_center()
    fig.update_layout(
        margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
         height=700,
        mapbox={
            'center': center,
            'style': "stamen-terrain",
            'zoom': 8}
    )
    fig.data[0].visible = True
    # app.logger.info(fig.data)
    steps = []
    for i in range(len(fig.data)):
        step = dict(
            method="update",
            label="{}".format(str(a.iloc[i*stepsize]['timestamp'])[:19]),
            args=[{"visible": [False] * len(fig.data)},
                  {"title": "Slider switched to step: " + str(i)}],  # layout attribute
        )
        if show_trace:
            for j in range(i+1):
                step["args"][0]["visible"][j] = True  # Toggle i'th trace to "visible"
        else:
            step["args"][0]["visible"][i] = True
        steps.append(step)
    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Timestamp: "},
        pad={"t": 25, "b": -10, "l": 40, "r": 40},
        steps=steps
    )]
    fig.update_layout(
        sliders=sliders
    )


    # fig.show()
    # fig.write_html("plotly.html")
    return fig
external_stylesheets = [dbc.themes.BOOTSTRAP]
# external_stylesheets = [
#     'https://codepen.io/chriddyp/pen/bWLwgP.css']
# external_stylesheets = [
#     'https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
ALLOWED_TYPES = (
    "text", "number", "password", "email", "search",
    "tel", "url", "range", "hidden",
)
def get_random_color(pastel_factor=0.5):
    return [(x+pastel_factor)/(1.0+pastel_factor) for x in [random.uniform(0, 1.0) for i in [1, 2, 3]]]

def generate_new_color():
    def rand(): return random.randint(100, 255)
    return '#%02X%02X%02X' % (rand(), rand(), rand())
def generate_ambulance_card(ambulance_id):
    # app.logger.info(ambulance_id)
    # app.logger.info(dict_ambulances[ambulance_id])
    single_ambulance = dict_ambulances[ambulance_id]
    return dbc.Card([
        dbc.CardBody(
            [
                html.H4(single_ambulance["name"],
                        className="card-title text-center"),
                html.Div([
                        #  html.P(
                        #      str(single_ambulance["dict_calls"]),
                        #      className="card-text", style={}
                        #  ),
                         ], style = s_card_box)
                # dbc.Button(
                #     "Go", color="primary", className="mt-3"),
            ]
        ),
    ],
        className="m-3",
        # color = color_sample,
        style={"backgroundColor": single_ambulance["ambulance_color"]},
    )
    # return dbc.Button(children=str(team_shortName),
    #                   color="primary",
    #                   className="mr-1",
    #                   id=str(team_shortName))
# app = dash.Dash(external_stylesheets=[])
#  html.Div(className = "container-sm", children = [
#     ]),
app.layout = html.Div(children=[
    html.Div(className="container",  style=main_container, children=[
        html.H1(children='Mileage Report', className="mb-4"),
        html.H3(id='button-clicks'),
        dbc.Row(
            [
                dcc.Input(
                    id='input-field',
                    type='text',
                    className='mr-3',
                    style={"display": "none"}
                ),
                html.Div([
                    dcc.DatePickerRange(
                        id='my-date-picker-range',
                        min_date_allowed=date(1995, 8, 5),
                        max_date_allowed=date.today() + datetime.timedelta(days=1),
                        initial_visible_month=date.today(),
                        end_date=date.today()
                    ),
                    html.Div(id='output-container-date-picker-range')
                ]),
                dbc.Button("Generate", id='generate',
                           className="mr-2",  style=s_button),
                dbc.Button("Reset", id='reset', className="mr-2", style=s_button),
                dbc.Button("Export", className="mr-2 ", style=s_button),
            ],
            align="center", justify="center", className="mb-5", style={'color': main_colors['main-blue']}
        ),
        html.Div(
            [
                dcc.Graph(
                    id='map-graph',
                    figure=get_fig(date(2019, 10, 1), date(2020, 10, 30))
                ),
            ],
            # align="center", justify="center", style=color_green
        ),
        dbc.Row(
            [
                dbc.Col([
                    html.H3(children='Testing Ambulances header'),
                    html.Div(
                        ""),
                ],  id='output-ambulances', width=12, style=color_red),
                dbc.Col([
                ], width=0, style=color_green),
            ]
        ),
    ]),
]
)
@app.callback(
    dash.dependencies.Output('output-ambulances', 'children'),
    [dash.dependencies.Input('input-field', 'value')])
def update_col(prop):
    hrm = dbc.Col(children=[generate_ambulance_card(i)
                            for i in dict_ambulances])
    # hm = generate_ambulance_card(dict_ambulances["8"])
    # hm = generate_ambulance_card(list(dict_ambulances.keys())[0])
    # app.logger.info(hrm)
    return hrm

@app.callback(
    dash.dependencies.Output('map-graph', 'figure'),
    [dash.dependencies.Input('my-date-picker-range', 'start_date'),
     dash.dependencies.Input('my-date-picker-range', 'end_date'),
     dash.dependencies.Input('generate', 'n_clicks'),
     dash.dependencies.Input('reset', 'n_clicks')])
def update_output(start_date, end_date, generate, reset):
    ctx = dash.callback_context
    button_id = ''
    generate_n_clicks = False
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        generate_n_clicks = True
    if button_id == 'generate' and generate_n_clicks:
        ret_fig = get_fig(start_date, end_date)
        if True:
            # app.logger.info('HERE')
            return ret_fig
    return get_fig(date(2019, 10, 1), date(2020, 10, 30))

if __name__ == '__main__':
    app.run_server(debug=True)
