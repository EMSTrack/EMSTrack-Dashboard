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
            dict_ambulances[amb["id"]] = {"name": amb["identifier"], "dict_calls": []}
        data = get(
            f'ambulance/{amb["id"]}/updates/?filter={start}T15:00:00.000Z,{end}T15:00:00.000Z').json()
        for d in data: # insert at beginning, since api call gives us positions from newest to oldest
            dict_ambulances[amb["id"]]["dict_calls"].insert(0, {"location": d["location"], "timestamp": d["timestamp"]})

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
    i = 0 # cycle through all main colors
    for ambulance in ambulances:
        id = ambulance['id']
        if id not in color_map:
            color_map[id] = colors[i]
            if i < len(colors) - 1:
                i += 1
            else:
                i = 0
    return color_map

def get_fig(start, end):
    ambulances = get_ambulances()
    ids = [ambulance['id'] for ambulance in ambulances]
    init_dict_ambulances(start, end)
    app.logger.info(dict_ambulances[ambulances[4]['id']])
    vehicles = {}
    df = pd.DataFrame()
    for ambulance in ambulances:
        id = ambulance['id']
        # data = get(f'ambulance/{id}/updates/').json()#'?filter=2019-10-01T15:00:00.000Z,2020-10-30T15:00:00.000Z').json()
        data = get(
            f'ambulance/{id}/updates/?filter={start}T15:00:00.000Z,{end}T15:00:00.000Z').json()
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
    color_map = get_ambulance_colors(ambulances)
    # app.logger.info(color_map)
    for step in range(2, data.shape[0], 5):
        fig.add_trace(
            go.Scattermapbox(
                visible=False,
                mode="markers+lines",
                lon=data.loc[:step:5, 'lon'],
                lat=data.loc[:step:5, 'lat'],
                marker={'size': 10}))

    fig.update_layout(
        margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
        mapbox={
            'center': center,
            'style': "stamen-terrain",
            'zoom': 8}
    )

    fig.data[0].visible = True

    steps = []
    for i in range(len(fig.data)):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)},
                  {"title": "Slider switched to step: " + str(i)}],  # layout attribute
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        steps.append(step)

    sliders = [dict(
        active=10,
        currentvalue={"prefix": "Frequency: "},
        pad={"t": 50},
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

# app = dash.Dash(external_stylesheets=[])

#  html.Div(className = "container-sm", children = [
#     ]),

app.layout = html.Div(children=[
    html.Div(className="container",  style=main_container, children=[

        html.H1(children='Mileage Report', className="mb-4"),

        html.H3(id='button-clicks'),

        dbc.Row(
            [
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
                dbc.Button("Reset", className="mr-2", style=s_button),
                dbc.Button("Export", className="mr-2 ", style=s_button),
            ],
            align="center", justify="center", className="mb-5", style={'color': main_colors['main-blue']}
        ),
        dbc.Row(
            [
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody(
                            [
                                html.H4("ambulance title",
                                        className="card-title"),
                                html.P(
                                    "title text",
                                    className="card-text",
                                ),
                                dbc.Button(
                                    "Go", color="primary"),
                            ]
                        ),
                    ],
                        className="m-3",
                        # style={"width": "18rem"},
                    ),

                    dbc.Card([
                        dbc.CardBody(
                             [
                                 html.H4("ambulance title",
                                         className="card-title"),
                                 html.P(
                                     "title text",
                                     className="card-text",
                                 ),
                                 dbc.Button(
                                     "Go", color="primary"),
                             ]
                             ),
                    ],
                        className="m-3",
                        # style={"width": "18rem"},
                    ),

                    dbc.Card([
                        dbc.CardBody(
                            [
                                html.H4("ambulance title",
                                        className="card-title"),
                                html.P(
                                    "title text",
                                    className="card-text",
                                ),
                                dbc.Button(
                                    "Go", color="primary"),
                            ]
                        ),
                    ],
                        className="m-3",
                        # style={"width": "18rem"},
                    ),

                    dbc.Card([
                        dbc.CardBody(
                            [
                                html.H4("ambulance title",
                                        className="card-title"),
                                html.P(
                                    "title text",
                                    className="card-text",
                                ),
                                dbc.Button(
                                    "Go", color="primary"),
                            ]
                        ),
                    ],
                        className="m-3",
                        # style={"width": "18rem"},
                    ),


                    html.Div(
                        ""),

                ], width=6, style=color_red),
                dbc.Col([

                    dcc.Graph(
                        id='map-graph',
                        figure=get_fig(date(2019, 10, 1), date(2020, 10, 30))
                    ),

                ], width=6, style=color_green),
            ]
        ),

    ]),

]

)

@app.callback(
    dash.dependencies.Output('map-graph', 'figure'),
    [dash.dependencies.Input('my-date-picker-range', 'start_date'),
     dash.dependencies.Input('my-date-picker-range', 'end_date'),
     dash.dependencies.Input('generate', 'n_clicks')])
def update_output(start_date, end_date, n_clicks):
    string_prefix = 'You have selected: '
    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
        start_date_string = start_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'Start Date: ' + start_date_string + ' | '
    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
        end_date_string = end_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'End Date: ' + end_date_string
    if n_clicks is not None:
        init_dict_ambulances()
        # app.logger.info(dict_ambulances)
        return get_fig(start_date, end_date)
    return get_fig(date(2019, 10, 1), date(2020, 10, 30))
    # if len(string_prefix) == len('You have selected: '):
    #     return 'Select a date to see it displayed here'
    # else:
    #     return string_prefix

if __name__ == '__main__':
    app.run_server(debug=True)