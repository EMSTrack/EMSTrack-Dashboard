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
from datetime import datetime as dt
import re
from haversine import haversine, Unit
from dash.exceptions import PreventUpdate
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
generate_n_clicks = False
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
# dict_ambulances = {}
def init_dict_ambulances(start, end):
    dict_ambulances = {}
    # ambulances = get_ambulances()
    # app.logger.info("DICTAMB")
    for amb in ambulances:
        if amb["id"] not in dict_ambulances.keys():
            color_sample = generate_new_color()
            dict_ambulances[amb["id"]] = {
                "name": amb["identifier"], "dict_calls": [], "ambulance_color": color_sample}
        data = get(
            f'ambulance/{amb["id"]}/updates/?filter={start}T15:00:00.000Z,{end}T15:00:00.000Z').json()
        for d in data:  
            # if not (dict_ambulances[amb["id"]]["name"] == "7BST414" and ((d["location"]["longitude"] == -122.084 and d["location"]["latitude"] == 37.4219983) or (d["location"]["longitude"] == -117.00371 and d["location"]["latitude"] == 32.5027))):
            # insert at beginning, since api call gives us positions from newest to oldest
            dict_ambulances[amb["id"]]["dict_calls"].insert(
                0, {"location": d["location"], "timestamp": d["timestamp"]})
    # app.logger.info(dict_ambulances)
    
    return dict_ambulances
    # app.logger.info(f"initial: {dict_ambulances}")
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
# def find_center():
#     center = {'lon': 0, 'lat': 0}
#     total_sum_long = 0
#     total_sum_lat = 0
#     total_calls_long = 0
#     total_calls_lat = 0
#     for id in dict_ambulances.keys():
#         for call in dict_ambulances[id]['dict_calls']:
#             total_sum_long += call['location']['longitude']
#             total_sum_lat += call['location']['latitude']
#             total_calls_long += 1
#             total_calls_lat += 1
#     mean_long = total_sum_long/total_calls_long
#     mean_lat = total_sum_lat/total_calls_lat
#     center['lon'] = mean_long
#     center['lat'] = mean_lat
#     return center

def days_between(d1, d2):
    d1 = dt.strptime(d1, "%Y-%m-%dT%H:%M:%S")
    d2 = dt.strptime(d2, "%Y-%m-%dT%H:%M:%S")
    return abs((d2 - d1).days)

