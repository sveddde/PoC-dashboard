import requests
import plotly.graph_objs as go
from plotly.offline import plot

def get_smhi_data():
    url = "https://opendata-download-metobs.smhi.se/api/version/latest/parameter/1/station/98210/period/latest-months/data.json"
    r = requests.get(url)

    print("Statuskod:", r.status_code)
    print("Svarstext:", r.text[:300])  # Begränsar till 300 tecken för översikt

    # Försök parsa JSON om det verkar OK
    try:
        data = r.json()
    except Exception as e:
        print("Kunde inte tolka JSON:", e)
        return [], []

    # ... fortsätt bearbeta datan ...

def get_sgu_data():
    url = "https://resource.sgu.se/api/grundvatten/observation/20250/latest"
    r = requests.get(url)
    data = r.json()
    obs = data["observations"][0]
    return obs["datetime"][:10], obs["value"]

def generate_html(dates, rainfall, gw_date, gw_level):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=rainfall, mode='lines+markers', name='Nederbörd (mm)'))
    fig.update_layout(title='Nederbörd i Göteborg (senaste månaden)', xaxis_title='Datum', yaxis_title='mm')

    html_text = f"""
    <h2>Grundvattennivå (SGU)</h2>
    <p>Datum: {gw_date}</p>
    <p>Nivå: {gw_level} meter över havet</p>
    <hr>
    """
    html_graph = plot(fig, output_type='div', include_plotlyjs='cdn')
    full_html = f"""
    <html>
    <head><title>Vatten Dashboard</title></head>
    <body>
    <h1>Vatten Dashboard</h1>
    {html_text}
    {html_graph}
    </body>
    </html>
    """
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(full_html)

if __name__ == "__main__":
    dates, rainfall = get_smhi_data()
    gw_date, gw_level = get_sgu_data()
    generate_html(dates, rainfall, gw_date, gw_level)
