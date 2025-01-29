import os.path

import plotly.graph_objects as go

# Sea-Bird imports
from seabirdscientific.instrument_data import cnv_to_instrument_data, InstrumentData
import seabirdscientific.visualization as viz

#print("renderers", pio.renderers)

# SBE example plot, though we're not using their viz.ChartConfig system.
def sbs_plot(
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

# TODO support mode with fewer axis sharing metrics of similar range.
def plot_for_cnv_file(cnv_file: str | None = None,
                      instr_data: InstrumentData | None = None,
                      axis_offset: float = 0.05,
                      include: set[str] | None = None,
                      exclude: set[str] = {'flag', 'nbin'}
                      ) -> go.Figure:

    if not exclude:
        exclude = set()

    # always exclude pressure metrics from x axis
    exclude.add('depSM')
    exclude.add('prdM')

    if instr_data is None:
        assert cnv_file is not None
        instr_data = cnv_to_instrument_data(cnv_file)

    # MeasurementSeries(label='tv290C', description='Temperature', units='ITS-90, deg C', start_time=datetime.datetime(2013, 2, 15, 8, 2, 22), values=array([29.5942, ...])
    measurements = instr_data.measurements
    # However, MeasurementSeries already has: description, label, units, values: np.ndarray
    # vars = [(x, viz.interpret_sbs_variable(x)) for x in measurements]

    if 'depSM' in measurements:
        ymetric = 'depSM'
    else:
        ymetric = 'prdM'

    y_values = measurements[ymetric].values
    y_var = viz.interpret_sbs_variable(ymetric)
    #print (y_var, measurements[ymetric])

    fig = go.Figure()
    # fig.layout.title = "Hello"

    layout=dict(
        # just need room for top-right buttons
        margin_t=32,
        margin_b=0,
        hovermode='y unified',
        yaxis=dict(
            title=y_var['units'],
            autorange="reversed",
            #domain=[0.5, 1.0]
        )
    )

    if include:
        selected_measurements = [m for m in measurements if m in include]
    else:
        selected_measurements = [m for m in measurements if m not in exclude]

    trace_count = 0
    for index, id in enumerate(selected_measurements):
        m = measurements[id]
        axis_num = index + 1

        var = viz.interpret_sbs_variable(id)
        #print(axis_num, id, var, m)

        title = var['units']
        if title == '':
            title = m.description
            units = m.units
            if units:
                title = f"{title}, {units}"

        if axis_num == 1:
            layout['xaxis'] = dict(
                title=title,
                showgrid=False,
                ticks="inside",
                ticklen=6
            )
        else:
            layout[f'xaxis{axis_num}'] = dict(
                title=title,
                showgrid=False,
                overlaying='x',
                anchor='free',
                # Unfortunately, autoshift and shift are only available on yaxis
                # https://plotly.com/python/multiple-axes/#automatically-shifting-axes
                # clamp to 1, otherwise error
                position = min(axis_offset * axis_num, 1.0),
                ticks='inside',
                ticklen=6,
                minor_ticks="inside"
                #tickwidth=1
            )

        s = go.Scatter(x=m.values, y=y_values, name=id, xaxis=f"x{axis_num}")
        fig.add_trace(s)
        trace_count += 1

    # make space for the xaxis
    layout['yaxis']['domain'] = [axis_offset * (trace_count + 1), 1.0]

    fig.update_layout(layout)

    return fig


# run this file to do plot development
if __name__ == '__main__':
    cnv_file = r'c:\Users\awhite\data\CTD\processed\19plus2_4525_20120905_test\done\19plus2_4525_20120905_testCFACLWDB.cnv'
    fig = plot_for_cnv_file(cnv_file)
    fig.show()
