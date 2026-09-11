RESE_PLOTS_DOC = """
Plot renewable electricity generation as a stacked area chart.

The function supports two plotting modes:

1. ``"hourly"``
   Plot hourly renewable electricity generation in MW using the
   ``hourly_output_mw`` results from ``run_rese_sources()``.

2. ``"cumulative"``
   Plot cumulative renewable electricity generation in GWh using the
   ``cumulative_energy_gwh_hourly`` results from
   ``run_rese_sources()``.

The function uses the renewable electricity results directly, so
``build_rese_power_df()`` is not required for plotting.

The renewable sources included in the plot can be selected using
``source_columns``. If no sources are specified, all available
renewable sources in ``rese_results`` are plotted.

Parameters
----------
rese_results : dict
    Renewable electricity results returned by
    ``run_rese_sources()``.

    The dictionary should contain a result for each renewable
    electricity source.

    Each renewable source result should contain:

    ``hourly_output_mw``
        Hourly renewable electricity generation in MW.

    ``cumulative_energy_gwh_hourly``
        Cumulative renewable electricity generation in GWh for
        each hour.

    Example structure::

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
    Renewable electricity source names to include in the plot.

    The values should correspond to keys in ``rese_results``.

    If ``None``, all available renewable electricity sources are
    plotted.

plot_type : {"hourly", "cumulative"}, optional
    Type of renewable electricity generation plot.

    ``"hourly"``
        Plot hourly renewable electricity generation in MW using
        ``hourly_output_mw``.

    ``"cumulative"``
        Plot cumulative renewable electricity generation in GWh using
        ``cumulative_energy_gwh_hourly``.

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
TypeError
    If ``rese_results`` is not a dictionary.

ValueError
    If ``rese_results`` is empty.

ValueError
    If ``plot_type`` is not ``"hourly"`` or ``"cumulative"``.

ValueError
    If a specified renewable electricity source is not found
    in ``rese_results``.

ValueError
    If the required hourly or cumulative data are not available
    for a selected renewable source.

ValueError
    If the selected hour range is invalid.

Notes
-----
For hourly plots, the function uses
``hourly_output_mw`` from each renewable source result.

The hourly values are already expressed in MW. No kW-to-MW
conversion is performed by this plotting function.

For cumulative plots, the function uses
``cumulative_energy_gwh_hourly`` from each renewable source result.

``build_rese_power_df()`` is not required for plotting. That method
is used separately to construct the RESE power streams in kW for
downstream electrolyser calculations.

Multiple renewable electricity sources are displayed as a stacked
area chart, allowing the contribution of each source to the total
renewable electricity generation to be visualised.

Examples
--------
Plot hourly renewable electricity generation::

    rese_plots(
        rese_results=rese_results,
        plot_type="hourly"
    )

Plot only wind and solar generation::

    rese_plots(
        rese_results=rese_results,
        source_columns=["wind_1", "solar_1"],
        plot_type="hourly"
    )

Plot a selected period of the year::

    rese_plots(
        rese_results=rese_results,
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