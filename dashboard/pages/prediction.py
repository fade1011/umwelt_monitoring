import dash
import plotly.express as px
from dash import dcc, html, register_page, callback
from dash.dependencies import Input, Output
from datetime import datetime
import pandas as pd

register_page(__name__)


prediction = pd.read_parquet('predictions.parquet')

prediction['Datum'] = pd.to_datetime(prediction['createdAt'])

weather_columns = prediction.drop(columns=['Datum', 'createdAt']).columns

cutoff = prediction['Datum'].iloc[-24]


layout = html.Div(children=[
    html.H1(children='Weather Data Visualization'),

    html.Div(children='''
        Select weather data to plot:
    '''),
    
    dcc.Dropdown(
        id='weather-data-dropdown',
        options=[col for col in weather_columns],
        value='Temperatur'  # Default value
    ),

    # Graph für tägliche Daten
    dcc.Graph(
        id='prediction'
    )
])

@callback(
    [Output(component_id='prediction', component_property='figure')],
    [Input('weather-data-dropdown', 'value')]
)

def update_graph(selected_data):
    fig = px.line(prediction, x='Datum', y=selected_data, title=f"Prediction for {selected_data}")
    fig.add_vline(x=cutoff, line_width=2, line_dash='dash', line_color='red')
    fig.add_vrect(x0=cutoff, x1=prediction['Datum'].iloc[-1] ,line_width=0, fillcolor="grey", opacity=0.2)
    return [fig]

