# Utilities file that handles all the logic of Dashboard Application.
import plotly.express as px
import pandas as pd
import requests
import time
import datetime
import dateutil.parser
import yaml
import random
import plotly.graph_objects as go
from datetime import date
from datetime import datetime as dt
from haversine import haversine, Unit
from style import * 
import os

def get(url, params=None, extend=True):
    """
    Method for a generic HTTP GET request
    Args: 
        url: string, url for GET request
        params: json object, GET request params
        extend: json obect, GET request headers
    Returns:
        A json object containing HTTP GET response. 
    """
    global base_url, token
    # set_token()
    if extend == True:
        url = base_url + url
    headers = {'Content-Type': 'application/json',
               'Authorization': f'Token {token}'}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response

def post(url, params=None, extend=True):
    """
    Method for a generic HTTP POST request
    Args: 
        url: string, url for POST request
        params: json object, POST request params
        extend: json obect, POST request headers
    Returns:
        A json object containing HTTP POST response. 
    """
    global base_url, token
    # set_token()
    if extend == True:
        url = base_url + url
    headers = {'Content-Type': 'application/json',
               'Authorization': f'Token {token}'}
    response = requests.post(url, headers=headers, data=params, timeout=10)
    response.raise_for_status()
    return response

def set_token(new_token):
    """
    Sets the token for accessing the API of EMSTrack.
    """
    global token
    token = new_token
    # global token_timestamp
    # try:
    #     token_timestamp
    # except NameError:
    #     token_timestamp = 0
    # if token_timestamp == 0:
    #     param = {
    #         'username': cfg['username'],
    #         'password': cfg['password']
    #     }
    #     headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    #     url = cfg['authurl']
    #     res = requests.post(url, data=param)
    #     res.raise_for_status()
    #     token_timestamp = time.time()
    #     token = res.json()['token']

def splitlotlan(row):
    """
    Refactors a row of a dataframe get rid of unnecessary location informaiton.

    Args:
        row: A dataframe row that has a location with longitude and latitude.
    
    Returns:
        A new dataframe row that has longitude and latitude.
    """
    row['lon'] = row['location']['longitude']
    row['lat'] = row['location']['latitude']
    
    return row

def init_dict_ambulances(start, end, ambulances):
    """
    Generates a dictionary and a dataframe that holds data about the ambulances
    such as id, timestamp, color and location.
    
    Args:
        start: A date object indicating start date.
        end: A date object indicating end date.
        ambulances: A list of ambulances (dictionaries with many fields).
    
    Returns:
        A dictionary and a dataframe that holds data about the ambulances.
    """
    # dict_ambulance is a dict where key is the ambulance id
    dict_ambulances = {}
    # df is a list of all points
    df = pd.DataFrame()
    # iterate through ambulances and make get request
    for amb in ambulances:
        if amb["id"] not in dict_ambulances.keys():
            color_sample = generate_new_color()
            dict_ambulances[amb["id"]] = {
                "name": amb["identifier"], "dict_calls": [], "ambulance_color": color_sample}
        data = get(
            f'ambulance/{amb["id"]}/updates/?filter={start}T00:00:00.000Z,{end}T00:00:00.000Z').json()
        # populate dict_ambulances
        for d in data:  
            dict_ambulances[amb["id"]]["dict_calls"].insert(
                0, {"location": d["location"], "timestamp": d["timestamp"]})
        # populate df
        data_df = [{'id': amb["id"], 'identifier': amb['identifier'], **item}
                for item in data]
        df = df.append(pd.DataFrame(data_df))
    
    # return both 
    return dict_ambulances, df

def get_ambulances():
    """
    Method to get a list of all ambulances
    
    Returns:
        A json object containing all ambulances
    """
    global cfg
    global base_url
    # with open("config.yml", 'r') as ymlfile:
    #     cfg = yaml.safe_load(ymlfile)
    SERVER = 'UCSD'
    # cfg = cfg[SERVER]
    cfg = {
        "authurl" : os.environ["DASHBOARD_AUTHURL_" + SERVER],
        "url" : os.environ["DASHBOARD_URL_" + SERVER],
        "username" : os.environ["DASHBOARD_USERNAME_" + SERVER],
        "password" : os.environ["DASHBOARD_PASSWORD_" + SERVER],
    }
    base_url = cfg['url']
    res = get('ambulance')
    ambulances = res.json()
    return ambulances

