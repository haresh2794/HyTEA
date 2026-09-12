PLOT_LCOH_SCENARIOS_DOC = """
Plot LCOH breakdowns for multiple hydrogen production scenarios.

The function creates a stacked bar chart showing the contribution of
different cost components to the levelized cost of hydrogen (LCOH).

Two plotting modes are available:

    1. ``breakdown="capex_opex"``
       Shows CAPEX and OPEX contributions separately for each scenario.

    2. ``breakdown="component"``
       Shows the total LCOH contribution of each individual component,
       combining its CAPEX and OPEX contributions where applicable.

Parameters
----------
scenario_results : dict
    Dictionary containing scenario names as keys and the corresponding
    ``levelized_cost_results`` dictionaries as values.

    Expected structure:

        {
            "Scenario 1": results_1["levelized_cost_results"],
            "Scenario 2": results_2["levelized_cost_results"],
            "Scenario 3": results_3["levelized_cost_results"],
        }

    For ``breakdown="capex_opex"``, each result dictionary should contain:

        ``capex_lcoh_breakdown``
            Dictionary containing CAPEX LCOH contributions by component.

        ``opex_lcoh_breakdown``
            Dictionary containing OPEX LCOH contributions by component.

        ``total_lcoh``
            Total LCOH for the scenario.

    For ``breakdown="component"``, each result dictionary should contain:

        ``component_lcoh``
            Dictionary containing total LCOH contributions by component.

        ``total_lcoh``
            Total LCOH for the scenario.

breakdown : str, optional
    Specifies how the LCOH breakdown is displayed.

    ``"capex_opex"``
        Creates one stacked bar per scenario.

        CAPEX components form the lower portion of the stack and OPEX
        components are stacked above the CAPEX contribution.

        CAPEX segments use the specified hatch, transparency, edge
        colour, and line width.

    ``"component"``
        Creates one stacked bar per scenario.

        Each segment represents the total LCOH contribution of an
        individual component.

    Default:
        ``"capex_opex"``

figsize : tuple, optional
    Figure size passed to Matplotlib.

    Default:
        ``(12, 7)``

title_fontsize : int, optional
    Font size used for the plot title.

    Default:
        ``16``

axis_fontsize : int, optional
    Font size used for the x-axis and y-axis labels.

    Default:
        ``13``

tick_fontsize : int, optional
    Font size used for axis tick labels.

    Default:
        ``11``

legend_fontsize : int, optional
    Font size used for the legend.

    Default:
        ``10``

value_fontsize : int, optional
    Font size used for the numerical total LCOH labels displayed above
    each scenario bar.

    Default:
        ``10``

bar_width : float, optional
    Width of each scenario bar.

    Default:
        ``0.4``

capex_alpha : float, optional
    Transparency applied to CAPEX segments in
    ``breakdown="capex_opex"`` mode.

    Default:
        ``0.75``

capex_hatch : str, optional
    Matplotlib hatch pattern applied directly to CAPEX segments.

    Default:
        ``"..."``

capex_edgecolor : str, optional
    Edge colour applied to CAPEX segments.

    Default:
        ``"0.65"``

capex_linewidth : float, optional
    Edge line width applied to CAPEX segments.

    Default:
        ``0.5``

save_plot : bool, optional
    Determines whether the generated figure is saved to disk.

    If ``True``, the directory containing ``plot_file`` is created if
    necessary and the figure is saved at 300 dpi.

    Default:
        ``True``

plot_file : str, optional
    Output path for the saved figure.

    Default:
        ``"plots/lcoh.png"``

Raises
------
ValueError
    If ``breakdown`` is not one of:

        ``"capex_opex"``
        ``"component"``

ValueError
    If ``scenario_results`` is empty.

Plot structure
--------------

For ``breakdown="capex_opex"``:

    - All CAPEX components appearing in the supplied scenarios are
      identified.
    - CAPEX contributions are stacked from the bottom of each bar.
    - All OPEX components are then stacked above the CAPEX contribution.
    - Components with zero contribution across every scenario are not
      plotted.
    - CAPEX segments use the configured hatch and transparency.
    - Total LCOH is displayed numerically above each scenario.

For ``breakdown="component"``:

    - All components appearing in ``component_lcoh`` are identified.
    - Each component is plotted as one segment of the stacked bar.
    - Components with zero contribution across every scenario are not
      plotted.
    - Total LCOH is displayed numerically above each scenario.

Scenario handling
-----------------

The scenario names are taken directly from the keys of
``scenario_results``.

The order of the scenarios in the input dictionary determines their
order on the x-axis.

LCOH values
-----------

The y-axis represents:

    LCOH (€/kg H₂)

The value displayed above each bar is the corresponding
``total_lcoh`` value rounded to two decimal places.

The y-axis lower limit is fixed at zero.

Output
------

The function displays the generated Matplotlib figure using
``plt.show()``.

If ``save_plot=True``, the figure is additionally saved to
``plot_file`` at 300 dpi with a tight bounding box.

The function does not return the Matplotlib figure or axes object.

Typical usage
-------------

CAPEX/OPEX breakdown:

    lcoh_scenarios_plots(
        scenario_results,
        breakdown="capex_opex"
    )

Component-wise breakdown:

    lcoh_scenarios_plots(
        scenario_results,
        breakdown="component"
    )

Custom formatting:

    lcoh_scenarios_plots(
        scenario_results,
        breakdown="capex_opex",
        figsize=(12, 7),
        title_fontsize=18,
        axis_fontsize=14,
        tick_fontsize=12,
        legend_fontsize=10,
        value_fontsize=11,
        bar_width=0.4,
        save_plot=True,
        plot_file="plots/lcoh_scenarios.png"
    )

Data requirements
-----------------

The function expects the supplied LCOH results to contain the relevant
breakdown dictionaries.

For CAPEX/OPEX mode:

    result["capex_lcoh_breakdown"]
    result["opex_lcoh_breakdown"]
    result["total_lcoh"]

For component mode:

    result["component_lcoh"]
    result["total_lcoh"]

Missing individual components are treated as having a contribution of
zero for that scenario.

Components that have zero contribution in every scenario are omitted
from the plot.

Purpose within HyTEA
--------------------

This function is a visualisation utility for comparing the levelized
cost of hydrogen across multiple HyTEA scenarios.

It is intended to show both:

    - how total LCOH differs between scenarios, and
    - which CAPEX, OPEX, or system components are responsible for those
      differences.

The function operates on already-calculated LCOH results and does not
perform the underlying techno-economic calculations itself.
"""