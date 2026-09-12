import os
import numpy as np
import pandas as pd
from .documentation.save_scenarios_to_csv_doc import SAVE_SCENARIO_RESULTS_TO_CSV_DOC

def save_scenario_results_to_csv(
    scenarios,
    output_file="scenario_results.csv"
):
    

    rows = []

    for scenario in scenarios:

        # =====================================================
        # GET CONFIGURATION AND RESULTS DIRECTLY FROM CORE
        # =====================================================

        config = scenario.config
        result = scenario.evaluate()

        # =====================================================
        # SCENARIO NAME
        # =====================================================

        scenario_name = result["scenario_name"]

        row = {
            "Scenario": scenario_name
        }

        # =====================================================
        # RESE
        # Only:
        #   - Capacity (MW)
        #   - Price (€/MWh)
        # =====================================================

        rese_config = config.get("rese_sources", {})

        for source_name, source_config in rese_config.items():

            row[f"RESE_{source_name}_capacity_mw"] = (
                source_config.get("capacity_mw", np.nan)
            )

            row[f"RESE_{source_name}_price_eur_per_mwh"] = (
                source_config.get("price_eur_per_mwh", np.nan)
            )

        # =====================================================
        # ECONOMICS CONFIGURATION
        # =====================================================

        economics_config = config.get("economics", {})

        row["economics_h2_lcoh_basis"] = (
            economics_config.get("h2_lcoh_basis", np.nan)
        )

        # =====================================================
        # GRID CONFIGURATION
        # =====================================================

        grid_config = config.get("grid", {})

        row["integrate_grid"] = config.get(
            "integrate_grid",
            grid_config.get("integrate_grid", np.nan)
        )

        row["grid_ghg_avg"] = grid_config.get(
            "ghg_avg",
            grid_config.get("grid_ghg_avg", np.nan)
        )

        # =====================================================
        # STORAGE
        # =====================================================

        storage_config = config.get("storage", {})
        storage_results = result["storage_results"]

        row["storage_storage_sizing_option"] = (
            storage_config.get("storage_sizing_option", np.nan)
        )

        row["storage_storage_capacity_tonnes"] = (
            storage_config.get("storage_capacity_tonnes", np.nan)
        )

        # Full storage capacity is only reported when storage
        # capacity is calculated by the model.
        if storage_config.get("storage_sizing_option") == "Tonnes":
            row["Full storage capacity (t)"] = np.nan
        else:
            row["Full storage capacity (t)"] = (
                storage_results["required_capacity_kg"] / 1000.0
            )

        # =====================================================
        # H2 PRODUCTION / DELIVERY
        # =====================================================

        annual_balance = result["annual_balance_results"]

        row["H2 delivered (kg)"] = (
            annual_balance["annual_supply_kg"]
        )

        row["H2 produced (kg)"] = (
            annual_balance["annual_production_kg"]
        )



        # =====================================================
        # LCOH
        # =====================================================

        levelized_cost_results = result["levelized_cost_results"]

        row["LCOH (€/kg H2)"] = (
            levelized_cost_results["total_lcoh"]
        )

        row["LCOH - CAPEX (€/kg H2)"] = (
            levelized_cost_results["capex_lcoh"]
        )

        row["LCOH - OPEX (€/kg H2)"] = (
            levelized_cost_results["opex_lcoh"]
        )

        # =====================================================
        # GHG RESULTS
        # =====================================================

        ghg_results = result["ghg_results"]

        row["GHG intensity (tCO2/tH2)"] = (
            ghg_results["ghg_t_per_tH2"]
        )

        row["GHG intensity (gCO2/kWh)"] = (
            ghg_results["ghg_g_per_kWh"]
        )

        row["Total GHG (tCO2/year)"] = (
            ghg_results["total_ghg_t_per_year"]
        )

        row["Grid GHG (tCO2/year)"] = (
            ghg_results["grid_ghg_t_per_year"]
        )

        row["Transport GHG (tCO2/year)"] = (
            ghg_results["transport_ghg_t_per_year"]
        )

        # =====================================================
        # LCOH COMPONENT BREAKDOWN
        # =====================================================

        component_lcoh = levelized_cost_results.get(
            "component_lcoh", {}
        )

        for component, value in component_lcoh.items():

            row[f"LCOH - {component}"] = value

        # =====================================================
        # LCOH CAPEX BREAKDOWN
        # =====================================================

        capex_lcoh_breakdown = levelized_cost_results.get(
            "capex_lcoh_breakdown", {}
        )

        for component, value in capex_lcoh_breakdown.items():

            row[f"LCOH CAPEX - {component}"] = value

        # =====================================================
        # LCOH OPEX BREAKDOWN
        # =====================================================

        opex_lcoh_breakdown = levelized_cost_results.get(
            "opex_lcoh_breakdown", {}
        )

        for component, value in opex_lcoh_breakdown.items():

            row[f"LCOH OPEX - {component}"] = value

        # =====================================================
        # ADD ROW
        # =====================================================

        rows.append(row)

    # =========================================================
    # CREATE DATAFRAME
    # =========================================================

    df = pd.DataFrame(rows)

    # =========================================================
    # SAVE CSV
    # =========================================================

    output_dir = os.path.dirname(output_file)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    df.to_csv(
        output_file,
        index=False
    )

    print(f"Scenario results saved to: {output_file}")

    return df

save_scenario_results_to_csv.__doc__ = SAVE_SCENARIO_RESULTS_TO_CSV_DOC