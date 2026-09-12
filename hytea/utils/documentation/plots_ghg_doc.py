PLOT_GHG_INTENSITY_SCENARIOS_DOC = """
Plot GHG intensity for multiple HyTEA scenarios.

This function creates a bar chart comparing the greenhouse gas (GHG)
intensity of multiple scenarios. The GHG results are supplied as a
dictionary, with each scenario associated with the GHG results returned
by the HyTEA model.

The function supports two GHG intensity metrics:

    - ``ghg_g_per_kWh``:
        GHG intensity in gCO2/kWh H2.

    - ``ghg_t_per_tH2``:
        GHG intensity in tCO2/tH2.

The selected GHG value is plotted as one bar for each scenario, with
the numerical value displayed above each bar. The y-axis starts at zero
to provide a consistent comparison between scenarios.

Parameters
----------
scenario_results : dict
    Dictionary containing scenario names and their GHG results.

    Each key is the scenario name and each value must contain the
    selected GHG metric.

    Example
    -------
    {
        "Scenario 1": results_1["ghg_results"],
        "Scenario 2": results_2["ghg_results"],
        "Scenario 3": results_3["ghg_results"],
    }

metric : str, optional
    GHG intensity metric to plot.

    Available options are:

        ``"ghg_g_per_kWh"``
            GHG intensity in gCO2/kWh H2.

        ``"ghg_t_per_tH2"``
            GHG intensity in tCO2/tH2.

    Default is ``"ghg_g_per_kWh"``.

figsize : tuple, optional
    Figure size passed to Matplotlib.

    Default is ``(10, 6)``.

title_fontsize : int, optional
    Font size of the plot title.

    Default is ``16``.

axis_fontsize : int, optional
    Font size of the x- and y-axis labels.

    Default is ``13``.

tick_fontsize : int, optional
    Font size of the axis tick labels.

    Default is ``11``.

value_fontsize : int, optional
    Font size of the numerical values displayed above the bars.

    Default is ``11``.

bar_width : float, optional
    Width of each bar.

    Default is ``0.7``.

save_plot : bool, optional
    Whether to save the generated figure to ``plot_file``.

    Default is ``True``.

plot_file : str, optional
    File path used when ``save_plot=True``.

    The parent directory is created automatically if it does not
    already exist.

    Default is ``"plots/results/ghg_intensity.png"``.

Raises
------
ValueError
    If ``metric`` is not one of the supported GHG metrics.

ValueError
    If ``scenario_results`` is empty.

KeyError
    If the selected GHG metric is not present in the results for
    one of the supplied scenarios.

Returns
-------
None
    The function displays the generated plot and does not return a
    value.

Notes
-----
The function expects the GHG results for each scenario to already have
been calculated by the HyTEA model. It only extracts and visualises
the selected GHG intensity metric.

The numerical value displayed above each bar is formatted to two
decimal places.

When ``save_plot=True``, the figure is saved at 300 dpi with a tight
bounding box.

Examples
--------
Plot GHG intensity in gCO2/kWh H2:

    scenario_ghg_results = {
        "Scenario 1": results_1["ghg_results"],
        "Scenario 2": results_2["ghg_results"],
        "Scenario 3": results_3["ghg_results"],
    }

    ghg_intensity_scenarios_plots(
        scenario_ghg_results,
        metric="ghg_g_per_kWh"
    )

Plot GHG intensity in tCO2/tH2:

    ghg_intensity_scenarios_plots(
        scenario_ghg_results,
        metric="ghg_t_per_tH2"
    )

Save the plot to a custom location:

    ghg_intensity_scenarios_plots(
        scenario_ghg_results,
        metric="ghg_g_per_kWh",
        save_plot=True,
        plot_file="plots/results/ghg_comparison.png"
    )
"""