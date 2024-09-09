# Native imports
import os.path

# Third-party imports
import gsw
import numpy as np
import pandas as pd
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
from plotly import subplots

# Sea-Bird imports
import sbs.process.cal_coefficients as cal
import sbs.process.conversion as conv
import sbs.process.processing as proc
import sbs.process.instrument_data as id
import sbs.visualize.visualization as viz

#print("renderers", pio.renderers)

def plot(
    data, title, x_names, x_bounds={0: [17, 24], 1: [-1, 6], 2: [-1, 6], 3: [-1, 6]}
):
    config = viz.ChartConfig(
        title=title,
        x_names=x_names,
        y_names=["press"],
        z_names=[],
        chart_type="overlay", # overlay or subplots
        bounds={
            "x": x_bounds,
            # 'y': { 0: [29, 32], 1: [29, 32], 2: [29, 32], 3: [29, 32] }
        },
        plot_loop_edit_flags=False,
        lift_pen_over_bad_data=True,
    )

    fig = viz.plot_xy_chart(data, config)
    fig["layout"]["yaxis"]["autorange"] = "reversed"
    fig.update_layout(height=800)
    fig.show()


def plot_for_cnv_file(cnv_file: str):
    cnv_data = id.cnv_to_instrument_data(cnv_file)

    #data = pd.DataFrame(data=cnv_data, columns=["temp", "press", "cond", "flag"])
    #cnv_data.measurements['sal00'].values

    measurements = cnv_data.measurements
    # However, MeasurementSeries already has: description, label, units, values: np.ndarray
    vars = [(x, viz.interpret_sbs_variable(x)) for x in measurements]

    #plot(data=cnv_data, title="Data Conversion", x_names=["temp", "cond"], x_bounds={})

    fig = go.Figure()
    fig.layout.title = "Hello"


    # MeasurementSeries(label='tv290C', description='Temperature', units='ITS-90, deg C', start_time=datetime.datetime(2013, 2, 15, 8, 2, 22), values=array([29.5942, 29.6049, 29.6075, 29.6117, 29.6141, 29.6124, 29.6089,
    xmetric = "tv290C"
    ymetric = "depSM"

    # xaxis=<name of axis?>
    # TODO maybe share axis based on units? see if any of metrics have same units or description, or interpret_sbs_variable
    s = go.Scatter(x=measurements[xmetric].values, y=measurements[ymetric].values, name=xmetric, xaxis="x1")
    fig.add_trace(s)

    xmetric = "c0S/m"
    s = go.Scatter(x=measurements[xmetric].values, y=measurements[ymetric].values, name=xmetric, xaxis="x2")
    fig.add_trace(s)

    #MeasurementSeries(label='c0S/m', description='Conductivity', units='S/m', start_time=datetime.datetime(2013, 2, 15, 8, 2, 22), values=array([5.656429, 5.66036 , 5.661478, 5.66785 , 5.673942, 5.676148,
    #MeasurementSeries(label='sal00', description='Salinity, Practical', units='PSU', start_time=datetime.datetime(2013, 2, 15, 8, 2, 22), values=array([34.0755, 34.0943, 34.0997, 34.1397, 34.1791, 34.195 , 34.212 ,


    # TODO autorange reverse

    # ref apply_overlay_config
    fig.update_layout(
        xaxis=dict(
            title="Foo",
        ),
        xaxis2=dict(
            title="Two",
            overlaying="x",
            position=0.1
        )
        )

    return fig


if __name__ == '__main__':
    cnv_file = r'c:\Users\awhite\data\CTD\processed\19plus2_4525_20120905_test\done\19plus2_4525_20120905_testCFACLWDB.cnv'
    fig = plot_for_cnv_file(cnv_file)
    fig.show()
