import dash
from dash import dcc, html, callback, register_page
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import sqlite3
import os

register_page(__name__, path="/")



# Get the current script directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the database file one folder up
db_path = os.path.join(current_dir, '..', '..', 'sensor_daten.sqlite')
# Verbindung zur SQlite Datei
connection = sqlite3.connect(db_path)

cursor = connection.cursor()

# Tägliche Werte für jede Wetterkategorie erhalten
query = """
SELECT
    station,
    DATE(createdAt) as date,
    AVG(Temperatur) as Temperatur,
    AVG(rel_Luftfeuchte) as Luftfeuchte,
    AVG(Luftdruck) as Luftdruck,
    AVG(Bodenfeuchte) as Bodenfeuchte,
    AVG(Bodentemperatur) as Bodentemperatur,
    MAX(Licht) as Licht,
    AVG(PM25) as PM25,
    AVG(PM10) as PM10
FROM
    WeatherData
GROUP BY
    station,
    DATE(createdAt)
ORDER BY
    station,
    DATE(createdAt);
"""

cursor.execute(query)

res = cursor.fetchall()

# Daten in Dataframe einlesen und Spaltennamen einfügen
fields = ['Station', 'Date', 'Temperatur', 'Luftfeuchte', 'Luftdruck', 'Bodenfeuchte', 'Bodentemperatur', 'Licht', 'PM25', 'PM10']

df = pd.DataFrame(res)
df.columns = fields

# Luftdruck der PoS Station auf Meereshöhe reduzieren
df['Luftdruck'] = np.where(df['Station'] == "PoS", df['Luftdruck']*1.03, df['Luftdruck'])

# 'Date' zu Datetime konvertieren
df['Date'] = pd.to_datetime(df['Date'])

# Outlier filtern
thresholds = {
    'Temperatur': (-50, 60), # Grenzwerte gewählt, da es  Messungen bis 950°C gab
    'Luftdruck': (950, 1060), # ungefähr die minimale und maximale jemals in DE gemessenen Werte
    'Bodenfeuchte': (0, 150), # Bodenfeuchte in %, bei starkem Regen können die Werte kurzfristig über 100% steigen
    'Bodentemperatur': (-50, 60), # es gab zum Teil Messungen von 360 Tsd.°C
}

filtered_df = df.apply(lambda col: col.where((col >= thresholds[col.name][0]) & (col <= thresholds[col.name][1]), np.nan) 
              if col.name in thresholds else col)


# Aggregierung auf Woche und Monat
filtered_df.set_index('Date', inplace=True)

weekly_df = filtered_df.groupby('Station').resample('W').mean().reset_index()
monthly_df = filtered_df.groupby('Station').resample('M').mean().reset_index()

# Datum der monatlichen Daten auf Format yyyy-mm konvertieren
monthly_df['Date'] = monthly_df['Date'].dt.strftime('%Y-%m')
filtered_df.reset_index(inplace=True)

# Spalten definieren, die im Dashboard angezeigt werden sollen
weather_columns = filtered_df.columns[2:]

# Layout der App definieren
layout = html.Div(children=[
    html.H1(children='Weather Data Visualization'),

    html.Div(children='''
        Select weather data to plot:
    '''),
    
    # Dropdown Menü, um zwischen den Wetterkategorien auswählen zu können
    dcc.Dropdown(
        id='weather-data-dropdown',
        options=[col for col in weather_columns],
        value='Temperatur'  # Default value
    ),

    # Graph für tägliche Daten
    dcc.Graph(
        id='daily-graph'
    ),

    # Graph für wöchentliche Daten
    dcc.Graph(
        id='weekly-graph'
    ),

    #Graph für monatliche Daten
    dcc.Graph(
        id='monthly-graph'
    )
])


@callback(
    [Output(component_id='daily-graph', component_property='figure'),
     Output(component_id='weekly-graph', component_property='figure'),
     Output(component_id='monthly-graph', component_property='figure')],
    [Input('weather-data-dropdown', 'value')]
)

def update_graphs(selected_data):
    fig1 = px.line(filtered_df, x='Date', y=selected_data, color='Station', title=f'Daily {selected_data} by Station')
    fig2 = px.line(weekly_df, x='Date', y=selected_data, color='Station', title=f"Weekly {selected_data} by Station")
    fig3 = px.line(monthly_df, x='Date', y=selected_data, color='Station', title=f"Monthly {selected_data} by Station")

    return fig1, fig2, fig3