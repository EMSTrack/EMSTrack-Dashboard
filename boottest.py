import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
body = html.Div([
    html.H1("Bootstrap Grid System Example")
    , dbc.Row(dbc.Col(html.Div(dbc.Alert("This is one column", color="primary"))))
    , dbc.Row([
            dbc.Col(html.Div(dbc.Alert("One of three columns", color="primary")))
            , dbc.Col(html.Div(dbc.Alert("One of three columns", color="primary")))
            , dbc.Col(html.Div(dbc.Alert("One of three columns", color="primary")))
            ])
        ])
app.layout = html.Div([body])

if __name__ == "__main__":
    app.run_server(debug = True)