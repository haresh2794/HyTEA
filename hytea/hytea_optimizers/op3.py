import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from copy import deepcopy

from ..hytea_core import HyTEACore

def op3_supply_led_production_ele_sizing(
    base_config,
    min_capacity=1.0,
    max_capacity=10.0,
    capacity_step=0.5,

    include_lcoh=False,
    include_capacity_factor=True,

    plot=False,

    figsize=(10, 6),

    title="Supply-led hydrogen production",
    capacity_factor_title="Electrolyser capacity factor",

    xlabel="Electrolyser capacity (MW)",
    h2_ylabel="Annual H₂ production (tH₂/year)",
    lcoh_ylabel="LCOH (€/kg H₂)",
    capacity_factor_ylabel="Electrolyser capacity factor (%)",

    title_fontsize=16,
    axis_fontsize=13,
    tick_fontsize=11,
    legend_fontsize=11,

    linewidth=2.0,
    marker_size=6,

    fontfamily="DejaVu Sans",

    h2_color="darkgreen",
    lcoh_color="darkred",
    capacity_factor_color="darkorange",

    grid=True,

    save_plot=False,
    plot_filename="supply_led_h2_production.png",
    capacity_factor_plot_filename="supply_led_capacity_factor.png",

    print_results=True
):
    """
    Evaluate annual hydrogen production for a range of electrolyser
    capacities under supply-led operation.

    Parameters
    ----------
    base_config : dict
        Base HyTEA configuration.

    min_capacity : float
        Minimum electrolyser capacity in MW.

    max_capacity : float
        Maximum electrolyser capacity in MW.

    capacity_step : float
        Step size for electrolyser capacity in MW.

    include_lcoh : bool
        If True, extract and plot LCOH.

    include_capacity_factor : bool
        If True, calculate and plot electrolyser capacity factor.

    plot : bool
        If True, generate plots.

    figsize : tuple
        Figure size.

    title : str
        Title for the H₂ production/LCOH plot.

    capacity_factor_title : str
        Title for the capacity factor plot.

    xlabel : str
        X-axis label.

    h2_ylabel : str
        H₂ production y-axis label.

    lcoh_ylabel : str
        LCOH y-axis label.

    capacity_factor_ylabel : str
        Capacity factor y-axis label.

    title_fontsize : int
        Plot title font size.

    axis_fontsize : int
        Axis label font size.

    tick_fontsize : int
        Tick label font size.

    legend_fontsize : int
        Legend font size.

    linewidth : float
        Line width.

    marker_size : float
        Marker size.

    fontfamily : str
        Matplotlib font family.

    h2_color : str
        Colour for H₂ production.

    lcoh_color : str
        Colour for LCOH.

    capacity_factor_color : str
        Colour for capacity factor.

    grid : bool
        Whether to show grid lines.

    save_plot : bool
        Whether to save the plots.

    plot_filename : str
        Filename for the H₂/LCOH plot.

    capacity_factor_plot_filename : str
        Filename for the capacity factor plot.

    print_results : bool
        Whether to print results.

    Returns
    -------
    dict
        Dictionary containing the results DataFrame and arrays.
    """

    import copy
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    # ==========================================================
    # Validate input
    # ==========================================================

    if not isinstance(base_config, dict):
        raise TypeError(
            "base_config must be a dictionary."
        )

    if "electrolyser" not in base_config:
        raise ValueError(
            "base_config must contain an "
            "'electrolyser' section."
        )

    operation_mode = base_config.get(
        "operation_mode",
        "demand_led"
    ).lower()

    if operation_mode != "supply_led":
        raise ValueError(
            "This function requires "
            "operation_mode='supply_led'."
        )

    if min_capacity <= 0:
        raise ValueError(
            "min_capacity must be greater than zero."
        )

    if max_capacity < min_capacity:
        raise ValueError(
            "max_capacity must be greater than or equal "
            "to min_capacity."
        )

    if capacity_step <= 0:
        raise ValueError(
            "capacity_step must be greater than zero."
        )

    # ==========================================================
    # Generate electrolyser capacity range
    # ==========================================================

    capacities = np.arange(
        min_capacity,
        max_capacity + capacity_step / 2,
        capacity_step
    )

    # ==========================================================
    # Storage for results
    # ==========================================================

    results = []

    # ==========================================================
    # Run each electrolyser capacity
    # ==========================================================

    for capacity in capacities:

        # ------------------------------------------------------
        # Create independent configuration
        # ------------------------------------------------------

        config = copy.deepcopy(base_config)

        config["operation_mode"] = "supply_led"

        config["electrolyser"]["electro_capacity"] = float(
            capacity
        )

        # ------------------------------------------------------
        # Run HyTEA
        # ------------------------------------------------------

        model = HyTEACore()

        model.configure(config)

        result = model.evaluate()

        # ======================================================
        # Annual H₂ production
        # ======================================================

        annual_production_kg = result[
            "annual_balance_results"
        ]["annual_production_kg"]

        annual_production_tonnes = (
            annual_production_kg / 1000.0
        )

        # ======================================================
        # Annual H₂ supply
        # ======================================================

        annual_supply_kg = result[
            "annual_balance_results"
        ]["annual_supply_kg"]

        annual_supply_tonnes = (
            annual_supply_kg / 1000.0
        )

        # ======================================================
        # Annual H₂ demand
        # ======================================================

        annual_demand_kg = result[
            "annual_balance_results"
        ]["annual_demand_kg"]

        annual_demand_tonnes = (
            annual_demand_kg / 1000.0
        )

        # ======================================================
        # Electrolyser capacity factor
        # ======================================================

        if include_capacity_factor:

            capacity_factor = result[
                "electrolyser_results"
            ]["totals"]["capacity_factor"]

            capacity_factor_percent = (
                capacity_factor * 100
            )

        else:

            capacity_factor = np.nan
            capacity_factor_percent = np.nan

        # ======================================================
        # LCOH
        # ======================================================

        if include_lcoh:

            lcoh = result[
                "levelized_cost_results"
            ]["total_lcoh"]

        else:

            lcoh = np.nan

        # ======================================================
        # Store results
        # ======================================================

        results.append(
            {
                "Electrolyser capacity (MW)": capacity,

                "H2 produced (kg/year)": (
                    annual_production_kg
                ),

                "H2 produced (tH₂/year)": (
                    annual_production_tonnes
                ),

                "H2 supplied (kg/year)": (
                    annual_supply_kg
                ),

                "H2 supplied (tH₂/year)": (
                    annual_supply_tonnes
                ),

                "H2 demand (kg/year)": (
                    annual_demand_kg
                ),

                "H2 demand (tH₂/year)": (
                    annual_demand_tonnes
                ),

                "Capacity factor": (
                    capacity_factor
                ),

                "Capacity factor (%)": (
                    capacity_factor_percent
                ),

                "LCOH (€/kg H2)": (
                    lcoh
                )
            }
        )

        # ======================================================
        # Print individual result
        # ======================================================

        if print_results:

            output = (
                f"Electrolyser: {capacity:.2f} MW | "
                f"H₂ production: "
                f"{annual_production_tonnes:,.2f} tH₂/year"
            )

            if include_capacity_factor:

                output += (
                    f" | Capacity factor: "
                    f"{capacity_factor_percent:.2f}%"
                )

            if include_lcoh:

                output += (
                    f" | LCOH: "
                    f"€{lcoh:.3f}/kg"
                )

            print(output)

    # ==========================================================
    # Convert results to DataFrame
    # ==========================================================

    results_df = pd.DataFrame(results)

    # ==========================================================
    # Print summary
    # ==========================================================

    if print_results:

        print("\n" + "=" * 90)
        print("")
        print("=" * 90)

        summary_columns = [
            "Electrolyser capacity (MW)",
            "H2 produced (tH₂/year)",
            "H2 supplied (tH₂/year)",
            "H2 demand (tH₂/year)"
        ]

        if include_capacity_factor:

            summary_columns.append(
                "Capacity factor (%)"
            )

        print(
            results_df[
                summary_columns
            ].to_string(index=False)
        )

        # ------------------------------------------------------
        # LCOH summary
        # ------------------------------------------------------

        if include_lcoh:

            print("\nLCOH results:")

            print(
                results_df[
                    [
                        "Electrolyser capacity (MW)",
                        "LCOH (€/kg H2)"
                    ]
                ].to_string(index=False)
            )

    # ==========================================================
    # Plot
    # ==========================================================

    if plot:

        # ------------------------------------------------------
        # Set font
        # ------------------------------------------------------

        plt.rcParams["font.family"] = fontfamily

        # ------------------------------------------------------
        # Create main figure
        # ------------------------------------------------------

        fig, ax1 = plt.subplots(
            figsize=figsize
        )

        # ======================================================
        # Axis 1 — Annual H₂ production
        # ======================================================

        line1 = ax1.plot(
            results_df[
                "Electrolyser capacity (MW)"
            ],

            results_df[
                "H2 produced (tH₂/year)"
            ],

            marker="o",
            markersize=marker_size,
            linewidth=linewidth,
            color=h2_color,

            label="Annual H₂ production"
        )

        ax1.set_xlabel(
            xlabel,
            fontsize=axis_fontsize
        )

        ax1.set_ylabel(
            h2_ylabel,
            fontsize=axis_fontsize,
            color=h2_color
        )

        ax1.tick_params(
            axis="both",
            labelsize=tick_fontsize
        )

        ax1.tick_params(
            axis="y",
            labelcolor=h2_color
        )

        # ======================================================
        # Axis 2 — LCOH
        # ======================================================

        line2 = []

        if include_lcoh:

            ax2 = ax1.twinx()

            line2 = ax2.plot(
                results_df[
                    "Electrolyser capacity (MW)"
                ],

                results_df[
                    "LCOH (€/kg H2)"
                ],

                marker="s",
                markersize=marker_size,
                linewidth=linewidth,
                color=lcoh_color,

                label="LCOH"
            )

            ax2.set_ylabel(
                lcoh_ylabel,
                fontsize=axis_fontsize,
                color=lcoh_color
            )

            ax2.tick_params(
                axis="y",
                labelsize=tick_fontsize,
                labelcolor=lcoh_color
            )

        # ======================================================
        # Axis 3 — Capacity factor
        # ======================================================

        line3 = []

        if include_capacity_factor:

            ax3 = ax1.twinx()

            # Move the third axis to the right
            ax3.spines["right"].set_position(
                ("outward", 65)
            )

            line3 = ax3.plot(
                results_df[
                    "Electrolyser capacity (MW)"
                ],

                results_df[
                    "Capacity factor (%)"
                ],

                marker="^",
                markersize=marker_size,
                linewidth=linewidth,
                color=capacity_factor_color,

                label="Capacity factor"
            )

            ax3.set_ylabel(
                capacity_factor_ylabel,
                fontsize=axis_fontsize,
                color=capacity_factor_color
            )

            ax3.tick_params(
                axis="y",
                labelsize=tick_fontsize,
                labelcolor=capacity_factor_color
            )

            # Optional: keep capacity factor between 0 and 100%
            ax3.set_ylim(
                0,
                100
            )

        # ======================================================
        # Grid
        # ======================================================

        if grid:

            ax1.grid(
                True,
                linestyle="--",
                alpha=0.4
            )

        # ======================================================
        # Combined legend
        # ======================================================

        lines = line1 + line2 + line3

        labels = [
            line.get_label()
            for line in lines
        ]

        ax1.legend(
            lines,
            labels,
            fontsize=legend_fontsize,
            loc="best"
        )

        # ======================================================
        # Title
        # ======================================================

        ax1.set_title(
            title,
            fontsize=title_fontsize
        )

        # ======================================================
        # Tick font sizes
        # ======================================================

        for label in ax1.get_xticklabels():

            label.set_fontsize(
                tick_fontsize
            )

        for label in ax1.get_yticklabels():

            label.set_fontsize(
                tick_fontsize
            )

        # ======================================================
        # Layout
        # ======================================================

        fig.tight_layout()

        # ------------------------------------------------------
        # Save
        # ------------------------------------------------------

        if save_plot:

            fig.savefig(
                plot_filename,
                dpi=300,
                bbox_inches="tight"
            )

            print(
                f"\nPlot saved to: "
                f"{plot_filename}"
            )

        plt.show()

    # ==========================================================
    # Return results
    # ==========================================================

    return {
        "results": results_df,

        "capacities_mw": results_df[
            "Electrolyser capacity (MW)"
        ].to_numpy(),

        "annual_h2_production_tonnes": results_df[
            "H2 produced (tH₂/year)"
        ].to_numpy(),

        "annual_h2_supply_tonnes": results_df[
            "H2 supplied (tH₂/year)"
        ].to_numpy(),

        "annual_h2_demand_tonnes": results_df[
            "H2 demand (tH₂/year)"
        ].to_numpy(),

        "capacity_factor": results_df[
            "Capacity factor"
        ].to_numpy(),

        "capacity_factor_percent": results_df[
            "Capacity factor (%)"
        ].to_numpy(),

        "lcoh_eur_per_kg": results_df[
            "LCOH (€/kg H2)"
        ].to_numpy()
    }