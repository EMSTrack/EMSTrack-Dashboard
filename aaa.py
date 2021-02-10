# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
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

import plotly.graph_objects as go # or plotly.express as px

from datetime import date
import re


import dash_bootstrap_components as dbc


def get (url, params=None, extend=True):
    global base_url, token
    set_token()
    if extend == True:
        url = base_url + url
    headers = {'Content-Type': 'application/json', 'Authorization': f'Token {token}'}

    response = requests.get(url, params=params, headers = headers)
    response.raise_for_status()
    return response

def post (url, params=None, extend=True):
    global base_url, token
    set_token()
    if extend == True:
        url = base_url + url
    headers = {'Content-Type': 'application/json', 'Authorization': f'Token {token}'}

    response = requests.post(url, headers = headers, data=params,timeout=10)
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
            'username' : cfg['username'],
            'password' : cfg['password']
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

def get_fig(start, end):
    global cfg
    global base_url
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    SERVER = 'EMSTrack'
    cfg = cfg[SERVER]
    base_url = cfg['url']

    res = get('ambulance')
    ambulances = res.json()
    vehicles = {}
    df = pd.DataFrame()
    for ambulance in ambulances:
        id = ambulance['id']
        # data = get(f'ambulance/{id}/updates/').json()#'?filter=2019-10-01T15:00:00.000Z,2020-10-30T15:00:00.000Z').json()
        data = get(f'ambulance/{id}/updates/?filter={start}T15:00:00.000Z,{end}T15:00:00.000Z').json()
        data = [{'id':id, 'identifier':ambulance['identifier'], **item} for item in data]
        df = df.append(pd.DataFrame(data))
        #print(data)
        vehicles[id] = {'ambulance':ambulance, 'data':data}
    df = df.apply(splitlotlan, axis=1).dropna()
    data=df
    data['timestamp'] = pd.to_datetime(data.timestamp)
    data = data.sort_values(by='timestamp', ascending=True).reset_index()
    center = {'lon': data['lon'].mean(), 'lat':data['lat'].mean()}
    fig = go.Figure()

    for step in range(2,data.shape[0],5):
        fig.add_trace(
            go.Scattermapbox(
            visible=False,
            mode = "markers+lines",
            lon = data.loc[:step:5,'lon'],
            lat = data.loc[:step:5,'lat'],
            marker = {'size': 10}))

    fig.update_layout(
        margin ={'l':0,'t':0,'b':0,'r':0},
        mapbox = {
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



external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css']
# external_stylesheets = [
#     'https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


ALLOWED_TYPES = (
    "text", "number", "password", "email", "search",
    "tel", "url", "range", "hidden",
)


# app = dash.Dash(external_stylesheets=[])

app.layout = html.Div(className="p-5", children=[
    html.H1(children='Mileage Report'),
    html.H3(id='button-clicks'),

    html.Div([
        dcc.DatePickerRange(
             id='my-date-picker-range',
             min_date_allowed=date(1995, 8, 5),
             max_date_allowed=date.today() + datetime.timedelta(days = 1),
             initial_visible_month=date.today(),
             end_date=date.today()
             ),
        html.Div(id='output-container-date-picker-range')
    ]),

    dbc.Button("Generate", id='generate', className="mr-2"),
    dbc.Button("Reset", className="mr-2"),
    dbc.Button("Export", className="mr-2 "),

    dcc.Graph(
        id='map-graph',
        figure=get_fig(date(2019, 10, 1), date(2020, 10, 30))
    ),

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
        app.logger.info(string_prefix)
        return get_fig(start_date, end_date)
    return get_fig(date(2019, 10, 1), date(2020, 10, 30))
    # if len(string_prefix) == len('You have selected: '):
    #     return 'Select a date to see it displayed here'
    # else:
    #     return string_prefix


if __name__ == '__main__':
    app.run_server(debug=True)
