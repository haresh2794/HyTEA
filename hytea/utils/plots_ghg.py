
import matplotlib.pyplot as plt
import numpy as np
import os
from .documentation.plots_ghg_doc import PLOT_GHG_INTENSITY_SCENARIOS_DOC

def ghg_intensity_scenarios_plots(
    scenario_results,
    metric="ghg_g_per_kWh",
    figsize=(10, 6),
    title_fontsize=16,
    axis_fontsize=13,
    tick_fontsize=11,
    value_fontsize=11,
    bar_width=0.7,
    save_plot=True,
    plot_file="plots/results/ghg_intensity.png"
):
    
    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    valid_metrics = [
        "ghg_g_per_kWh",
        "ghg_t_per_tH2"
    ]

    if metric not in valid_metrics:
        raise ValueError(
            f"Invalid metric '{metric}'. "
            f"Choose from {valid_metrics}."
        )

    if not scenario_results:
        raise ValueError(
            "scenario_results cannot be empty."
        )

    # ----------------------------------------------------------
    # Scenario names
    # ----------------------------------------------------------

    scenario_names = list(
        scenario_results.keys()
    )

    # ----------------------------------------------------------
    # Extract GHG values
    # ----------------------------------------------------------

    ghg_values = []

    for scenario_name, result in scenario_results.items():

        if metric not in result:
            raise KeyError(
                f"'{metric}' not found in GHG results "
                f"for '{scenario_name}'."
            )

        ghg_values.append(
            float(result[metric])
        )

    # ----------------------------------------------------------
    # X positions
    # ----------------------------------------------------------

    x = np.arange(
        len(scenario_names)
    )

    # ----------------------------------------------------------
    # Plot
    # ----------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=figsize
    )

    bars = ax.bar(
        x,
        ghg_values,
        width=bar_width
    )

    # ----------------------------------------------------------
    # Values above bars
    # ----------------------------------------------------------

    for bar, value in zip(
        bars,
        ghg_values
    ):

        ax.text(
            bar.get_x()
            + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=value_fontsize
        )

    # ----------------------------------------------------------
    # Axis labels
    # ----------------------------------------------------------

    ax.set_xlabel(
        "Scenario",
        fontsize=axis_fontsize
    )

    if metric == "ghg_g_per_kWh":

        ax.set_ylabel(
            "GHG Intensity (gCO₂/kWh H₂)",
            fontsize=axis_fontsize
        )

    elif metric == "ghg_t_per_tH2":

        ax.set_ylabel(
            "GHG Intensity (tCO₂/tH₂)",
            fontsize=axis_fontsize
        )

    ax.set_title(
        "GHG Intensity by Scenario",
        fontsize=title_fontsize
    )

    # ----------------------------------------------------------
    # X-axis
    # ----------------------------------------------------------

    ax.set_xticks(x)

    ax.set_xticklabels(
        scenario_names,
        fontsize=tick_fontsize
    )

    # ----------------------------------------------------------
    # Y-axis
    # ----------------------------------------------------------

    ax.tick_params(
        axis="y",
        labelsize=tick_fontsize
    )

    ax.set_ylim(
        bottom=0
    )

    # ----------------------------------------------------------
    # Layout
    # ----------------------------------------------------------

    plt.tight_layout()

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



    plt.show()



ghg_intensity_scenarios_plots.__doc__ = PLOT_GHG_INTENSITY_SCENARIOS_DOC