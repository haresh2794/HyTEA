import numpy as np
import pandas as pd

from hytea.hytea_components.rese.rese_model import RenewableElectricity
from hytea.hytea_components.grid.grid_model import Grid
from hytea.hytea_components.electrolyser.electrolyser_model import ALKElectrolyser
from hytea.hytea_components.storage.storage import HydrogenStorage
from hytea.hytea_components.transport.truck_transport import HydrogenTruckTransport
from hytea.hytea_components.finance.discounting import DiscountingModel
from hytea.hytea_components.finance.lc import LevelizedCostModel


class HyTEACore:
    """
    HyTEA Core - Version 5

    Responsibilities:
    - run multiple RESE sources
    - aggregate RESE outputs
    - build hourly_cf_mul for Grid
    - run Grid only if integrated
    - configure Electrolyser
    - calculate residual grid stream required to meet electrolyser input capacity
    - build final stream-wise power DataFrame in kW
    - run Electrolyser with RESE + optional Grid stream
    - configure and run Storage using electrolyser outputs
    - configure and run Transport using storage/electrolyser outputs

    Current scope:
    - RESE
    - optional Grid
    - Electrolyser
    - Storage
    - Truck transport
    - no finance
    """

    def __init__(self):
        self.config = {}

        self.rese_models = {}
        self.rese_results = {}
        self.aggregated_results = {}

        self.grid_model = None
        self.grid_results = {}
        self.grid_summary = {}

        self.electrolyser_model = None
        self.electrolyser_results = {}

        self.storage_model = None
        self.storage_results = {}

        self.transport_model = None
        self.transport_results = {}

        self.power_df = None
        self.grid_stream_kW = None

        self.finance_results = {}
        self.discounting_results = {}
        self.levelized_cost_results = {}

    def configure(self, config):
        self.config = dict(config)

    def validate_config(self):
        if not isinstance(self.config, dict):
            raise ValueError("config must be a dictionary.")

        if "rese_sources" not in self.config:
            raise ValueError("config must contain 'rese_sources'.")

        if not isinstance(self.config["rese_sources"], dict):
            raise ValueError("'rese_sources' must be a dictionary of named RESE sources.")

        if len(self.config["rese_sources"]) == 0:
            raise ValueError("'rese_sources' cannot be empty.")

        if "electrolyser" not in self.config:
            raise ValueError("config must contain 'electrolyser'.")

        if self.config.get("integrate_grid", False) and "grid" not in self.config:
            raise ValueError("grid config is required when integrate_grid=True.")

        if "storage" not in self.config:
            raise ValueError("config must contain 'storage' for this version.")

        if "transport" not in self.config:
            raise ValueError("config must contain 'transport' for this version.")
        if "finance" not in self.config:
            raise ValueError("config must contain 'finance' for this version.")

    def run_rese_sources(self):
        self.rese_models = {}
        self.rese_results = {}

        for source_name, source_config in self.config["rese_sources"].items():
            csv_file = source_config.get("csv_file", None)

            rese_config = dict(source_config)
            rese_config.pop("csv_file", None)

            model = RenewableElectricity()
            model.configure(config=rese_config, csv_file=csv_file)

            self.rese_models[source_name] = model
            self.rese_results[source_name] = model.evaluate()

        return self.rese_results

    def aggregate_rese_results(self):
        if not self.rese_results:
            self.aggregated_results = {}
            return self.aggregated_results

        hourly_output_arrays = []
        cumulative_hourly_arrays = []

        total_capex = 0.0
        total_opex = 0.0

        for _, result in self.rese_results.items():
            hourly_output = np.asarray(result["hourly_output_mw"], dtype=float)
            cumulative_hourly = np.asarray(result["cumulative_energy_gwh_hourly"], dtype=float)

            hourly_output_arrays.append(hourly_output)
            cumulative_hourly_arrays.append(cumulative_hourly)

            total_capex += float(result["capex"])
            total_opex += float(result["opex"])

        combined_hourly_output_mw = np.sum(hourly_output_arrays, axis=0)
        combined_cumulative_energy_gwh_hourly = np.sum(cumulative_hourly_arrays, axis=0)

        self.aggregated_results = {
            "hourly_output_mw": combined_hourly_output_mw,
            "total_capex": total_capex,
            "total_opex": total_opex,
            "cumulative_energy_gwh_hourly": combined_cumulative_energy_gwh_hourly,
            "cumulative_energy_gwh_total": float(combined_cumulative_energy_gwh_hourly[-1]),
        }

        return self.aggregated_results

    def build_hourly_cf_mul(self):
        if not self.rese_models:
            return None

        cf_arrays = []

        for source_name, model in self.rese_models.items():
            if model.hourly_cf is None:
                raise ValueError(
                    f"hourly_cf not available for source '{source_name}'. "
                    "Make sure RESE sources are evaluated before building hourly_cf_mul."
                )

            cf_arrays.append(np.asarray(model.hourly_cf, dtype=float))

        return np.vstack(cf_arrays)

    def run_grid(self):
        if not self.config.get("integrate_grid", False):
            self.grid_model = None
            self.grid_results = {}
            self.grid_summary = {}
            return self.grid_results

        hourly_cf_mul = self.build_hourly_cf_mul()

        self.grid_model = Grid()
        self.grid_model.configure(
            config=self.config.get("grid", {}),
            hourly_cf_mul=hourly_cf_mul
        )

        self.grid_results = self.grid_model.evaluate()

        self.grid_summary = {
            "hourly_weighted_cf": self.grid_results["hourly_weighted_cf"],
            "hourly_price_trend": self.grid_results["hourly_price_trend"],
            "hourly_purchase_price_trend": self.grid_results["hourly_purchase_price_trend"],
            "hourly_sales_price_trend": self.grid_results["hourly_sales_price_trend"],
            "hourly_ghg_trend": self.grid_results["hourly_ghg_trend"],
            "avg_weighted_cf": float(np.mean(self.grid_results["hourly_weighted_cf"])),
            "avg_purchase_price": float(np.mean(self.grid_results["hourly_purchase_price_trend"])),
            "avg_sales_price": float(np.mean(self.grid_results["hourly_sales_price_trend"])),
            "avg_ghg_intensity": float(np.mean(self.grid_results["hourly_ghg_trend"])),
             "avg_price_trend": float(np.mean(self.grid_results["avg_price_trend"])),
        }

        return self.grid_results

    def setup_electrolyser(self):
        """
        Configure the electrolyser once so the core can access
        the actual required input capacity before building the grid stream.
        """
        self.electrolyser_model = ALKElectrolyser()
        self.electrolyser_model.configure(config=self.config.get("electrolyser", {}))
        return self.electrolyser_model

    def build_rese_power_df(self):
        """
        Build stream-wise RESE power DataFrame in kW.
        """
        stream_power = {}

        for source_name, result in self.rese_results.items():
            hourly_output_mw = np.asarray(result["hourly_output_mw"], dtype=float)
            stream_power[source_name] = hourly_output_mw * 1000.0  # MW -> kW

        if not stream_power:
            raise ValueError("No RESE stream outputs available for electrolyser input.")

        return pd.DataFrame(stream_power)

    def build_grid_stream(self, rese_power_df):
        """
        Build hourly grid stream in kW as residual power required to meet
        the electrolyser actual input capacity.

        At this stage:
        - if integrate_grid is False, returns zeros
        - if integrate_grid is True, grid fills only the residual
        - price and GHG caps are not yet applied
        """
        hours = len(rese_power_df)

        if not self.config.get("integrate_grid", False):
            self.grid_stream_kW = np.zeros(hours)
            return self.grid_stream_kW

        if self.electrolyser_model is None:
            raise ValueError("Electrolyser must be configured before building grid stream.")

        target_input_kW = self.electrolyser_model.get_actual_input_capacity_kW()
        non_grid_total_kW = rese_power_df.sum(axis=1).to_numpy(dtype=float)

        grid_power_kW = np.maximum(target_input_kW - non_grid_total_kW, 0.0)

        self.grid_stream_kW = grid_power_kW
        return self.grid_stream_kW

    def build_power_df_for_electrolyser(self):
        rese_power_df = self.build_rese_power_df()
        grid_stream_kW = self.build_grid_stream(rese_power_df)

        power_df = rese_power_df.copy()

        if self.config.get("integrate_grid", False):
            power_df["grid"] = grid_stream_kW

        self.power_df = power_df
        return self.power_df

    def run_electrolyser(self):
        if self.electrolyser_model is None:
            self.setup_electrolyser()

        power_df = self.build_power_df_for_electrolyser()
        self.electrolyser_results = self.electrolyser_model.evaluate(power_df=power_df)

        return self.electrolyser_results

    def build_storage_config(self):
        """
        Build storage config by combining user-provided storage inputs
        with internally available upstream electrolyser outputs.
        """
        if not self.electrolyser_results:
            raise ValueError("Electrolyser results must exist before building storage config.")

        storage_config = dict(self.config.get("storage", {}))

        if "hourly_production_kgph" not in storage_config:
            storage_config["hourly_production_kgph"] = np.asarray(
                self.electrolyser_results["hourly"]["H2_kg"], dtype=float
            )

        if "electro_capacity" not in storage_config:
            storage_config["electro_capacity"] = self.electrolyser_model.electro_capacity

        if "avg_sec_electrolyser" not in storage_config:
            storage_config["avg_sec_electrolyser"] = self.electrolyser_model.avg_sec_electrolyser

        return storage_config

    def run_storage(self):
        """
        Run storage using:
        - user-provided storage config
        - hourly electrolyser H2 production
        - internally available electrolyser parameters
        """
        storage_config = self.build_storage_config()

        self.storage_model = HydrogenStorage()
        self.storage_model.configure(config=storage_config)
        self.storage_results = self.storage_model.hourly_analysis()

        return self.storage_results

    def build_transport_config(self):
        """
        Build transport config by combining user-provided transport inputs
        with internally available upstream values.
        """
        transport_config = dict(self.config.get("transport", {}))

        # Inject P0 from electrolyser outlet pressure if not provided
        if "P0_bar" not in transport_config:
            transport_config["P0_bar"] = self.electrolyser_model.outlet_pressure

        # Inject P1 from storage pressure if not provided
        if "P1_bar" not in transport_config:
            transport_config["P1_bar"] = self.storage_model.pout_bar

        # Inject Q2 from upstream hourly hydrogen flow if not provided
        if "Q2_kgph" not in transport_config:
            if self.storage_results:
                supply_tph = np.asarray(self.storage_results["supply_tph"], dtype=float)
                transport_config["Q2_kgph"] = float(np.mean(supply_tph * 1000.0))
            else:
                hourly_h2_kg = np.asarray(self.electrolyser_results["hourly"]["H2_kg"], dtype=float)
                transport_config["Q2_kgph"] = float(np.mean(hourly_h2_kg))

        # Inject Q1 if not provided
        if "Q1_kgph" not in transport_config:
            if self.storage_results:
                prod_kgph = np.asarray(self.storage_results["hourly_production_kgph"], dtype=float)
                transport_config["Q1_kgph"] = float(np.max(prod_kgph))
            else:
                hourly_h2_kg = np.asarray(self.electrolyser_results["hourly"]["H2_kg"], dtype=float)
                transport_config["Q1_kgph"] = float(np.max(hourly_h2_kg))

        return transport_config

    def run_transport(self):
        """
        Run truck transport using:
        - user-provided transport config
        - electrolyser outlet pressure
        - storage pressure
        - upstream hydrogen flow
        """
        transport_config = self.build_transport_config()

        self.transport_model = HydrogenTruckTransport()
        self.transport_model.configure(config=transport_config)
        self.transport_results = self.transport_model.evaluate()

        return self.transport_results
    
    def _get_annual_h2_for_finance(self):
        """
        Get annual hydrogen denominator for discounting and LCOH.

        Priority:
        1. transport total annual H2
        2. storage cumulative supply
        3. electrolyser total H2
        """
        if self.transport_results:
            val = float(self.transport_results.get("total_annual_h2_kg", 0.0))
            if val > 0:
                return val

        if self.storage_results:
            cum_supply_t = np.asarray(
                self.storage_results.get("cumulative_supply_t", np.array([])),
                dtype=float
            )
            if cum_supply_t.size > 0:
                return float(cum_supply_t[-1] * 1000.0)

        if self.electrolyser_results:
            return float(self.electrolyser_results["totals"].get("H2_kg", 0.0))

        return 0.0

    def build_cost_breakdown(self):
        """
        Build CAPEX and OPEX breakdown for:
        - RESE
        - Electrolyser + compressor/liquefier combined CAPEX block
        - Storage
        - Transport

        CAPEX adjustment logic:
        x = electrolyser base CAPEX
        y = compressor/liquefier base CAPEX

        adjusted_xy_capex =
            EMU cost
            + interconnection cost
            + engineering cost
            + 1.5652 * ((electrolyser_capacity * 1000)^-0.154) * (x + y)

        IMPORTANT:
        x+y is NOT added again separately, to avoid double counting.
        """
        finance_cfg = self.config.get("finance", {})

        # ---------------- RESE ----------------
        rese_capex = 0.0
        rese_opex = 0.0
        for _, rese_result in self.rese_results.items():
            rese_capex += float(rese_result.get("capex", 0.0))
            rese_opex += float(rese_result.get("opex", 0.0))

        # ---------------- Electrolyser ----------------
        elec_totals = self.electrolyser_results.get("totals", {})
        electrolyser_base_capex = float(elec_totals.get("capex", 0.0))
        electrolyser_opex = float(elec_totals.get("opex", 0.0))

        # ---------------- Storage split ----------------
        storage_total_capex = float(self.storage_results.get("total_storage_capex", 0.0))
        storage_total_opex = float(self.storage_results.get("total_storage_opex", 0.0))
        compressor_liquefier_capex = float(self.storage_results.get("total_compressor_capex", 0.0))

        hourly_prod_kgph = np.asarray(
            self.storage_results.get("hourly_production_kgph", np.array([])),
            dtype=float
        )
        annual_prod_kg = float(np.sum(hourly_prod_kgph)) if hourly_prod_kgph.size > 0 else 0.0

        storage_method = self.storage_model.storage_method
        energy_cost = float(self.storage_model.energy_cost)

        if storage_method == "Liquid H2":
            process_energy_opex = float(self.storage_model.liq_storage_sec) * energy_cost * annual_prod_kg
        else:
            process_energy_opex = float(self.storage_model.sec_compressor) * energy_cost * annual_prod_kg

        # compressor/liquefier opex = 2% fixed + process energy term
        compressor_liquefier_fixed_opex = 0.02 * compressor_liquefier_capex
        compressor_liquefier_opex = compressor_liquefier_fixed_opex + process_energy_opex

        # storage capex excluding compressor/liquefier capex
        if self.storage_model.com_liq_included:
            storage_capex = max(storage_total_capex - compressor_liquefier_capex, 0.0)
        else:
            storage_capex = storage_total_capex

        # storage opex excluding compressor/liquefier opex
        storage_opex = max(storage_total_opex - compressor_liquefier_opex, 0.0)

        # ---------------- Transport ----------------
        transport_capex = float(self.transport_results.get("truck_fleet_capex", 0.0))
        transport_opex = float(self.transport_results.get("truck_fleet_opex", 0.0))

        # ---------------- Adjusted electrolyser + compressor/liquefier block ----------------
        x = electrolyser_base_capex
        y = compressor_liquefier_capex
        xy = x + y

        energy_management_factor = float(finance_cfg.get("energy_management_factor", 0.10))
        interconnection_factor = float(finance_cfg.get("interconnection_factor", 0.20))
        engineering_factor = float(finance_cfg.get("engineering_factor", 0.15))

        electro_capacity_kw = float(self.electrolyser_model.electro_capacity) * 1000.0

        if electro_capacity_kw > 0:
            installed_xy_factor = 1.5652 * (electro_capacity_kw ** (-0.154))
        else:
            installed_xy_factor = 0.0

        emu_cost = energy_management_factor * xy
        interconnection_cost = interconnection_factor * xy
        engineering_cost = engineering_factor * xy
        installed_xy_cost = installed_xy_factor * xy

        adjusted_xy_capex = (
            emu_cost
            + interconnection_cost
            + engineering_cost
            + installed_xy_cost
        )

        # ---------------- Totals ----------------
        total_capex = (
            rese_capex
            + adjusted_xy_capex
            + storage_capex
            + transport_capex
        )

        total_opex = (
            rese_opex
            + electrolyser_opex
            + compressor_liquefier_opex
            + storage_opex
            + transport_opex
        )

        annual_h2_kg = self._get_annual_h2_for_finance()

        breakdown = {
            "capex": {
                "rese": rese_capex,
                "electrolyser_plus_compressor_liquefier": adjusted_xy_capex,
                "storage": storage_capex,
                "transport": transport_capex,
            },
            "capex_sub_breakdown": {
                "electrolyser_base_capex_x": x,
                "compressor_liquefier_base_capex_y": y,
                "xy_base_capex": xy,
                "emu_cost": emu_cost,
                "interconnection_cost": interconnection_cost,
                "engineering_cost": engineering_cost,
                "installed_xy_cost": installed_xy_cost,
                "installed_xy_factor": installed_xy_factor,
            },
            "opex": {
                "rese": rese_opex,
                "electrolyser": electrolyser_opex,
                "compressor_liquefier": compressor_liquefier_opex,
                "storage": storage_opex,
                "transport": transport_opex,
            },
            "totals": {
                "total_capex": total_capex,
                "total_opex": total_opex,
                "annual_h2_kg": annual_h2_kg,
            }
        }

        self.finance_results = breakdown
        return breakdown

    def _discount_single_cost_item(self, initial_value=0.0, annual_value=0.0):
        """
        Discount one cost item using the generic DiscountingModel.
        """
        finance_cfg = self.config.get("finance", {})

        model = DiscountingModel()
        model.configure({
            "discount_rate": finance_cfg.get("discount_rate", 0.06),
            "construction_years": finance_cfg.get("construction_years", 1),
            "project_life_years": finance_cfg.get("project_life_years", 20),
            "initial_value": float(initial_value),
            "annual_value": float(annual_value),
            "additional_values": {},
            "decommissioning_fraction": finance_cfg.get("decommissioning_fraction", 0.0),
        })
        return model.evaluate()

    def _discount_hydrogen(self, annual_h2_kg):
        """
        Discount annual hydrogen denominator.
        No decommissioning is applied to hydrogen.
        """
        finance_cfg = self.config.get("finance", {})

        model = DiscountingModel()
        model.configure({
            "discount_rate": finance_cfg.get("discount_rate", 0.06),
            "construction_years": finance_cfg.get("construction_years", 1),
            "project_life_years": finance_cfg.get("project_life_years", 20),
            "initial_value": 0.0,
            "annual_value": float(annual_h2_kg),
            "additional_values": {},
            "decommissioning_fraction": 0.0,
        })
        return model.evaluate()

    def run_finance(self):
        """
        Build total and individual discounted costs, then calculate total and individual LCOH.
        """
        breakdown = self.build_cost_breakdown()

        capex_items = breakdown["capex"]
        opex_items = breakdown["opex"]
        annual_h2_kg = breakdown["totals"]["annual_h2_kg"]

        # ---------------- Discount hydrogen ----------------
        h2_discounting = self._discount_hydrogen(annual_h2_kg)
        discounted_h2 = float(h2_discounting["total_present_value"])

        if discounted_h2 <= 0:
            raise ValueError("Discounted hydrogen must be greater than zero for LCOH calculation.")

        # ---------------- Discount CAPEX items ----------------
        discounted_capex = {}
        for name, value in capex_items.items():
            discounted_capex[name] = self._discount_single_cost_item(
                initial_value=value,
                annual_value=0.0
            )

        # ---------------- Discount OPEX items ----------------
        discounted_opex = {}
        for name, value in opex_items.items():
            discounted_opex[name] = self._discount_single_cost_item(
                initial_value=0.0,
                annual_value=value
            )

        # ---------------- Total discounted cost ----------------
        total_discounted_capex = sum(
            float(res["total_present_value"]) for res in discounted_capex.values()
        )
        total_discounted_opex = sum(
            float(res["total_present_value"]) for res in discounted_opex.values()
        )
        total_discounted_cost = total_discounted_capex + total_discounted_opex

        # ---------------- Total LCOH ----------------
        total_lcoh_model = LevelizedCostModel()
        total_lcoh_model.configure({
            "discounted_numerator_total": total_discounted_cost,
            "discounted_denominator_total": discounted_h2,
        })
        total_lcoh_results = total_lcoh_model.evaluate()

        # ---------------- Individual LCOH ----------------
        individual_lcoh = {
            "capex": {},
            "opex": {},
            "combined": {}
        }

        # CAPEX LCOH
        for name, res in discounted_capex.items():
            lc_model = LevelizedCostModel()
            lc_model.configure({
                "discounted_numerator_total": float(res["total_present_value"]),
                "discounted_denominator_total": discounted_h2,
            })
            individual_lcoh["capex"][name] = lc_model.evaluate()["levelized_cost"]

        # OPEX LCOH
        for name, res in discounted_opex.items():
            lc_model = LevelizedCostModel()
            lc_model.configure({
                "discounted_numerator_total": float(res["total_present_value"]),
                "discounted_denominator_total": discounted_h2,
            })
            individual_lcoh["opex"][name] = lc_model.evaluate()["levelized_cost"]

        # Combined CAPEX + OPEX by component
        combined_components = ["rese", "storage", "transport"]

        for name in combined_components:
            capex_val = float(discounted_capex.get(name, {}).get("total_present_value", 0.0))
            opex_val = float(discounted_opex.get(name, {}).get("total_present_value", 0.0))

            lc_model = LevelizedCostModel()
            lc_model.configure({
                "discounted_numerator_total": capex_val + opex_val,
                "discounted_denominator_total": discounted_h2,
            })
            individual_lcoh["combined"][name] = lc_model.evaluate()["levelized_cost"]

        # Combined block for electrolyser + compressor/liquefier
        block_capex = float(
            discounted_capex["electrolyser_plus_compressor_liquefier"]["total_present_value"]
        )
        block_opex = (
            float(discounted_opex["electrolyser"]["total_present_value"])
            + float(discounted_opex["compressor_liquefier"]["total_present_value"])
        )

        lc_model = LevelizedCostModel()
        lc_model.configure({
            "discounted_numerator_total": block_capex + block_opex,
            "discounted_denominator_total": discounted_h2,
        })
        individual_lcoh["combined"]["electrolyser_plus_compressor_liquefier"] = lc_model.evaluate()["levelized_cost"]

        self.discounting_results = {
            "capex": discounted_capex,
            "opex": discounted_opex,
            "hydrogen": h2_discounting,
            "discounted_total_capex": total_discounted_capex,
            "discounted_total_opex": total_discounted_opex,
            "discounted_total_cost": total_discounted_cost,
            "discounted_total_h2": discounted_h2,
        }

        self.levelized_cost_results = {
            "total_lcoh": total_lcoh_results["levelized_cost"],
            "individual_lcoh": individual_lcoh,
        }

        return {
            "finance_breakdown": self.finance_results,
            "discounting_results": self.discounting_results,
            "levelized_cost_results": self.levelized_cost_results,
        }
    
    def check_annual_h2_balance(self):
        """
        Check whether annual hydrogen production/supply is sufficient
        to meet annual demand and return a written message.
        """

        # Annual demand from storage input
        annual_demand_kg = 0.0
        if self.storage_results:
            demand_kgph = np.asarray(
                self.storage_results.get("hourly_demand_kgph", np.array([])),
                dtype=float
            )
            if demand_kgph.size > 0:
                annual_demand_kg = float(np.sum(demand_kgph))

        # Prefer final annual supply if available
        annual_supply_kg = 0.0
        if self.transport_results:
            annual_supply_kg = float(self.transport_results.get("total_annual_h2_kg", 0.0))

        if annual_supply_kg <= 0 and self.storage_results:
            cumulative_supply_t = np.asarray(
                self.storage_results.get("cumulative_supply_t", np.array([])),
                dtype=float
            )
            if cumulative_supply_t.size > 0:
                annual_supply_kg = float(cumulative_supply_t[-1] * 1000.0)

        # Also track electrolyser production for reporting
        annual_production_kg = 0.0
        if self.electrolyser_results:
            annual_production_kg = float(
                self.electrolyser_results.get("totals", {}).get("H2_kg", 0.0)
            )

        # Decide sufficiency using final annual supply if available,
        # otherwise fall back to annual production
        reference_kg = annual_supply_kg if annual_supply_kg > 0 else annual_production_kg
        surplus_deficit_kg = reference_kg - annual_demand_kg
        is_sufficient = reference_kg >= annual_demand_kg

        if is_sufficient:
            message = (
                f"Annual hydrogen supply is sufficient. "
                f"Available = {reference_kg:,.2f} kg/year, "
                f"demand = {annual_demand_kg:,.2f} kg/year, "
                f"surplus = {surplus_deficit_kg:,.2f} kg/year."
            )
        else:
            message = (
                f"Annual hydrogen supply is not sufficient. "
                f"Available = {reference_kg:,.2f} kg/year, "
                f"demand = {annual_demand_kg:,.2f} kg/year, "
                f"deficit = {abs(surplus_deficit_kg):,.2f} kg/year."
            )

        return {
            "annual_production_kg": annual_production_kg,
            "annual_supply_kg": annual_supply_kg,
            "annual_demand_kg": annual_demand_kg,
            "reference_kg": reference_kg,
            "surplus_deficit_kg": surplus_deficit_kg,
            "is_sufficient": is_sufficient,
            "message": message,
        }
    
    def evaluate(self):
        self.validate_config()
        self.run_rese_sources()
        self.aggregate_rese_results()
        self.run_grid()
        self.setup_electrolyser()
        self.run_electrolyser()
        self.run_storage()
        self.run_transport()
        self.run_finance()
        annual_balance_results = self.check_annual_h2_balance()

        return {
            "scenario_name": self.config.get("scenario_name"),
            "rese_results": self.rese_results,
            "aggregated_results": self.aggregated_results,
            "grid_results": self.grid_results,
            "grid_summary": self.grid_summary,
            "power_df": self.power_df,
            "grid_stream_kW": self.grid_stream_kW,
            "electrolyser_results": self.electrolyser_results,
            "storage_results": self.storage_results,
            "transport_results": self.transport_results,
            "finance_results": self.finance_results,
            "discounting_results": self.discounting_results,
            "levelized_cost_results": self.levelized_cost_results,
            "annual_balance_results": annual_balance_results,
            
        }