def days_between(d1, d2):
    """
    Method to find the days between date d1 and date d2. 

    Args:
        d1: A date object
        d2: A date object
    
    Returns:
        A float, difference between d1 and d2 in days
    """
    d1 = dt.strptime(d1, "%Y-%m-%dT%H:%M:%S")
    d2 = dt.strptime(d2, "%Y-%m-%dT%H:%M:%S")
    return abs((d2 - d1).days)

def add_lines(fig, dict_ambulances):
    """
    Method to add lines to a figure. Called before add_points(fig) 
    and add_slider(fig). 

    Args:
        fig: go.Figure() object
        dict_ambulances: dictionary object
    """

    # Iterates through all of the ambulances and adds traces to figure in such a manner
    # so that route lines are roughly separated based on distance and time
    for id in dict_ambulances.keys():
        # Arrays that will append all the call information to
        lons = []
        lats = []
        times = []

        # Iterates through all the of the calls of each individual ambulance
        for i, call in enumerate(dict_ambulances[id]['dict_calls']):

            # Initial append
            if i == 0:
                lons.append(call['location']['longitude'])
                lats.append(call['location']['latitude'])
                times.append(call['timestamp'])
            
            # Appends based on if the previous call and the most recent call are less than a day apart and within the range of a 100 miles
            elif (days_between(call['timestamp'][:19], times[-1][:19]) < 2) and (haversine((call['location']['latitude'], call['location']['longitude']), (lats[-1], lons[-1]), unit=Unit.MILES) < 100) and (i != (len(dict_ambulances)-1)):
                lons.append(call['location']['longitude'])
                lats.append(call['location']['latitude'])
                times.append(call['timestamp'])
            
            # Final append
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
                        hoverinfo='skip',
                        marker=go.scattermapbox.Marker(symbol='circle', color=dict_ambulances[id]['ambulance_color'], size=20),
                    )
                )
            
            # Resets the arrays and adds the current set of points as a trace into the figure
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
                        hoverinfo='skip',
                        marker=go.scattermapbox.Marker(symbol='circle', color=dict_ambulances[id]['ambulance_color'], size=20),
                    )
                )
                lons = []
                lats = []
                times = []
                lons.append(call['location']['longitude'])
                lats.append(call['location']['latitude'])
                times.append(call['timestamp'])

    return

