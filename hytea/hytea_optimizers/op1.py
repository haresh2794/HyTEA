import numpy as np
import pandas as pd
from copy import deepcopy
from .documentation.op1_doc import OP1_MIN_ELECTROLYSER_CAPACITY_DOC

from ..hytea_core import HyTEACore

def op1_min_electrolyser_capacity(
    base_config,
    min_capacity=1.0,
    max_capacity=10.0,
    capacity_step=0.5,
    tolerance_kg=1e-6
):
    """
    OP1 – Minimum Electrolyser Capacity with Fixed Hydrogen Storage

    Determines the minimum electrolyser capacity required to satisfy
    hydrogen demand in all 8,760 hours of the year while keeping the
    storage capacity fixed as specified in the configuration.

    The function tests electrolyser capacities over the specified range
    and identifies the smallest capacity for which hourly hydrogen supply
    is sufficient to meet demand in every hour.

    Requirement:
    storage_sizing_option must be set to "Tonnes" and
    storage_capacity_tonnes must be specified.

    Only the electrolyser capacity is varied. All other configuration
    parameters remain unchanged.
    """

    # =========================================================
    # CHECK STORAGE CONFIGURATION
    # =========================================================

    storage_config = base_config.get("storage", {})

    if storage_config.get("storage_sizing_option") != "Tonnes":
        raise ValueError(
            "OP1 requires storage_sizing_option='Tonnes'. "
            f"Current value: "
            f"{storage_config.get('storage_sizing_option')}"
        )

    if "storage_capacity_tonnes" not in storage_config:
        raise ValueError(
            "OP1 requires 'storage_capacity_tonnes' when "
            "storage_sizing_option='Tonnes'."
        )

    storage_capacity_tonnes = float(
        storage_config["storage_capacity_tonnes"]
    )

    # =========================================================
    # CHECK DEMAND
    # =========================================================

    if "hourly_demand_kgph" not in base_config:
        raise ValueError(
            "OP1 requires 'hourly_demand_kgph' in the configuration."
        )

    demand_kgph = np.asarray(
        base_config["hourly_demand_kgph"],
        dtype=float
    )

    if len(demand_kgph) != 8760:
        raise ValueError(
            f"OP1 requires 8760 hourly demand values. "
            f"Found {len(demand_kgph)}."
        )

    # =========================================================
    # CAPACITY RANGE
    # =========================================================

    capacities = np.arange(
        min_capacity,
        max_capacity + capacity_step / 2,
        capacity_step
    )

    results = []

    minimum_capacity = None
    minimum_result = None

    # =========================================================
    # RUN EACH ELECTROLYSER CAPACITY
    # =========================================================

    for electrolyser_capacity in capacities:

        # -----------------------------------------------------
        # Copy the original configuration
        # -----------------------------------------------------

        config = deepcopy(base_config)

        # -----------------------------------------------------
        # Change ONLY electrolyser capacity
        # -----------------------------------------------------

        config["electrolyser"]["electro_capacity"] = float(
            electrolyser_capacity
        )

        # -----------------------------------------------------
        # Run HyTEA
        # -----------------------------------------------------

        model = HyTEACore()

        model.configure(config)

        result = model.evaluate()

        # =====================================================
        # GET THE ACTUAL H2 SUPPLY STREAM FROM CORE
        # =====================================================
        #
        # This is the supply stream used by Core for the
        # annual H2 balance.
        #
        # It includes the appropriate production/storage
        # supply stream.
        # =====================================================

        supply_kgph = np.asarray(
            model.h2_supply_kgph,
            dtype=float
        )

        if len(supply_kgph) != 8760:
            raise ValueError(
                "HyTEA H2 supply stream does not contain 8760 "
                f"values. Found {len(supply_kgph)}."
            )

        # =====================================================
        # HOURLY SUPPLY VS DEMAND
        # =====================================================

        hourly_difference_kg = (
            supply_kgph - demand_kgph
        )

        # Deficit only if supply is below demand by more than
        # the numerical tolerance.

        deficit_mask = (
            hourly_difference_kg < -tolerance_kg
        )

        number_of_deficit_hours = int(
            np.sum(deficit_mask)
        )

        hourly_deficit_kg = np.maximum(
            demand_kgph - supply_kgph,
            0.0
        )

        total_deficit_kg = float(
            np.sum(hourly_deficit_kg)
        )

        demand_satisfied = (
            number_of_deficit_hours == 0
        )

        # =====================================================
        # WORST HOURLY DIFFERENCE
        # =====================================================

        minimum_hourly_difference_kg = float(
            np.min(hourly_difference_kg)
        )

        maximum_hourly_difference_kg = float(
            np.max(hourly_difference_kg)
        )

        # =====================================================
        # ANNUAL RESULTS
        # =====================================================

        annual_balance = result[
            "annual_balance_results"
        ]

        h2_produced = annual_balance[
            "annual_production_kg"
        ]

        h2_supplied = annual_balance[
            "annual_supply_kg"
        ]

        h2_demand = annual_balance[
            "annual_demand_kg"
        ]

        # =====================================================
        # STORE RESULT
        # =====================================================

        results.append({
            "Electrolyser capacity (MW)": float(
                electrolyser_capacity
            ),

            "Storage capacity (t)": (
                storage_capacity_tonnes
            ),

            "H2 produced (kg)": (
                h2_produced
            ),

            "H2 demand (kg)": (
                h2_demand
            ),

            "H2 supplied (kg)": (
                h2_supplied
            ),

            "Number of deficit hours": (
                number_of_deficit_hours
            ),

            "Total H2 deficit (kg)": (
                total_deficit_kg
            ),

            "Minimum hourly supply-demand difference (kg)": (
                minimum_hourly_difference_kg
            ),

            "Maximum hourly supply-demand difference (kg)": (
                maximum_hourly_difference_kg
            ),

            "Demand satisfied all 8760 hours": (
                demand_satisfied
            )
        })

        # =====================================================
        # FIRST FEASIBLE CAPACITY
        # =====================================================

        if demand_satisfied:

            minimum_capacity = float(
                electrolyser_capacity
            )

            minimum_result = result

            break

    # =========================================================
    # RESULTS DATAFRAME
    # =========================================================

    results_df = pd.DataFrame(results)

    # =========================================================
    # MESSAGE
    # =========================================================

    if minimum_capacity is not None:

        print(
            f"\nOP1 result: The minimum electrolyser capacity "
            f"required to satisfy hydrogen demand in all 8,760 "
            f"hours is {minimum_capacity:.1f} MW, using "
            f"{storage_capacity_tonnes:.2f} tonnes of fixed "
            f"hydrogen storage."
        )

    else:

        print(
            f"\nOP1 result: No electrolyser capacity between "
            f"{min_capacity:.1f} and {max_capacity:.1f} MW "
            f"can satisfy hydrogen demand in all 8,760 hours "

        )

    return {
      "minimum_electrolyser_capacity_mw": minimum_capacity,
      "storage_capacity_t": storage_capacity_tonnes,
      "results": results_df,
      "minimum_result": minimum_result
  }


op1_min_electrolyser_capacity.__doc__ = OP1_MIN_ELECTROLYSER_CAPACITY_DOC