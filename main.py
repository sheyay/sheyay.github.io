import json
from datetime import datetime
import numpy as np
import pandas as pd
import plotly as px
import plotly.graph_objects as go
import sqlalchemy
from flask import Flask, render_template
from plotly.subplots import make_subplots
import plotly.io as pio

pio.templates

host = '/cloudsql/turnkey-crowbar-351921:us-central1:instance2'
db = 'mccoy_energy'
user = 'root'
pasw = 'instance2'
query_string = dict({'unix_socket': host})
engine = sqlalchemy.create_engine(
    sqlalchemy.engine.url.URL(
        drivername='mysql+pymysql',
        username=user,
        password=pasw,
        database=db,
        query=query_string,
    ),
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800
)
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def tempchart():
    elec_data = pd.read_sql('SELECT * FROM dashboardnew_view WHERE type_key=2', engine)

    chw_data = pd.read_sql('SELECT * FROM dashboardnew_view WHERE type_key=1', engine)

    steam_data = pd.read_sql('SELECT * FROM dashboardnew_view WHERE type_key=3', engine)

    print(elec_data)
    print(chw_data)
    print(steam_data)

    chw_data['energy_consumption'] = chw_data['energy_consumption'].multiply(other=0.000293)
    elec_data['energy_consumption'] = elec_data['energy_consumption'].multiply(other=0.000293)
    steam_data['energy_consumption'] = steam_data['energy_consumption'].multiply(other=0.000293)

    data = {'Consumption': 'kW', 'STEAM': steam_data['energy_consumption'].sum(),
            'ELEC': elec_data['energy_consumption'].sum(),
            'CHW': chw_data['energy_consumption'].sum()}

    fig = make_subplots(
        rows=4, cols=2,
        specs=[
            [{"colspan": 2}, None],
            [{"secondary_y": True, "colspan": 2}, None],
            [{"colspan": 2}, None],
            [{"colspan": 2}, None],
        ],
        subplot_titles=("Consumption/Day by system",
                        "Consumption and Temperature",
                        "Maximum, Average and Minimum Temperatures",
                        "Weekends and Working Days"))

    fig.add_trace(go.Bar(x=chw_data['Date'], y=chw_data['energy_consumption'], legendgroup=1, name="Cooling"), row=1,
                  col=1)
    fig.add_trace(go.Bar(x=elec_data['Date'], y=elec_data['energy_consumption'], legendgroup=1, name="Electrical"),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=steam_data['Date'], y=steam_data['energy_consumption'], legendgroup=1, name="Heating"),
                  row=1, col=1)

    fig.add_trace(go.Bar(x=elec_data['Date'], y=elec_data['energy_consumption'], name="Electricity", showlegend=True,
                         legendgroup=2),
                  row=2, col=1, secondary_y=False)
    fig.add_trace(
        go.Scatter(x=elec_data['Date'], y=elec_data["TempAvg"], name="Avg Temp", showlegend=True, legendgroup=2),
        row=2, col=1, secondary_y=True)

    fig.add_trace(go.Scatter(x=elec_data['Date'], y=elec_data['Temp Max'], name='Maximum',
                             line=dict(width=1.5, color='#110b87'),
                             showlegend=True, legendgroup=3),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=elec_data['Date'], y=elec_data['TempAvg'], name='Average'
                             , line=dict(width=1.5, color='#5a719c'),
                             showlegend=True, legendgroup=3),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=elec_data['Date'], y=elec_data['TempMin'], name='Minimum',
                             line=dict(width=2, color='#cc503e'), showlegend=True, legendgroup=3),
                  row=3, col=1)

    # Plotting Weekdays and Weekends

    # define the y-axis limits
    ymin, ymax = elec_data['energy_consumption'].min() - 5, elec_data['energy_consumption'].max() + 5

    # create an auxiliary time series for highlighting the weekends, equal
    # to "ymax" on Saturday and Sunday, and to "ymin" on the other days
    elec_data['Date'] = pd.to_datetime(elec_data.Date)
    elec_data['weekend'] = np.where(elec_data['Date'].dt.day_name().isin(['Sunday', 'Saturday']), ymax, ymin)

    # Plotting Weekends (Saturday, Sunday)
    fig.add_trace(
        go.Scatter(
            x=elec_data['Date'],
            y=elec_data['weekend'],
            fill='tonext',
            fillcolor='#d9d9d9',
            mode='lines',
            line=dict(width=0, shape='hvh'),
            showlegend=True,
            hoverinfo=None, name='Weekends', legendgroup=4), row=4, col=1)

    # plot the time series as a line chart
    fig.add_trace(
        go.Scatter(
            x=elec_data['Date'],
            y=elec_data['energy_consumption'],
            mode='lines+markers',
            marker=dict(size=1, color='#cc503e'),
            line=dict(width=1.5, color='#cc503e'),
            showlegend=True, name='Electricity', legendgroup=4), row=4, col=1)

    # Update xaxis properties
    fig.update_xaxes(title_text="Date", tickangle=45, tickfont=dict(family='Rockwell', size=10), row=1,
                     col=1, rangeselector=dict(
            buttons=list([
                dict(count=1, label="1 Month", step="month", stepmode="backward"),
                dict(count=6, label="6 months", step="month", stepmode="backward"),
                dict(count=1, label="1 Year", step="year", stepmode="backward"),
                dict(label="All", step="all")
            ])
        ))

    fig.update_xaxes(title_text="Date", tickangle=45, tickfont=dict(family='Rockwell', size=10), row=2,
                     col=1, rangeselector=dict(
            buttons=list([
                dict(count=1, label="1 Month", step="month", stepmode="backward"),
                dict(count=6, label="6 months", step="month", stepmode="backward"),
                dict(count=1, label="1 Year", step="year", stepmode="backward"),
                dict(label="All", step="all")
            ])
        ))

    fig.update_xaxes(title_text="Date", tickangle=45, tickfont=dict(family='Rockwell', size=10), row=3,
                     col=1, rangeselector=dict(
            buttons=list([
                dict(count=1, label="1 Month", step="month", stepmode="backward"),
                dict(count=6, label="6 months", step="month", stepmode="backward"),
                dict(count=1, label="1 Year", step="year", stepmode="backward"),
                dict(label="All", step="all")
            ])
        ))

    fig.update_xaxes(title_text="Date", tickfont=dict(family='Rockwell', size=12), row=4,
                     col=1, rangeselector=dict(
            buttons=list([
                dict(count=1, label="1 Month", step="month", stepmode="backward"),
                dict(count=6, label="6 months", step="month", stepmode="backward"),
                dict(count=1, label="1 Year", step="year", stepmode="backward"),
                dict(label="All", step="all")
            ])
        ))

    # Update yaxis properties
    fig.update_yaxes(title_text="Consumption (kW's)", row=1, col=1)
    fig.update_yaxes(title_text="Electricity Consumption (kW's)", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Temperature (FAHRENHEIT)", row=2, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Temperature (FAHRENHEIT)", row=3, col=1)
    fig.update_yaxes(title_text="Electricity Consumption (kW's)", row=4, col=1)

    # paper_bgcolor='rgba(0, 0, 0,0)', plot_bgcolor='rgba(0, 0, 0,0)'

    fig.update_layout(height=1700, width=930, legend_tracegroupgap=390,
                      barmode='relative')

    graphJSON = json.dumps(fig, cls=px.utils.PlotlyJSONEncoder)

    return render_template('dashboard.html', graphJSON=graphJSON, data=data)


@app.route('/about_us')
def about_us():
    return render_template('about_us.html')


@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')


@app.route('/data')
def data():
    return render_template('data.html')


@app.route('/predictions')
def predictions():
    return render_template('predictions.html')


@app.route('/data_warehousing')
def data_warehousing():
    return render_template('data_warehousing.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