def add_points(fig, dict_ambulances, data, center):
    """
    Method to add points to a figure that already has lines. 
    Called after add_lines(fig) function. Calls add_slider(fig) 
    function within this function at the end.  

    Args:
        fig: go.Figure() object
        dict_ambulances: dictionary object
        data: pandas dataframe intially holding all lines
        center: dictionary with 'lon' and 'lat' values, 
            coordinates of center of map
    """
    # number of lines in the figure
    line_size = len(fig.data)
    # by default (number of points < 50), step size 1 
    stepsize = 1
    num_of_steps = 50
    # if number of points > 50, divide data into 50 steps 
    if(data.shape[0] > num_of_steps):
        stepsize = data.shape[0]//num_of_steps
    # iterate through all points using stepsize
    for step in range(0, data.shape[0], stepsize):
        # assign a to all data up to current step
        a = data.loc[:step:1]
        # get all ambulance names
        amb_name = a['id']
        # keep unique ambulance names
        unique_ids = a.id.unique()
        curr_trace = []
        # get the latest point for each ambulance
        for id in unique_ids:
            curr_trace.append(a.loc[a['id']==id].iloc[-1])
        curr_trace_df = pd.DataFrame(curr_trace)
        # curr_trace_df has latest point for each ambulance, sort them 
        curr_trace_df = curr_trace_df.sort_values(by='timestamp', ascending=False).reset_index()
        # the latest time is the first point
        latest_time = curr_trace_df['timestamp'].iloc[0]
        # initialize lons, lats, texts, colors for the map
        # they contain the latest point first
        lons = [curr_trace_df['lon'].iloc[0]]
        lats = [curr_trace_df['lat'].iloc[0]]
        texts = [curr_trace_df['identifier'].iloc[0] + " {}".format(curr_trace_df['timestamp'].iloc[0])]
        colors = [dict_ambulances[curr_trace_df['id'].iloc[0]]["ambulance_color"]]
        # add the rest of the points, one per remaining ambulance
        # there is some extra logic using days_between to exclude all points < 2 days 
        # from the latest point
        for i in range(1, len(list(curr_trace_df['timestamp']))):
            if days_between(str(curr_trace_df['timestamp'].iloc[i])[:10] + "T" + 
                            str(curr_trace_df['timestamp'].iloc[i])[11:19], 
                            str(latest_time)[:10] + "T" + str(latest_time)[11:19]) < 2:
                lons.append(curr_trace_df['lon'].iloc[i])
                lats.append(curr_trace_df['lat'].iloc[i])
                texts.append(curr_trace_df['identifier'].iloc[i] + " {}".format(curr_trace_df['timestamp'].iloc[i]))
                colors.append(dict_ambulances[curr_trace_df['id'].iloc[i]]["ambulance_color"])
        
        # adds the trace for all the points gotten based on the logic above
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

    # center the map
    fig.update_layout(
        margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
        height=700,
        mapbox={
            'center': center,
            'style': "dark",
            'accesstoken': 'pk.eyJ1IjoiZ29rdWxhciIsImEiOiJja25zM3Q0Y2IwMnM2Mm90aDRpOGg3OGxoIn0.puvyGlK6lGk_LkJKFBgfDw',
            'zoom': 8}
    )

    # add slider
    add_slider(fig, a, stepsize, line_size)
    return

def add_slider(fig, a, stepsize, line_size):
    """
    Method to add slider to a figure that already has the lines and points. 
    Called after add_lines(fig) and add_points(fig) functions respectively. 

    Args:
        fig: go.Figure() object
        a: pandas dataframe holding all lines and points
        stepsize: int to determine slider step size
        line_size: int total number of lines in graph, skipped over in slider
    """
    # set all the lines to visible intially
    fig.data[line_size].visible = True
    steps = []
    # assign visibility for each step in the slider
    # this will assign the lines in the beginning to visible and the points up to
    # the current step to visible, all later points are not visible
    for i in range(line_size, len(fig.data)):
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
    # add slider to fig
    fig.update_layout(
        sliders=sliders
    )
    # move the legend down a bit so it doesn't get blocked
    fig.update_layout(legend=dict(
        y=0.95,
    ))

    return


def get_fig(start, end):
    """
    Main method to create the map figure with lines, points, and slider

    Args:
        start: A date object indicating start date
        end: A date object indicating end date
    
    Returns:
        A plotly.graph_objects.Figure() object containing lines, points, and slider
    """
    # get ambulances, extract their ids and get their data within start and end date range
    # store the data into dict_ambulances(organized by ambulance) and df(sequential).
    ambulances = get_ambulances()
    ids = [ambulance['id'] for ambulance in ambulances]
    dict_ambulances, df = init_dict_ambulances(start, end, ambulances)
    # split longitude and latitude
    df = df.apply(splitlotlan, axis=1).dropna() 
    data = df 
    # return error message if no data in date range
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
    # sort the data by timestamp from earliest to latest
    data['timestamp'] = pd.to_datetime(data.timestamp)
    data = data.sort_values(by='timestamp', ascending=True).reset_index()
    # get center coordinates to use in map 
    center = {'lon': data['lon'].mean(), 'lat': data['lat'].mean()}
    
    # declare figure, add lines, add points
    # slider is added inside add_points()
    fig = go.Figure()
    add_lines(fig, dict_ambulances)
    add_points(fig, dict_ambulances, data, center)

    return fig

def generate_new_color():
    """
    Creates a new random color.
    
    Returns:
        A string with random red, green and blue values.
    """
    def rand(): return random.randint(100, 255)
    return '#%02X%02X%02X' % (rand(), rand(), rand())