# -*- coding: utf-8 -*-
# Run this app with `python index.py` and visit http://127.0.0.1:8050/ in your web browser.
# Main file that handles the layout and callbacks of the Dashboard application.
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.express as px
import datetime
from datetime import date
from dash.exceptions import PreventUpdate
from style import * 
from utils import *

from flask import Flask

# Global to keep track of when the Generate button was last pushed
generate_n_clicks = False

# Adds Bootstrap styling to application
external_stylesheets = [dbc.themes.BOOTSTRAP]

# server = Flask(__name__)
# app = dash.Dash(server=server, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__, 
                # server=server, 
                external_stylesheets=external_stylesheets,
                url_base_pathname="/dashboard/")

# Defines the actual layout of HTML elements on the application
app.layout = html.Div(children=[
    html.Div(className="container-fluid",  style=main_container, children=[
        html.H1(children='Dashboard', className="mb-4"),
        html.H3(id='button-clicks'),

        # Adds all the input fields for the application
        dbc.Row(
            [
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
                dbc.Button("Reset", id='reset', className="mr-2", style=s_button),
            ],
            align="center", justify="center", className="mb-5", style={'color': main_colors['main-blue']}
        ),

        # Adds a loading wrapper for loading animation
        html.Div(className="loader-wrapper",children=[
            dcc.Loading(
                parent_className='loading_wrapper',
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
        ])
    ]),
]
)

@app.callback(
    dash.dependencies.Output('map-graph', 'figure'),
    [dash.dependencies.Input('my-date-picker-range', 'start_date'),
     dash.dependencies.Input('my-date-picker-range', 'end_date'),
     dash.dependencies.Input('generate_d', 'n_clicks'),
     dash.dependencies.Input('reset', 'n_clicks')])
def update_output(start_date, end_date, generate_d, reset):
    """
    Handles the callback for when the User inputs a new start and end date
    and clicks generate or the reset button is clicked.

    Args:
        start_date: The date used to determine the beginning of the range.
        end_date: The date used to determine the end of the range.
        generate_d: An integer that keeps track of how many times the button
            was clicked.
        reset: An integer that keeps track of how many times the button
            was clicked.
    
    Returns:
        A figure that will ultimately update the main map graph on the page.
        
    """
    ctx = dash.callback_context
    button_id = ''
    generate_n_clicks = False

    # Checks the dash callback context to see if a button was clicked
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # Checks if the generate button was clicked
        if button_id == "generate_d":
            generate_n_clicks = True
        
        # Checks if the reset button was clicked
        elif button_id == "reset":
            return get_fig(date(2019, 10, 1), date.today())
    
    # Ends the callback in case a button was not clicked
    else:
        raise PreventUpdate

    # Ends the callback in case the dates were not inputted
    if start_date is None or end_date is None:
        raise PreventUpdate
    
    # Checks if start and end dates are not empty
    if start_date is not None and end_date is not None:

        # Checks if generate button was clicked
        if button_id == 'generate_d' and generate_n_clicks:
            generate_n_clicks = False
            ret_fig = get_fig(start_date, end_date)

            # Checks if figure is not empty
            if ret_fig is not None:
                return ret_fig

    # Ends callback in any other case not already listed above
    raise PreventUpdate

@app.callback(
    dash.dependencies.Output('my-date-picker-range', 'start_date'),
    dash.dependencies.Output('my-date-picker-range', 'end_date'),
    [dash.dependencies.Input('reset', 'n_clicks')])
def update_start_date(reset):
    """
    Handles the callback for when the reset button is pushed and the start
    date field needs to be updated.

    Args:
        reset: An integer that keeps track of how many times the button
            was clicked.
    
    Returns:
        A date object that will update the value of the start date field.
    """
    ctx = dash.callback_context
    button_id = ''
    generate_n_clicks = False

    # Checks the dash callback context to see if a button was clicked
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # Checks if reset button was clicked
        if button_id == "reset":
            return date(2019, 10, 1), date.today()
    
    # Ends callback in case a button was not clicked
    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.run_server()