def get_fig(start, end, show_slider=False):
    # app.logger.info(dict_ambulances)
    ids = [ambulance['id'] for ambulance in ambulances]
    dict_ambulances = init_dict_ambulances(start, end)
    # app.logger.info(dict_ambulances)
    # init_dict_ambulances()
    vehicles = {}
    df = pd.DataFrame()
    for ambulance in ambulances:
        id = ambulance['id']
        data = get(
            f'ambulance/{id}/updates/?filter={start}T15:00:00.000Z,{end}T15:00:00.000Z').json()
        data = [{'id': id, 'identifier': ambulance['identifier'], **item}
                for item in data]
        df = df.append(pd.DataFrame(data))
        vehicles[id] = {'ambulance': ambulance, 'data': data}

    df = df.apply(splitlotlan, axis=1).dropna()
    data = df
    # app.logger.info(data.shape) # data is good
    if data.empty:
        return {
            "layout": {
                "xaxis": {
                    "visible": False
                },
                "yaxis": {
                    "visible": False
                },
                "annotations": [
                    {
                        "text": "No matching data found",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {
                            "size": 28
                        }
                    }
                ]
            }
        }
    data['timestamp'] = pd.to_datetime(data.timestamp)
    data = data.sort_values(by='timestamp', ascending=True).reset_index()
    center = {'lon': data['lon'].mean(), 'lat': data['lat'].mean()}
    fig = go.Figure()
    # app.logger.info("initial fig {}".format(len(fig.data)))

    for id in dict_ambulances.keys():
        lons = []
        lats = []
        times = []
        for i, call in enumerate(dict_ambulances[id]['dict_calls']):
            if i == 0:
                lons.append(call['location']['longitude'])
                lats.append(call['location']['latitude'])
                times.append(call['timestamp'])
            elif (days_between(call['timestamp'][:19], times[-1][:19]) < 2) and (haversine((call['location']['latitude'], call['location']['longitude']), (lats[-1], lons[-1]), unit=Unit.MILES) < 100) and (i != (len(dict_ambulances)-1)):
                lons.append(call['location']['longitude'])
                lats.append(call['location']['latitude'])
                times.append(call['timestamp'])
            elif i == (len(dict_ambulances)-1):
                lons.append(call['location']['longitude'])
                lats.append(call['location']['latitude'])
                times.append(call['timestamp'])
                fig.add_trace(
                    go.Scattermapbox(
                        visible=True,
                        mode="lines",
                        lon=lons,
                        lat=lats,
                        text=times,
                        name=dict_ambulances[id]['name'],
                        legendgroup=str(id),
                        showlegend=True,
                        marker=go.scattermapbox.Marker(symbol='circle', color=dict_ambulances[id]['ambulance_color'], size=20),
                    )
                )
            else:
                fig.add_trace(
                    go.Scattermapbox(
                        visible=True,
                        mode="lines",
                        lon=lons,
                        lat=lats,
                        text=times,
                        name=dict_ambulances[id]['name'],
                        legendgroup=str(id),
                        showlegend=False,
                        marker=go.scattermapbox.Marker(symbol='circle', color=dict_ambulances[id]['ambulance_color'], size=20),
                    )
                )
                lons = []
                lats = []
                times = []
                lons.append(call['location']['longitude'])
                lats.append(call['location']['latitude'])
                times.append(call['timestamp'])
    # fig.update_layout(
    #     margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
    #     height=700,
    #     mapbox={
    #         'center': center,
    #         'style': "dark",
    #         'accesstoken': 'pk.eyJ1IjoiZ29rdWxhciIsImEiOiJja25zM3Q0Y2IwMnM2Mm90aDRpOGg3OGxoIn0.puvyGlK6lGk_LkJKFBgfDw',
    #         'zoom': 8}
    # )

    # app.logger.info(f"dictamb fig: {len(fig.data)}")

    line_size = len(fig.data)

    stepsize = 1
    if(data.shape[0] > 50):
        stepsize = data.shape[0]//50
    for step in range(0, data.shape[0], stepsize):
        a = data.loc[:step:1]
        amb_name = a['id']
        unique_ids = a.id.unique()
        # app.logger.info(unique_ids)
        # names = []
        # timestamps = []
        # app.logger.info(dict_ambulances)
        curr_trace = []
        for id in unique_ids:
            # lons.append(a.loc[a['id']==id, 'lon'].iloc[-1])
            # lats.append(a.loc[a['id']==id, 'lat'].iloc[-1])
            # texts.append(a.loc[a['id']==id, 'identifier'].iloc[-1] + " {}".format(a.loc[a['id']==id, 'timestamp'].iloc[-1]))
            # # texts.append(a.loc[a['id']==id, 'timestamp'].iloc[-1])
            # # names.append(a.loc[a['id']==id, 'identifier'].iloc[-1]) 
            # # colors.append(color_map[id])
            # colors.append(dict_ambulances[id]["ambulance_color"])
            curr_trace.append(a.loc[a['id']==id].iloc[-1])
        curr_trace_df = pd.DataFrame(curr_trace)
        curr_trace_df = curr_trace_df.sort_values(by='timestamp', ascending=False).reset_index()
        latest_time = curr_trace_df['timestamp'].iloc[0]
        lons = [curr_trace_df['lon'].iloc[0]]
        lats = [curr_trace_df['lat'].iloc[0]]
        texts = [curr_trace_df['identifier'].iloc[0] + " {}".format(curr_trace_df['timestamp'].iloc[0])]
        colors = [dict_ambulances[curr_trace_df['id'].iloc[0]]["ambulance_color"]]
        for i in range(1, len(list(curr_trace_df['timestamp']))):
            if days_between(str(curr_trace_df['timestamp'].iloc[i])[:10] + "T" + 
                            str(curr_trace_df['timestamp'].iloc[i])[11:19], 
                            str(latest_time)[:10] + "T" + str(latest_time)[11:19]) < 2:
                lons.append(curr_trace_df['lon'].iloc[i])
                lats.append(curr_trace_df['lat'].iloc[i])
                texts.append(curr_trace_df['identifier'].iloc[i] + " {}".format(curr_trace_df['timestamp'].iloc[i]))
                colors.append(dict_ambulances[curr_trace_df['id'].iloc[i]]["ambulance_color"])

        # app.logger.info(curr_trace_df['timestamp'])

        fig.add_trace(
            go.Scattermapbox(
                visible=False,
                mode="markers",
                lon=lons,
                lat=lats,
                text=texts,
                legendgroup="points",
                name="Points",
                showlegend=True,
                marker=go.scattermapbox.Marker(symbol='circle', color=colors, size=20),
            )
        )
    fig.update_layout(
        margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
        height=700,
        mapbox={
            'center': center,
            'style': "dark",
            'accesstoken': 'pk.eyJ1IjoiZ29rdWxhciIsImEiOiJja25zM3Q0Y2IwMnM2Mm90aDRpOGg3OGxoIn0.puvyGlK6lGk_LkJKFBgfDw',
            'zoom': 8}
    )
    fig.data[0].visible = True
    steps = []
    # app.logger.info(len(fig.data))
    for i in range(line_size, len(fig.data)):
        # app.logger.info(i)
        step = dict(
            method="update",
            label="{}".format(str(a.iloc[(i-line_size)*stepsize]['timestamp'])[:19]),
            args=[{"visible": [True] * line_size + [False] * (len(fig.data)-line_size)},
                {"title": "Slider switched to step: " + str(i)}],  # layout attribute
        )
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
    # app.logger.info(len(fig.data))
    # dict_ambulances = {}
    fig.update_layout(legend=dict(
        # yanchor="top",
        y=0.95,
        # xanchor="left",
        # x=0.01
    ))
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
# def generate_ambulance_card(ambulance_id):
#     single_ambulance = dict_ambulances[ambulance_id]
#     return dbc.Card([
#         dbc.CardBody(
#             [
#                 html.H4(single_ambulance["name"],
#                         className="card-title text-center"),
#                 html.Div([
#                         #  html.P(
#                         #      str(single_ambulance["dict_calls"]),
#                         #      className="card-text", style={}
#                         #  ),
#                          ], style = s_card_box)
#                 # dbc.Button(
#                 #     "Go", color="primary", className="mt-3"),
#             ]
#         ),
#     ],
#         className="m-3",
#         # color = color_sample,
#         style={"backgroundColor": single_ambulance["ambulance_color"]},
#     )
    # return dbc.Button(children=str(team_shortName),
    #                   color="primary",
    #                   className="mr-1",
    #                   id=str(team_shortName))
