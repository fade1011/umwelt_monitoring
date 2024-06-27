import dash
from dash import Dash, dcc, html, page_container

app = Dash(__name__, use_pages=True)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        dcc.Link(page['name']+"  |  ", href=page['path'])
            for page in dash.page_registry.values()
    ]),
    page_container
])

if __name__ == "__main__":
    app.run_server(debug=True)