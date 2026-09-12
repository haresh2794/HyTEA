import matplotlib.pyplot as plt
import numpy as np
import os
from .documentation.plots_lcoh_doc import PLOT_LCOH_SCENARIOS_DOC


def lcoh_scenarios_plots(
    scenario_results,
    breakdown="capex_opex",
    figsize=(12, 7),
    title_fontsize=16,
    axis_fontsize=13,
    tick_fontsize=11,
    legend_fontsize=10,
    value_fontsize=10,
    bar_width=0.4,
    capex_alpha=0.75,
    capex_hatch="...",
    capex_edgecolor="0.65",
    capex_linewidth=0.5,
    save_plot=True,
    plot_file="plots/lcoh.png"
):
    """
    Plot LCOH breakdown for multiple scenarios.

    Parameters
    ----------
    scenario_results : dict
        Dictionary containing scenario names and their
        'levelized_cost_results'.

        Example:
        {
            "Scenario 1": results_1["levelized_cost_results"],
            "Scenario 2": results_2["levelized_cost_results"],
            "Scenario 3": results_3["levelized_cost_results"],
        }

    breakdown : str
        "capex_opex"
            One stacked bar per scenario.
            CAPEX components are at the bottom.
            OPEX components are above CAPEX.
            CAPEX uses a light dotted hatch.

        "component"
            One stacked bar per scenario.
            Each component represents its total LCOH
            contribution (CAPEX + OPEX).

    figsize : tuple
        Figure size.

    title_fontsize : int
        Title font size.

    axis_fontsize : int
        Axis label font size.

    tick_fontsize : int
        Tick label font size.

    legend_fontsize : int
        Legend font size.

    value_fontsize : int
        Font size for total LCOH values.

    bar_width : float
        Width of the bars.

    capex_alpha : float
        Transparency of CAPEX segments.

    capex_hatch : str
        Hatch pattern for CAPEX.

    capex_edgecolor : str
        Edge colour of CAPEX segments.

    capex_linewidth : float
        Edge line width of CAPEX segments.
    """

    # ==========================================================
    # VALIDATION
    # ==========================================================

    if breakdown not in ["capex_opex", "component"]:
        raise ValueError(
            "breakdown must be either "
            "'capex_opex' or 'component'"
        )

    if not scenario_results:
        raise ValueError(
            "scenario_results cannot be empty."
        )

    # ==========================================================
    # SCENARIOS
    # ==========================================================

    scenario_names = list(scenario_results.keys())
    n_scenarios = len(scenario_names)

    x = np.arange(n_scenarios)

    # ==========================================================
    # FIGURE
    # ==========================================================

    fig, ax = plt.subplots(figsize=figsize)

    # ==========================================================
    # OPTION 1
    # CAPEX + OPEX BREAKDOWN
    # ==========================================================

    if breakdown == "capex_opex":

        # ------------------------------------------------------
        # Find all components
        # ------------------------------------------------------

        components = set()

        for result in scenario_results.values():

            components.update(
                result.get(
                    "capex_lcoh_breakdown",
                    {}
                ).keys()
            )

            components.update(
                result.get(
                    "opex_lcoh_breakdown",
                    {}
                ).keys()
            )

        components = sorted(components)

        # ------------------------------------------------------
        # CAPEX
        # ------------------------------------------------------

        capex_bottom = np.zeros(n_scenarios)

        for component in components:

            values = np.array([
                result.get(
                    "capex_lcoh_breakdown",
                    {}
                ).get(component, 0.0)
                for result in scenario_results.values()
            ], dtype=float)

            # Skip components that are zero in every scenario
            if not np.any(values != 0):
                continue

            # CAPEX segment
            #
            # The hatch is applied directly to this bar.
            # Therefore it exactly matches the CAPEX segment.
            ax.bar(
                x,
                values,
                bottom=capex_bottom,
                width=bar_width,
                label=f"CAPEX – {component}",
                alpha=capex_alpha,
                hatch=capex_hatch,
                edgecolor=capex_edgecolor,
                linewidth=capex_linewidth
            )

            # Move the bottom of the stack upwards
            capex_bottom += values

        # ------------------------------------------------------
        # OPEX
        # ------------------------------------------------------

        opex_bottom = capex_bottom.copy()

        for component in components:

            values = np.array([
                result.get(
                    "opex_lcoh_breakdown",
                    {}
                ).get(component, 0.0)
                for result in scenario_results.values()
            ], dtype=float)

            # Skip components that are zero in every scenario
            if not np.any(values != 0):
                continue

            # OPEX segment
            ax.bar(
                x,
                values,
                bottom=opex_bottom,
                width=bar_width,
                label=f"OPEX – {component}"
            )

            # Move the bottom of the stack upwards
            opex_bottom += values

        # ------------------------------------------------------
        # Total LCOH labels
        # ------------------------------------------------------

        for i, result in enumerate(
            scenario_results.values()
        ):

            total_lcoh = float(
                result.get("total_lcoh", 0.0)
            )

            ax.text(
                i,
                total_lcoh,
                f"{total_lcoh:.2f}",
                ha="center",
                va="bottom",
                fontsize=value_fontsize
            )

        # ------------------------------------------------------
        # Title
        # ------------------------------------------------------

        ax.set_title(
            "LCOH CAPEX and OPEX Breakdown",
            fontsize=title_fontsize
        )

    # ==========================================================
    # OPTION 2
    # COMPONENT-WISE TOTAL LCOH
    # ==========================================================

    elif breakdown == "component":

        # ------------------------------------------------------
        # Find all components
        # ------------------------------------------------------

        components = set()

        for result in scenario_results.values():

            components.update(
                result.get(
                    "component_lcoh",
                    {}
                ).keys()
            )

        components = sorted(components)

        # ------------------------------------------------------
        # Component stack
        # ------------------------------------------------------

        bottom = np.zeros(n_scenarios)

        for component in components:

            values = np.array([
                result.get(
                    "component_lcoh",
                    {}
                ).get(component, 0.0)
                for result in scenario_results.values()
            ], dtype=float)

            # Skip components that are zero in every scenario
            if not np.any(values != 0):
                continue

            ax.bar(
                x,
                values,
                bottom=bottom,
                width=bar_width,
                label=component
            )

            bottom += values

        # ------------------------------------------------------
        # Total LCOH labels
        # ------------------------------------------------------

        for i, result in enumerate(
            scenario_results.values()
        ):

            total_lcoh = float(
                result.get("total_lcoh", 0.0)
            )

            ax.text(
                i,
                total_lcoh,
                f"{total_lcoh:.2f}",
                ha="center",
                va="bottom",
                fontsize=value_fontsize
            )

        # ------------------------------------------------------
        # Title
        # ------------------------------------------------------

        ax.set_title(
            "LCOH Component Breakdown",
            fontsize=title_fontsize
        )

    # ==========================================================
    # AXIS FORMATTING
    # ==========================================================

    ax.set_xlabel(
        "Scenario",
        fontsize=axis_fontsize
    )

    ax.set_ylabel(
        "LCOH (€/kg H₂)",
        fontsize=axis_fontsize
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        scenario_names,
        fontsize=tick_fontsize
    )

    ax.tick_params(
        axis="y",
        labelsize=tick_fontsize
    )

    # ==========================================================
    # LEGEND
    # ==========================================================

    ax.legend(
        fontsize=legend_fontsize,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=7,
        frameon=False
    )
    # ==========================================================
    # Y AXIS
    # ==========================================================

    ax.set_ylim(
        bottom=0
    )

    # ==========================================================
    # LAYOUT
    # ==========================================================

    # ----------------------------------------------------------
    # Save plot
    # ----------------------------------------------------------
    if save_plot:

        os.makedirs(
            os.path.dirname(plot_file),
            exist_ok=True
        )

        plt.savefig(
            plot_file,
            dpi=300,
            bbox_inches="tight"
        )


    #plt.tight_layout()
    #plt.subplots_adjust(bottom=0.25)

    plt.show()



lcoh_scenarios_plots.__doc__ = PLOT_LCOH_SCENARIOS_DOC