# app = dash.Dash(external_stylesheets=[])
#  html.Div(className = "container-sm", children = [
#     ]),
ambulances = get_ambulances()

app.layout = html.Div(children=[
    html.Div(className="container-fluid",  style=main_container, children=[
        html.H1(children='Mileage Report', className="mb-4"),
        html.H3(id='button-clicks'),
        dbc.Row(
            [
                # dcc.Input(
                #     id='input-field',
                #     type='text',
                #     className='mr-3',
                #     style={"display": "none"}
                # ),
                html.Div([
                    dcc.DatePickerRange(
                        id='my-date-picker-range',
                        min_date_allowed=date(1995, 8, 5),
                        max_date_allowed=date.today() + datetime.timedelta(days=1),
                        initial_visible_month=date.today(),
                        start_date=date(2019, 10, 1),
                        end_date=date.today()
                    ),
                    html.Div(id='output-container-date-picker-range')
                ]),
                dbc.Button("Generate", id='generate_d',
                           className="mr-2",  style=s_button),
                # dbc.Button("Generate-Static", id='generate_s',
                #            className="mr-2",  style=s_button),
                dbc.Button("Reset", id='reset', className="mr-2", style=s_button),
                dbc.Button("Export", className="mr-2 ", style=s_button),
            ],
            align="center", justify="center", className="mb-5", style={'color': main_colors['main-blue']}
        ),
        dcc.Loading(
            id="loading-2",
            children=[html.Div(
                    [
                        dcc.Graph(
                            id='map-graph',
                            className="mx-0",
                            figure=get_fig(date(2019, 10, 1), date.today())
                        ),
                    ],
                ),
            ],
            type="circle",
        ),
        # html.Div(
        #     [
        #         dcc.Graph(
        #             id='map-graph',
        #             className="mx-0",
        #             figure=get_fig(date(2019, 10, 1), date.today())
        #         ),
        #         # dcc.Loading(
        #         #     id="loading-2",
        #         #     children=[html.Div([html.Div(id="loading-output-2")])],
        #         #     type="circle",
        #         # ),
        #     ],
        #     # align="center", justify="center", style=color_green
        # ),
        # dbc.Row(
        #     [
        #         dbc.Col([
        #             html.H3(children='Testing Ambulances header'),
        #             html.Div(
        #                 ""),
        #         ],  id='output-ambulances', width=12, style=color_red),
        #         dbc.Col([
        #         ], width=0, style=color_green),
        #     ]
        # ),
    ]),
]
)
# @app.callback(
#     dash.dependencies.Output('output-ambulances', 'children'),
#     [dash.dependencies.Input('input-field', 'value')])
# def update_col(prop):
#     hrm = dbc.Col(children=[generate_ambulance_card(i)
#                             for i in dict_ambulances])
#     # hm = generate_ambulance_card(dict_ambulances["8"])
#     # hm = generate_ambulance_card(list(dict_ambulances.keys())[0])
#     return hrm

