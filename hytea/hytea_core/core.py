import numpy as np
import pandas as pd

from hytea.hytea_components.rese.rese_model import RenewableElectricity
from hytea.hytea_components.grid.grid_model import Grid
from hytea.hytea_components.electrolyser.electrolyser_model import ALKElectrolyser
from hytea.hytea_components.storage.storage import HydrogenStorage
from hytea.hytea_components.transport.truck_transport import HydrogenTruckTransport


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

    def evaluate(self):
        self.validate_config()
        self.run_rese_sources()
        self.aggregate_rese_results()
        self.run_grid()
        self.setup_electrolyser()
        self.run_electrolyser()
        self.run_storage()
        self.run_transport()

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
        }