import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_demand_profile(
    use_demand_file=False,
    constant_demand=50,
    demand_column="demand",
    plot_demand=False,
    save_plot=False,
    plot_file="plots/demand_profile.png"
):
    """
    Load an hourly hydrogen demand profile.

    If use_demand_file=False:
        Uses a constant hourly demand.

    If use_demand_file is a CSV path:
        Loads the hourly demand profile from that CSV file.

    Returns
    -------
    np.ndarray
        8760-hour demand profile in kg/h.
    """

    # ==========================================================
    # USER-PROVIDED CSV PROFILE
    # ==========================================================
    if use_demand_file:

        input_file = use_demand_file

        if not os.path.isfile(input_file):
            raise FileNotFoundError(
                f"Demand file not found: {input_file}"
            )

        df = pd.read_csv(input_file)

        if demand_column not in df.columns:
            raise ValueError(
                f"Column '{demand_column}' not found in the CSV. "
                f"Available columns: {list(df.columns)}"
            )

        demand = df[demand_column].astype(float).to_numpy()

        # Handle leap year
        if len(demand) == 8784:
            print(
                "8784-hour leap-year profile detected. "
                "Using the first 8760 hours."
            )
            demand = demand[:8760]

        if len(demand) != 8760:
            raise ValueError(
                f"Demand profile must contain 8760 hours. "
                f"Found {len(demand)} hours."
            )

        print(f"Loaded demand profile from: {input_file}")

    # ==========================================================
    # CONSTANT DEMAND
    # ==========================================================
    else:

        demand = np.full(
            8760,
            constant_demand,
            dtype=float
        )

        print(
            f"Using constant demand of "
            f"{constant_demand} kg/h."
        )

    # ==========================================================
    # PLOT DEMAND PROFILE
    # ==========================================================
    if plot_demand or save_plot:

        plt.figure(figsize=(12, 4))

        plt.plot(
            np.arange(1, 8761),
            demand,
            linewidth=0.8
        )

        plt.xlabel("Hour of Year")
        plt.ylabel("Hydrogen Demand (kg/h)")
        plt.title("Hourly Hydrogen Demand Profile")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save plot
        if save_plot:

            plot_dir = os.path.dirname(plot_file)

            if plot_dir:
                os.makedirs(plot_dir, exist_ok=True)

            plt.savefig(
                plot_file,
                dpi=300,
                bbox_inches="tight"
            )

            print(f"Demand plot saved to: {plot_file}")

        if plot_demand:
            plt.show()

        plt.close()

    return demand