@app.callback(
    dash.dependencies.Output('map-graph', 'figure'),
    [dash.dependencies.Input('my-date-picker-range', 'start_date'),
     dash.dependencies.Input('my-date-picker-range', 'end_date'),
     dash.dependencies.Input('generate_d', 'n_clicks'),
     dash.dependencies.Input('reset', 'n_clicks')])
def update_output(start_date, end_date, generate_d, reset):
    # print(app.layout)
    ctx = dash.callback_context
    button_id = ''
    generate_n_clicks = False
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        app.logger.info(button_id)
        if button_id == "generate_d":
            generate_n_clicks = True
        elif button_id == "reset":
            return get_fig(date(2019, 10, 1), date.today())
            # return app.layout
    else:
        raise PreventUpdate
    if start_date is None or end_date is None:
        raise PreventUpdate
    if start_date is not None and end_date is not None:
        # if button_id == 'generate_s' and generate_n_clicks:
        #     ret_fig = get_fig(start_date, end_date, False)
        #     if ret_fig is not None:
        #         return ret_fig
        if button_id == 'generate_d' and generate_n_clicks:
            generate_n_clicks = False
            ret_fig = get_fig(start_date, end_date, True)
            # app.logger.info(len(ret_fig.data))
            if ret_fig is not None:
                return ret_fig
    raise PreventUpdate

@app.callback(
    dash.dependencies.Output('my-date-picker-range', 'start_date'),
    dash.dependencies.Output('my-date-picker-range', 'end_date'),
    [dash.dependencies.Input('reset', 'n_clicks')])
def update_start_date(reset):
    # print(app.layout)
    ctx = dash.callback_context
    button_id = ''
    generate_n_clicks = False
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        app.logger.info(button_id)
        if button_id == "reset":
            return date(2019, 10, 1), date.today()
    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
