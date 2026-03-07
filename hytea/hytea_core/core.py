import numpy as np
from hytea.hytea_components.rese.rese_model import RenewableElectricity
from hytea.hytea_components.grid.grid_model import Grid


class HyTEACore:
    """
    HyTEA Core - Version 2

    Responsibilities:
    - accept simple scenario configuration
    - run multiple RESE sources
    - preserve source-wise outputs
    - aggregate combined RESE outputs
    - build hourly_cf_mul from source CF arrays
    - run Grid only if grid is integrated

    Version 2 scope:
    - RESE
    - optional Grid
    - no electrolyser
    - no storage
    - no transport
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

        if self.config.get("integrate_grid", False):
            if "grid" not in self.config:
                raise ValueError("grid config is required when integrate_grid=True.")

    def run_rese_sources(self):
        """
        Run all configured RESE sources and preserve source labels.
        """
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
        """
        Aggregate all RESE source outputs into combined system-level outputs.

        Stream-wise avg_capacity_factor is preserved in rese_results.
        At this stage, no combined avg capacity factor is calculated.
        """
        if not self.rese_results:
            self.aggregated_results = {}
            return self.aggregated_results

        hourly_output_arrays = []
        cumulative_hourly_arrays = []

        total_capex = 0.0
        total_opex = 0.0

        for source_name, result in self.rese_results.items():
            hourly_output = np.asarray(result["hourly_output_mw"], dtype=float)
            cumulative_hourly = np.asarray(result["cumulative_energy_gwh_hourly"], dtype=float)
            capex = float(result["capex"])
            opex = float(result["opex"])

            hourly_output_arrays.append(hourly_output)
            cumulative_hourly_arrays.append(cumulative_hourly)

            total_capex += capex
            total_opex += opex

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
        """
        Build hourly_cf_mul for Grid from the loaded RESE source CF arrays.

        IMPORTANT:
        The current Grid.weighted_res_e_cf() implementation expects shape:
            (n_sources, 8760)
        not:
            (8760, n_sources)

        So we stack source CF arrays row-wise.
        """
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

        hourly_cf_mul = np.vstack(cf_arrays)
        return hourly_cf_mul

    def run_grid(self):
        """
        Run Grid only if grid is integrated.
        """
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

        # simple summary values
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

    def evaluate(self):
        self.validate_config()
        self.run_rese_sources()
        self.aggregate_rese_results()
        self.run_grid()

        return {
            "scenario_name": self.config.get("scenario_name"),
            "rese_results": self.rese_results,
            "aggregated_results": self.aggregated_results,
            "grid_results": self.grid_results,
            "grid_summary": self.grid_summary,
        }