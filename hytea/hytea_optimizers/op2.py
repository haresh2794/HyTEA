import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from copy import deepcopy

from ..hytea_core import HyTEACore


def op2_electrolyser_capacity_storage(
    base_config,
    min_capacity=1.0,
    max_capacity=10.0,
    capacity_step=0.5
):
    """
    OP2 – Electrolyser Capacity vs Hydrogen Storage Requirement

    Determines the electrolyser capacity that requires the minimum
    hydrogen storage capacity, subject to the condition that annual
    hydrogen production is greater than annual hydrogen demand.

    The electrolyser capacity is varied while all other configuration
    parameters remain unchanged.

    Only electrolyser capacities where:

        Annual H2 production > Annual H2 demand

    are considered feasible.

    Among the feasible electrolyser capacities, the capacity with
    the minimum required hydrogen storage capacity is selected.

    Returns:
        dict containing:
            - results: DataFrame
            - minimum_required_storage_t: Minimum required storage
              capacity among feasible electrolyser capacities
            - minimum_electrolyser_capacity_for_storage_mw:
              Electrolyser capacity corresponding to the minimum
              required storage capacity
            - minimum_starting_storage_t: Starting storage at the
              selected electrolyser capacity
            - figure: Matplotlib figure
    """

    # ---------------------------------------------------------
    # Check demand
    # ---------------------------------------------------------

    if "hourly_demand_kgph" not in base_config:
        raise ValueError(
            "OP2 requires 'hourly_demand_kgph' in the configuration."
        )

    demand_kgph = np.asarray(
        base_config["hourly_demand_kgph"],
        dtype=float
    )

    if len(demand_kgph) != 8760:
        raise ValueError(
            f"OP2 requires 8760 hourly demand values. "
            f"Found {len(demand_kgph)}."
        )

    # Annual H2 demand
    annual_h2_demand_t = float(
        np.sum(demand_kgph) / 1000.0
    )

    # ---------------------------------------------------------
    # Check capacity inputs
    # ---------------------------------------------------------

    if min_capacity <= 0:
        raise ValueError(
            "'min_capacity' must be greater than zero."
        )

    if max_capacity < min_capacity:
        raise ValueError(
            "'max_capacity' must be greater than or equal to "
            "'min_capacity'."
        )

    if capacity_step <= 0:
        raise ValueError(
            "'capacity_step' must be greater than zero."
        )

    # ---------------------------------------------------------
    # Generate electrolyser capacity range
    # ---------------------------------------------------------

    capacities = np.arange(
        min_capacity,
        max_capacity + capacity_step / 2,
        capacity_step
    )

    results = []

    # ---------------------------------------------------------
    # Run model for each electrolyser capacity
    # ---------------------------------------------------------

    for electrolyser_capacity in capacities:

        config = deepcopy(base_config)

        # Vary electrolyser capacity
        config["electrolyser"]["electro_capacity"] = float(
            electrolyser_capacity
        )

        # Force Full Storage condition
        config["storage"]["storage_sizing_option"] = "Full storage"

        # Remove user-defined starting storage.
        # This allows the model to calculate the required
        # starting storage automatically.
        config["storage"].pop(
            "starting_h2_storage_t",
            None
        )

        # -----------------------------------------------------
        # Run HyTEA
        # -----------------------------------------------------

        model = HyTEACore()
        model.configure(config)
        model.evaluate()

        storage_results = model.storage_results

        if not storage_results:
            raise ValueError(
                "OP2 could not obtain storage results from HyTEA."
            )

        # -----------------------------------------------------
        # Annual H2 production
        # -----------------------------------------------------

        annual_h2_production_t = (
            float(
                model.electrolyser_results["totals"]["H2_kg"]
            )
            / 1000.0
        )

        # -----------------------------------------------------
        # Check electrolyser sizing
        # -----------------------------------------------------

        production_greater_than_demand = (
            annual_h2_production_t > annual_h2_demand_t
        )

        # -----------------------------------------------------
        # Starting storage
        # -----------------------------------------------------

        starting_storage_t = float(
            storage_results["starting_storage_t"][0]
        )

        # -----------------------------------------------------
        # Required storage capacity
        # -----------------------------------------------------

        required_storage_capacity_t = (
            float(
                storage_results["required_capacity_kg"]
            )
            / 1000.0
        )

        # -----------------------------------------------------
        # Required initial storage
        # -----------------------------------------------------

        required_initial_storage_t = (
            float(
                storage_results["required_initial_storage_kg"]
            )
            / 1000.0
        )

        # -----------------------------------------------------
        # Store results
        # -----------------------------------------------------

        results.append({
            "Electrolyser capacity (MW)": float(
                electrolyser_capacity
            ),
            "Annual H2 production (t/year)": (
                annual_h2_production_t
            ),
            "Annual H2 demand (t/year)": (
                annual_h2_demand_t
            ),
            "Production > Demand": (
                production_greater_than_demand
            ),
            "Starting storage (t)": (
                starting_storage_t
            ),
            "Required initial storage (t)": (
                required_initial_storage_t
            ),
            "Required storage capacity (t)": (
                required_storage_capacity_t
            )
        })

    # ---------------------------------------------------------
    # Create DataFrame
    # ---------------------------------------------------------

    results_df = pd.DataFrame(results)

    # ---------------------------------------------------------
    # Select only capacities where:
    #
    # Annual H2 production > Annual H2 demand
    # ---------------------------------------------------------

    feasible_results_df = results_df[
        results_df["Annual H2 production (t/year)"]
        > results_df["Annual H2 demand (t/year)"]
    ].copy()

    if feasible_results_df.empty:
        raise ValueError(
            "No electrolyser capacity in the specified range "
            "produces more H2 than the annual demand."
        )

    # ---------------------------------------------------------
    # Find minimum required storage capacity
    # among feasible electrolyser capacities
    # ---------------------------------------------------------

    minimum_storage_index = feasible_results_df[
        "Required storage capacity (t)"
    ].idxmin()

    minimum_required_storage_t = float(
        feasible_results_df.loc[
            minimum_storage_index,
            "Required storage capacity (t)"
        ]
    )

    minimum_electrolyser_capacity_for_storage_mw = float(
        feasible_results_df.loc[
            minimum_storage_index,
            "Electrolyser capacity (MW)"
        ]
    )

    minimum_starting_storage_t = float(
        feasible_results_df.loc[
            minimum_storage_index,
            "Starting storage (t)"
        ]
    )

    minimum_h2_production_t = float(
        feasible_results_df.loc[
            minimum_storage_index,
            "Annual H2 production (t/year)"
        ]
    )

    # ---------------------------------------------------------
    # Plot
    # ---------------------------------------------------------

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        results_df["Electrolyser capacity (MW)"],
        results_df["Starting storage (t)"],
        marker="o",
        label="Starting storage"
    )

    ax.plot(
        results_df["Electrolyser capacity (MW)"],
        results_df["Required storage capacity (t)"],
        marker="o",
        label="Required storage capacity"
    )

    ax.set_xlabel(
        "Electrolyser capacity (MW)"
    )

    ax.set_ylabel(
        "Hydrogen storage (t)"
    )

    ax.set_title(
        "Electrolyser Capacity vs Hydrogen Storage Requirement"
    )

    ax.grid(
        True,
        alpha=0.3
    )

    ax.legend()

    plt.tight_layout()
    plt.show()

    # ---------------------------------------------------------
    # Print results
    # ---------------------------------------------------------

    print("\nOP2 result:")

    print(
        f"Annual H2 demand: "
        f"{annual_h2_demand_t:.2f} t/year"
    )

    print(
        f"Annual H2 production at selected capacity: "
        f"{minimum_h2_production_t:.2f} t/year"
    )

    print(
        f"Selected electrolyser capacity: "
        f"{minimum_electrolyser_capacity_for_storage_mw:.2f} MW"
    )

    print(
        f"Minimum required storage capacity: "
        f"{minimum_required_storage_t:.3f} t"
    )

    print(
        f"Starting storage at selected capacity: "
        f"{minimum_starting_storage_t:.3f} t"
    )

    # ---------------------------------------------------------
    # Return
    # ---------------------------------------------------------

    return {
        "results": results_df,
        "minimum_required_storage_t": (
            minimum_required_storage_t
        ),
        "minimum_electrolyser_capacity_for_storage_mw": (
            minimum_electrolyser_capacity_for_storage_mw
        ),
        "minimum_starting_storage_t": (
            minimum_starting_storage_t
        ),
        "figure": fig
    }