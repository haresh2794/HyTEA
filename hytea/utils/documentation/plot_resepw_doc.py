RESE_PLOTS_DOC = """
Plot renewable electricity generation as a stacked area chart.

The function supports two plotting modes:

1. ``"hourly"``
   Plot hourly renewable electricity generation in MW using a
   pandas DataFrame.

2. ``"cumulative"``
   Plot cumulative renewable electricity generation in GWh using
   the results returned by ``run_rese_sources()``.

The renewable sources included in the plot can be selected using
``source_columns``. If no sources are specified, all available
renewable sources are plotted.

Parameters
----------
rese_df : pandas.DataFrame, optional
    Hourly renewable electricity generation data.

    Required when ``plot_type="hourly"``.

    Each renewable electricity source should be represented by a
    column in the DataFrame.

    Example::

        rese_df = pd.DataFrame({
            "wind": wind_output,
            "solar": solar_output
        })

rese_results : dict, optional
    Renewable electricity results returned by
    ``run_rese_sources()``.

    Required when ``plot_type="cumulative"``.

    The dictionary should contain a result for each renewable
    electricity source, including the hourly cumulative energy
    generation.

    Expected structure::

        {
            "wind_1": {
                "hourly_output_mw": ...,
                "cumulative_energy_gwh_total": ...,
                "cumulative_energy_gwh_hourly": ...
            },

            "solar_1": {
                "hourly_output_mw": ...,
                "cumulative_energy_gwh_total": ...,
                "cumulative_energy_gwh_hourly": ...
            }
        }

source_columns : list, optional
    Renewable electricity sources to include in the plot.

    For ``plot_type="hourly"``, the values should correspond to
    column names in ``rese_df``.

    For ``plot_type="cumulative"``, the values should correspond
    to keys in ``rese_results``.

    If ``None``, all available renewable electricity sources are
    plotted.

plot_type : {"hourly", "cumulative"}, optional
    Type of renewable electricity generation plot.

    ``"hourly"``
        Plot hourly renewable electricity generation in MW.

    ``"cumulative"``
        Plot cumulative renewable electricity generation in GWh.

    Default is ``"hourly"``.

start_hour : int, optional
    First hour to include in the plot.

    The first hour of the year is represented by ``1``.

    Default is ``1``.

end_hour : int, optional
    Last hour to include in the plot.

    If ``None``, the function plots all available hours.

plot_title : str, optional
    Title of the plot.

    If ``None``, a default title is generated based on ``plot_type``.

save_plot : bool, optional
    If ``True``, save the generated figure to ``plot_file``.

    Default is ``False``.

plot_file : str, optional
    Path where the generated figure will be saved.

    If ``None``, a default filename is selected based on
    ``plot_type``.

    Default filenames are::

        plots/rese_power_hourly.png
        plots/rese_power_cumulative.png

show_plot : bool, optional
    If ``True``, display the generated figure.

    Default is ``True``.

Returns
-------
matplotlib.figure.Figure
    The generated Matplotlib figure.

Raises
------
ValueError
    If ``plot_type`` is not ``"hourly"`` or ``"cumulative"``.

TypeError
    If ``rese_df`` is not a pandas DataFrame when using
    ``plot_type="hourly"``.

TypeError
    If ``rese_results`` is not a dictionary when using
    ``plot_type="cumulative"``.

ValueError
    If the specified renewable source columns or result keys cannot
    be found.

ValueError
    If the selected hour range is invalid.

Notes
-----
For hourly plots, the function uses the specified renewable source
columns from ``rese_df`` and plots their electricity generation in MW.

For cumulative plots, the function uses
``cumulative_energy_gwh_hourly`` from each renewable source result.

Multiple renewable electricity sources are displayed as a stacked
area chart, allowing the contribution of each source to the total
renewable electricity generation to be visualised.

Examples
--------
Plot hourly renewable electricity generation::

    rese_plots(
        rese_df=rese_df,
        plot_type="hourly"
    )

Plot only wind and solar generation::

    rese_plots(
        rese_df=rese_df,
        source_columns=["wind", "solar"],
        plot_type="hourly"
    )

Plot a selected period of the year::

    rese_plots(
        rese_df=rese_df,
        start_hour=1,
        end_hour=168,
        plot_type="hourly"
    )

Plot cumulative renewable energy generation::

    rese_plots(
        rese_results=rese_results,
        plot_type="cumulative"
    )

Save the cumulative plot without displaying it::

    rese_plots(
        rese_results=rese_results,
        plot_type="cumulative",
        save_plot=True,
        show_plot=False,
        plot_file="plots/annual_rese_generation.png"
    )
"""