import numpy as np
import pandas as pd

from hytea.hytea_components.rese.rese_model import RenewableElectricity
from hytea.hytea_components.grid.grid_model import Grid
from hytea.hytea_components.electrolyser.alk import ALKElectrolyser
from hytea.hytea_components.electrolyser.pem import PEMElectrolyser
from hytea.hytea_components.storage.storage import HydrogenStorage
from hytea.hytea_components.transport.truck_transport import HydrogenTruckTransport
from hytea.hytea_components.economics.discounting import DiscountingModel
from hytea.hytea_components.economics.lc import LevelizedCostModel


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
    - Economics
    """
    #================
    # 1. Initialize
    #================
    def __init__(self): #Initiating variables
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
        # Common hourly H2 supply stream used by downstream components
        self.h2_supply_kgph = np.array([])

        # No-storage demand check
        self.no_storage_h2_deficit_kgph = np.array([])
        self.no_storage_h2_surplus_kgph = np.array([])
        self.no_storage_total_h2_deficit_kg = 0.0
        self.no_storage_demand_fulfilled = True

        self.transport_model = None
        self.transport_results = {}

        self.power_df = None
        self.rese_export_streams = {}
        self.grid_stream_kW = None

        self.economics_results = {}
        self.discounting_results = {}
        self.levelized_cost_results = {}

    def configure(self, config): #Configuring the inputs for submodels
        self.config = dict(config)

    
    #=============================
    # VALIDATIONS
    #=============================

    def validate_config(self):
        if not isinstance(self.config, dict): #if the config is not  a dictionary respond with error
            raise ValueError("config must be a dictionary.")

        if "rese_sources" not in self.config: #if rese_sources is not available it returns error
            raise ValueError("config must contain 'rese_sources'.")

        if not isinstance(self.config["rese_sources"], dict): #if rese_sources not dictionary
            raise ValueError("'rese_sources' must be a dictionary of named RESE sources.")

        if len(self.config["rese_sources"]) == 0: #if rese_sources empty
            raise ValueError("'rese_sources' cannot be empty.")

        if "electrolyser" not in self.config: #electrolyser size not configured
            raise ValueError("config must contain 'electrolyser'.")

        if self.config.get("integrate_grid", False) and "grid" not in self.config: #if integrated is true the grid profile must be an input
            raise ValueError("grid config is required when integrate_grid=True.")

        """
        if "storage" not in self.config:
            raise ValueError("config must contain 'storage' for this version.")

        if "transport" not in self.config:
            raise ValueError("config must contain 'transport' for this version.")
        if "economics" not in self.config:
            raise ValueError("config must contain 'economics' for this version.")
    
    
        """

    # ==================================================================================================================================================
    # Running RESE sources model through the RESE model
    # ===================================================================================================================================================
    def run_rese_sources(self): 

        # -------------------------------------------------------------------------
        # Renewable electricity input (rese_sources)
        # -------------------------------------------------------------------------
        # This should be a dictionary where each key represents a renewable source
        # (for example: "wind", "solar"), and the value contains the configuration
        # for that source.
        #
        # Example structure:
        #
        # config["rese_sources"] = {
        #     "wind": {
        #         "csv_file": "wind_cf.csv",   # optional: time-series data (e.g. capacity factor)
        #         "installed_capacity_mw": 100,
        #         "capex_per_mw": 1200000,
        #         "opex_fraction": 0.03
        #     },
        #     "solar": {
        #         "csv_file": "solar_cf.csv",
        #         "installed_capacity_mw": 50
        #     }
        # }
        #
        # Notes:
        # - Each source is handled independently (separate model instance per source).
        # - If provided, "csv_file" is passed separately to the model (not part of main config).
        # - All other parameters are sent directly into the RenewableElectricity model.
        # - This structure allows combining multiple sources (e.g. wind + solar).
        # - Must be a dictionary (not a list), since the code loops using .items().
        # -------------------------------------------------------------------------

        self.rese_models = {}
        self.rese_results = {}

        #self.rese_models > stores the model object for each source
        #self.rese_results > stores the evaluated output for each source #
        """
        #example
        rese_results = {
            "wind": {
                "hourly_generation_kwh": pd.Series(...),   # time series
                "annual_generation_kwh": 320_000_000,
                "capacity_factor": 0.365,
                "installed_capacity_mw": 100,
                "capex": 120_000_000,
                "opex_annual": 3_600_000
            },
        """
        for source_name, source_config in self.config["rese_sources"].items():
            csv_file = source_config.get("csv_file", None)

            rese_config = dict(source_config)
            rese_config.pop("csv_file", None)

            model = RenewableElectricity()
            model.configure(config=rese_config, csv_file=csv_file)

            self.rese_models[source_name] = model
            self.rese_results[source_name] = model.evaluate()

        return self.rese_results
    
    #==============================
    # AGGREGATE RESE individual results to one
    #===============================

    def aggregate_rese_results(self): #It merges all renewable sources into one combined time series and total cost structure.

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
    
    #==========================================================================================================================================================================
    # GRID
    #==========================================================================================================================================================================
    
    #===============================================
    # build_hourly_cf_mul is only USED for grid price estimation and intensity, This is passed into the Grid model
    #===============================================
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

    #==============================
    # Running Grid Model, This will only give out price trends, purchases prices and sales prices of the grid
    #==============================

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

        #Gives out all the grid outputs here

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
    

    #=============================================================================================================================================================================
    # ELECTROLYSER
    #==============================================================================================================================================================================

    def setup_electrolyser(self): #TEST 1 completed 
            """
            Configure electrolyser based on type (ALK / PEM)
            """

            electrolyser_config = self.config.get("electrolyser", {})
            elec_type = electrolyser_config.get("type", "ALK").lower()

            if elec_type == "pem":
                self.electrolyser_model = PEMElectrolyser() # TEST completed 

            else:  # default
                self.electrolyser_model = ALKElectrolyser()

            self.electrolyser_model.configure(config=electrolyser_config)

            return self.electrolyser_model
        

    #=======================================================
    #Build the Rese dataframe required for electrolyse input from the rese_results > hourly_output_mw, as electrolyser streamwise input power 
    #========================================================

    #RESE CAP added for electricity export priority
    def build_rese_power_df(self):
        """
        Build stream-wise RESE power DataFrame in kW,
        applying electricity export priority caps if configured.
        """
        stream_power = {}

        rese_config = self.config.get("rese_sources", {})

        for source_name, result in self.rese_results.items():
            hourly_output_mw = np.asarray(result["hourly_output_mw"], dtype=float)

            source_cfg = rese_config.get(source_name, {})
            priority_export = source_cfg.get("priority_electricity_export", False)
            export_cap_mw = float(source_cfg.get("electricity_export_cap_mw", 0.0))

            if priority_export and export_cap_mw > 0:
                # --- Export stream (what goes to grid/export) ---
                export_mw = np.minimum(hourly_output_mw, export_cap_mw)
                self.rese_export_streams[source_name] = export_mw  # Export stream added

                # --- Remaining for electrolyser ---
                adjusted_output_mw = np.maximum(hourly_output_mw - export_cap_mw, 0.0)
            else:
                # No export priority
                self.rese_export_streams[source_name] = np.zeros_like(hourly_output_mw)
                adjusted_output_mw = hourly_output_mw

            stream_power[source_name] = adjusted_output_mw * 1000.0

        if not stream_power:
            raise ValueError("No RESE stream outputs available for electrolyser input.")

        return pd.DataFrame(stream_power)
    
    #============================================================================
    #Build hourly grid stream in kW as residual power required to meet
    #=============================================================================

    def build_grid_stream(self, rese_power_df):#TEST 3 COMPLETED, the peak hours in the excel is considering the time from 6-8 PM, python considers 5-7 PM so it it correct
        """
        Build hourly grid stream in kW as residual power required to meet
        the electrolyser actual input capacity, subject to user-defined
        max grid price, max grid GHG intensity, and optional peak-hour blocking.

        Logic:
        - if integrate_grid is False -> all zeros
        - if integrate_grid is True -> grid fills only the residual gap
        - grid is only allowed in hours where:
            purchase_price <= max_grid_price
            ghg_intensity <= max_grid_ghg
        - if use_grid_during_peak_hours is False, grid is blocked during peak hours
        """

        hours = len(rese_power_df)

        if not self.config.get("integrate_grid", False):
            self.grid_stream_kW = np.zeros(hours)
            return self.grid_stream_kW

        if self.electrolyser_model is None:
            raise ValueError("Electrolyser must be configured before building grid stream.")

        if not self.grid_results:
            raise ValueError("Grid results are not available. Run run_grid() before build_grid_stream().")

        grid_cfg = self.config.get("grid", {})
        max_grid_price = float(grid_cfg.get("max_grid_price", 120.0))   # €/MWh
        max_grid_ghg = float(grid_cfg.get("max_grid_ghg", 500.0))       # gCO2/kWh
        use_grid_during_peak_hours = bool(grid_cfg.get("use_grid_during_peak_hours", True))
        peak_hours = tuple(grid_cfg.get("peak_hours", (17, 18)))

        target_input_kW = self.electrolyser_model.get_actual_input_capacity_kW()
        non_grid_total_kW = rese_power_df.sum(axis=1).to_numpy(dtype=float)

        residual_kW = np.maximum(target_input_kW - non_grid_total_kW, 0.0)

        hourly_price = np.asarray(
            self.grid_results["hourly_purchase_price_trend"],
            dtype=float
        )
        hourly_ghg = np.asarray(
            self.grid_results["hourly_ghg_trend"],
            dtype=float
        )

        if len(hourly_price) != hours or len(hourly_ghg) != hours:
            raise ValueError("Grid time series length does not match RESE time series length.")

        allowed_mask = (hourly_price <= max_grid_price) & (hourly_ghg <= max_grid_ghg)

        if not use_grid_during_peak_hours:
            hour_of_day = np.arange(hours) % 24
            peak_mask = np.isin(hour_of_day, peak_hours)
            allowed_mask = allowed_mask & (~peak_mask)

        grid_power_kW = np.where(allowed_mask, residual_kW, 0.0)

        self.grid_stream_kW = grid_power_kW
        return self.grid_stream_kW
    
    #=======================================================================
    # Build the entire power stream protile including grid
    #=========================================================================

    def build_power_df_for_electrolyser(self): #TEST 4 COMPLETED but outputs depend on get_actual_input_capacity_kW
        rese_power_df = self.build_rese_power_df()
        grid_stream_kW = self.build_grid_stream(rese_power_df)

        power_df = rese_power_df.copy()

        if self.config.get("integrate_grid", False):
            power_df["grid"] = grid_stream_kW

        self.power_df = power_df
        return self.power_df
    
    #================================================================================
    # Run Electrolyser
    #=================================================================================

    def run_electrolyser(self): #TEST 5 Completed, #TEST 5.1 completed electrolyser_efficiency()
        if self.electrolyser_model is None:
            self.setup_electrolyser()

        power_df = self.build_power_df_for_electrolyser()
        self.electrolyser_results = self.electrolyser_model.evaluate(power_df=power_df)

        return self.electrolyser_results



    #=============================================================================================================================================================================================
    # STRORAGE
    #=============================================================================================================================================================================================

    def build_storage_config(self):
        """
        Build storage config by combining user-provided storage inputs
        with internally available upstream electrolyser outputs.
        """
        """
        #Ensure electrolyser has already run
        if not self.electrolyser_results:
            raise ValueError("Electrolyser results must exist before building storage config.")

        storage_config = dict(self.config.get("storage", {}))

        if "hourly_production_kgph" not in storage_config: #Inject H₂ production
            storage_config["hourly_production_kgph"] = np.asarray(
                self.electrolyser_results["hourly"]["H2_kg"], dtype=float
            )

        if "electro_capacity" not in storage_config: #electrolyser capacity ,for sizing
            storage_config["electro_capacity"] = self.electrolyser_model.electro_capacity

        if "avg_sec_electrolyser" not in storage_config: #electrolyser sec required for energy calculation
            storage_config["avg_sec_electrolyser"] = self.electrolyser_model.avg_sec_electrolyser

        return storage_config

        """
        storage_config = dict(self.config.get("storage", {}))

        # Inject system-level H2 demand into storage model
        if "hourly_demand_kgph" not in self.config:
            raise ValueError(
                "config must contain 'hourly_demand_kgph'."
            )

        storage_config["hourly_demand_kgph"] = np.asarray(
            self.config["hourly_demand_kgph"],
            dtype=float
        )

        # Inject H2 production from electrolyser
        if "hourly_production_kgph" not in storage_config:
            storage_config["hourly_production_kgph"] = np.asarray(
                self.electrolyser_results["hourly"]["H2_kg"],
                dtype=float
            )

        # Inject electrolyser capacity for storage sizing
        if "electro_capacity" not in storage_config:
            storage_config["electro_capacity"] = self.electrolyser_model.electro_capacity

        # Inject electrolyser SEC
        if "avg_sec_electrolyser" not in storage_config:
            storage_config["avg_sec_electrolyser"] = self.electrolyser_model.avg_sec_electrolyser

        return storage_config
    
    
    #=================================================
    # Run Stroage
    #=================================================

    def run_storage(self): #TEST 6 COMPLETED tested with all stroge arrays, 

        """
        TEST 6 ISSUE
        In the Excel sheet, the supply and demand do not equalize. The problem was 
        with the minimum H2 stored. Initially, this was considered to be the minimum of 
        idealized storage np.min(ideal_storage_curve_kg)/1000, but it should actually be the minimum of demand or idealized 
        storage. This ensures that, as long as storage does not go below zero, the supply 
        remains equal to the required demand. minimum_h2_stored_t = np.min(np.minimum(ideal_storage_curve_kg, demand_kgph)) / 1000
        Equalizing supply and demand can be adjusted using the fos.


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
    
    def build_h2_supply(self):
        """
        Build the common hourly hydrogen supply stream.

        If storage is enabled:
            H2 supply = storage supply

        If storage is disabled:
            H2 supply = electrolyser H2 production

        Output:
            self.h2_supply_kgph in kg/h
        """

        if self.config.get("use_storage", True):

            if not self.storage_results:
                raise ValueError(
                    "Storage results are required when use_storage=True."
                )

            supply_tph = np.asarray(
                self.storage_results["supply_tph"],
                dtype=float
            )

            self.h2_supply_kgph = supply_tph * 1000.0

        else:

            self.h2_supply_kgph = np.asarray(
                self.electrolyser_results["hourly"]["H2_kg"],
                dtype=float
            )

            self.check_h2_demand_when_no_storage()

        return self.h2_supply_kgph
    

    def check_h2_demand_when_no_storage(self):

        demand = np.asarray(
            self.config["hourly_demand_kgph"],
            dtype=float
        )

        supply = np.asarray(
            self.h2_supply_kgph,
            dtype=float
        )

        # Hourly H2 deficit
        self.no_storage_h2_deficit_kgph = np.maximum(
            demand - supply,
            0.0
        )

        # Hourly H2 surplus
        self.no_storage_h2_surplus_kgph = np.maximum(
            supply - demand,
            0.0
        )

        # Total annual deficit
        self.no_storage_total_h2_deficit_kg = float(
            np.sum(self.no_storage_h2_deficit_kgph)
        )

        # Demand fulfilment
        self.no_storage_demand_fulfilled = (
            self.no_storage_total_h2_deficit_kg <= 1e-9
        )

        if self.no_storage_demand_fulfilled:
            print("H₂ demand fulfilled.")
        else:
            print(
                f"WARNING: H₂ demand not fulfilled. "
                f"Total annual deficit = "
                f"{self.no_storage_total_h2_deficit_kg:,.2f} kg."
            )

        return {
            "no_storage_demand_fulfilled":
                self.no_storage_demand_fulfilled,

            "no_storage_total_h2_deficit_kg":
                self.no_storage_total_h2_deficit_kg,

            "no_storage_h2_deficit_kgph":
                self.no_storage_h2_deficit_kgph,

            "no_storage_h2_surplus_kgph":
                self.no_storage_h2_surplus_kgph,
        }
    #============================================================================================================================================================================================
    # TRANSPORT
    #==============================================================================================================================================================================================

    def build_transport_config(self):
        """
        Build transport config using the common H2 supply stream.

        If storage is enabled, H2 supply comes from storage.
        If storage is disabled, H2 supply comes directly from
        the electrolyser.
        """

        transport_config = dict(self.config.get("transport", {}))

        use_storage = self.config.get("use_storage", True)

        # --------------------------------------------------
        # P0: electrolyser outlet pressure
        # --------------------------------------------------
        if "P0_bar" not in transport_config:
            transport_config["P0_bar"] = (
                self.electrolyser_model.outlet_pressure
            )

        # --------------------------------------------------
        # P1: storage pressure if storage is enabled
        # Otherwise use P0 unless user explicitly provides P1
        # --------------------------------------------------
        if "P1_bar" not in transport_config:

            if use_storage:
                transport_config["P1_bar"] = (
                    self.storage_model.pout_bar
                )
            else:
                transport_config["P1_bar"] = (
                    transport_config["P0_bar"]
                )

        # --------------------------------------------------
        # Q2: average H2 supply to transport
        # --------------------------------------------------
        if "Q2_kgph" not in transport_config:

            transport_config["Q2_kgph"] = float(
                np.mean(self.h2_supply_kgph)
            )

        # --------------------------------------------------
        # Q1: maximum H2 supply to transport
        # --------------------------------------------------
        if "Q1_kgph" not in transport_config:

            transport_config["Q1_kgph"] = float(
                np.max(self.h2_supply_kgph)
            )

        return transport_config
    
    #======================================
    # Run Transport
    #======================================

    def run_transport(self): #TEST 7 completed with minor errors , Check boost_spec_capex
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
    
    #===============================
    #Validations
    #===============================
    
    def validate_energy_balance(self):
        streams = self.electrolyser_results.get("streams", {})
        totals = self.electrolyser_results.get("totals", {})

        total_from_streams = sum(
            s.get("totals", {}).get("energy_used_kWh", 0.0)
            for s in streams.values()
        )

        total_system = float(totals.get("energy_electrolysis_kWh", 0.0))

        if not np.isclose(total_from_streams, total_system, rtol=1e-5):
            raise ValueError(
                f"Energy mismatch: streams sum = {total_from_streams}, system total = {total_system}"
            )
    
    #==============================================================================================================================================================
    # ECONOMICS  
    #===============================================================================================================================================================

    # Get annual h2 delivered
    
    def _get_annual_h2_delivered_basis(self):
        """
        Get annual hydrogen denominator for discounting and LCOH.

        Priority:
        1. transport total annual H2
        2. storage cumulative supply
        3. electrolyser total H2
        """

        if self.storage_results:
            cum_supply_t = np.asarray(
                self.storage_results.get("cumulative_supply_t", np.array([])),
                dtype=float
            )
            if cum_supply_t.size > 0:
                return float(cum_supply_t[-1] * 1000.0)
            
        if self.electrolyser_results:
            return float(self.electrolyser_results["totals"].get("H2_kg", 0.0))

        if self.transport_results:
            val = float(self.transport_results.get("total_annual_h2_transported_kg", 0.0))
            if val > 0:
                return val



        return 0.0

 
    
    
    # Get annual h2 produced

    def _get_annual_h2_for_lcoh(self):
            """
            Get annual hydrogen denominator for LCOH.
            Uses only hydrogen produced by the electrolyser during the modeled period.
            This avoids counting pre-existing stored hydrogen unless its cost is also included.
            """
            if self.electrolyser_results:
                return float(self.electrolyser_results.get("totals", {}).get("H2_kg", 0.0))
            
            return 0.0
    
    
    # ==========================
    # Cost breakdown
    # =========================
    

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

    

        IMPORTANT:
        x+y is NOT added again separately, to avoid double counting.
        """
        economics_cfg = self.config.get("economics", {})


        # -------------------------------------------- RESE --------------------------------------------
        #USE STREAM WISE POWER TO GET ELECTRICITY COST BASED ON RESE_INCLUDED IN BOUNDARY CONDITION or NOT Also have user input of €/MWh for each stream
        #TEST 10 - 
        rese_capex = 0.0
        rese_opex = 0.0

        streams = self.electrolyser_results.get("streams", {})

        for source_name, source_cfg in self.config["rese_sources"].items():

            include = source_cfg.get("include_in_boundary", True)

            if not include:
                price = source_cfg.get("price_eur_per_mwh")
                if price is None:
                    raise ValueError(
                        f"RESE source '{source_name}' is outside boundary but has no price defined."
                    )

                price = float(price)

                streams = self.electrolyser_results.get("streams", {})

                energy_kWh = float(
                    streams.get(source_name, {})
                        .get("totals", {})
                        .get("energy_used_kWh", 0.0)
                )

                energy_MWh = energy_kWh / 1000.0

                rese_opex += energy_MWh * price

            else:
                rese_result = self.rese_results.get(source_name, {})

                rese_capex += float(rese_result.get("capex", 0.0))
                rese_opex += float(rese_result.get("opex", 0.0))
        
        


        # -------------------------------------------- Grid ----------------------------------------------------
        grid_opex = 0.0

        if self.config.get("integrate_grid", False):

            streams = self.electrolyser_results.get("streams", {})
            grid_stream = streams.get("grid", {})

            energy_kWh_array = grid_stream.get("energy_used_kWh", None)

            if energy_kWh_array is not None:

                energy_kWh_array = np.asarray(energy_kWh_array, dtype=float)

                grid_cfg = self.config.get("grid", {})
                use_fixed = grid_cfg.get("use_fixed_rate", False)

                # ---------------------------------
                # CASE 1: FIXED RATE
                # ---------------------------------
                if use_fixed:
                    avg_price = float(grid_cfg.get("avg_grid_price", 0.0))

                    total_energy_MWh = float(np.sum(energy_kWh_array)) / 1000.0

                    grid_opex = total_energy_MWh * avg_price

                # ---------------------------------
                # CASE 2: HOURLY PRICE
                # ---------------------------------
                else:
                    if not self.grid_results or "hourly_purchase_price_trend" not in self.grid_results:
                        raise ValueError("Hourly grid pricing requested but grid results not available")

                    price_array = np.asarray(
                        self.grid_results["hourly_purchase_price_trend"],
                        dtype=float
                    )

                    if len(price_array) != len(energy_kWh_array):
                        raise ValueError("Mismatch: grid price and energy arrays must have same length")

                    # €/MWh → €/kWh
                    price_per_kWh = price_array / 1000.0

                    grid_opex = float(np.sum(energy_kWh_array * price_per_kWh))



        # -------------------------------------------- Electrolyser --------------------------------------------
        elec_totals = self.electrolyser_results.get("totals", {})
        electrolyser_capex = float(elec_totals.get("capex", 0.0))
        electrolyser_opex = float(elec_totals.get("opex", 0.0))


        #-----------------------------------------water---------------------------------------------------------
        water_cfg = self.config.get("water", {})
        water_price = float(water_cfg.get("water_cost_eur_per_m3", 2.38))
        total_water_m3 = float(
            self.electrolyser_results.get("totals", {}).get("water_m3", 0.0)
        )

        water_opex = total_water_m3 * water_price



        # -------------------------------------------- Storage split --------------------------------------------
        storage_total_capex = float(self.storage_results.get("total_storage_capex", 0.0))
        storage_total_opex = float(self.storage_results.get("total_storage_opex", 0.0))
        compressor_liquefier_capex = float(self.storage_results.get("total_compressor_capex", 0.0))
        compressor_liquefier_opex = float(self.storage_results.get("total_compressor_opex", 0.0))



        # -------------------------------------------- Transport --------------------------------------------

        transport_capex = float(self.transport_results.get("transportation_capex", 0.0))
        transport_opex = float(self.transport_results.get("transportation_opex", 0.0))

        

        # ----------------Interconnection, Energy manangement Enginnering and Other costs----------------

        main_equipment_cost = electrolyser_capex + compressor_liquefier_capex
       
        energy_management_factor = float(economics_cfg.get("energy_management_factor", 0.10))
        interconnection_factor = float(economics_cfg.get("interconnection_factor", 0.20))
        engineering_factor = float(economics_cfg.get("engineering_factor", 0.15))

        electro_capacity_kw = float(self.electrolyser_model.electro_capacity) * 1000.0

        if electro_capacity_kw > 0:
            other_cost_factor = 1.5652 * (electro_capacity_kw ** (-0.154))
        else:
            other_cost_factor = 0.0

        emu_cost = energy_management_factor * main_equipment_cost
        interconnection_cost = interconnection_factor * main_equipment_cost
        engineering_cost = engineering_factor * main_equipment_cost
        other_cost = other_cost_factor * main_equipment_cost

        other_capex = (
            emu_cost
            + interconnection_cost
            + engineering_cost
            + other_cost

        )

        # ---------------- Totals ----------------
        total_capex = (
            rese_capex
            + electrolyser_capex 
            + compressor_liquefier_capex
            + other_capex
            + storage_total_capex
            + transport_capex
        )

        total_opex = (
            rese_opex
            + electrolyser_opex
            + grid_opex
            + compressor_liquefier_opex
            + storage_total_opex
            + transport_opex
            + water_opex
        )

        lcoh_basis = self.config.get("economics", {}).get(
            "h2_lcoh_basis",
            "produced"
        ).lower()

        if lcoh_basis == "produced":
            annual_h2_kg = self._get_annual_h2_for_lcoh()

        elif lcoh_basis == "delivered":
            annual_h2_kg = self._get_annual_h2_delivered_basis()

        else:
            raise ValueError(
                "Invalid 'h2_lcoh_basis'. "
                "Choose either 'produced' or 'delivered'."
            )

        #annual_h2_kg = self._get_annual_h2_for_lcoh() #Get annual h2 produced else if the delivered is required use _get_annual_h2_delivered_basis()

        breakdown = { #TEST 11 - PENDING
            "capex": {
                "rese": rese_capex,
                "electrolyser":electrolyser_capex,
                "grid": 0,
                "compressor_liquefier": compressor_liquefier_capex,
                "emu_cost": emu_cost,
                "interconnection_cost": interconnection_cost,
                "engineering_cost": engineering_cost,
                "other_cost": other_cost,
                "storage": storage_total_capex,
                "transport": transport_capex,
                "water":0,
            },
            "capex_sub_breakdown": {
                "electrolyser_capex": electrolyser_capex,
                "compressor_liquefier_capex": compressor_liquefier_capex,
                "main_equipment_cost": main_equipment_cost,
                "emu_cost": emu_cost,
                "interconnection_cost": interconnection_cost,
                "engineering_cost": engineering_cost,
                "other_cost": other_cost,
                "other_cost_factor": other_cost_factor,
            },
            "opex": {
                "rese": rese_opex,
                "electrolyser": electrolyser_opex,
                "grid": grid_opex,
                "compressor_liquefier": compressor_liquefier_opex,
                "emu_cost": 0,
                "interconnection_cost": 0,
                "engineering_cost": 0,
                "other_cost": 0,
                "storage": storage_total_opex,
                "transport": transport_opex,
                "water":water_opex,
                
            },
            "totals": {
                "total_capex": total_capex,
                "total_opex": total_opex,
                "annual_h2_kg": annual_h2_kg,
            }
        }

        self.economics_results = breakdown
        return breakdown
    



    # Discounting number are wrong - TEST 11
    def _discount_single_cost_item(self, initial_value=0.0, annual_value=0.0):
        """
        Discount one cost item using the generic DiscountingModel.
        """
        economics_cfg = self.config.get("economics", {})

        model = DiscountingModel()
        model.configure({
            "discount_rate": economics_cfg.get("discount_rate", 0.06),
            "construction_years": economics_cfg.get("construction_years", 1),
            "project_life_years": economics_cfg.get("project_life_years", 20),
            "initial_value": float(initial_value),
            "annual_value": float(annual_value),
            "additional_values": {},
            "decommissioning_fraction": economics_cfg.get("decommissioning_fraction", 0.05),
        })
        return model.evaluate()
    




    #This seems okay 
    def _discount_hydrogen(self, annual_h2_kg):
        """
        Discount annual hydrogen denominator.
        No decommissioning is applied to hydrogen.
        """
        economics_cfg = self.config.get("economics", {})

        model = DiscountingModel()
        model.configure({
            "discount_rate": economics_cfg.get("discount_rate", 0.06),
            "construction_years": economics_cfg.get("construction_years", 1),
            "project_life_years": economics_cfg.get("project_life_years", 20),
            "initial_value": 0.0,
            "annual_value": float(annual_h2_kg),
            "additional_values": {},
            "decommissioning_fraction": 0.0,
        })
        return model.evaluate()
    

    # 
    #======================================================
    # Run Economics
    #======================================================

    def run_economics(self):
        """
        Clean LCOH calculation framework:

        Outputs:
        - Total LCOH
        - CAPEX-only LCOH
        - OPEX-only LCOH
        - Individual CAPEX LCOH contributions
        - Individual OPEX LCOH contributions
        - Component-wise combined LCOH (CAPEX + OPEX)
        """

        breakdown = self.build_cost_breakdown()

        capex_items = breakdown["capex"]
        opex_items = breakdown["opex"]
        annual_h2_kg = breakdown["totals"]["annual_h2_kg"]

        # ============================================================
        # 1. Discount hydrogen
        # ============================================================
        h2_discount = self._discount_hydrogen(annual_h2_kg)
        total_pv_h2 = float(h2_discount["total_present_value"])

        if total_pv_h2 <= 0:
            raise ValueError("Discounted hydrogen must be > 0")

        # ============================================================
        # 2. Discount CAPEX
        # ============================================================
        total_pv_capex_breakdown = {}
        for name, value in capex_items.items():
            res = self._discount_single_cost_item(
                initial_value=value,
                annual_value=0.0
            )
            total_pv_capex_breakdown[name] = float(res["total_present_value"])

        # ============================================================
        # 3. Discount OPEX
        # ============================================================
        total_pv_opex_breakdown = {}
        for name, value in opex_items.items():
            res = self._discount_single_cost_item(
                initial_value=0.0,
                annual_value=value
            )
            total_pv_opex_breakdown[name] = float(res["total_present_value"])

        # ============================================================
        # 4. Totals
        # ============================================================
        total_pv_capex = sum(total_pv_capex_breakdown.values())
        total_pv_opex = sum(total_pv_opex_breakdown.values())
        total_pv_costs = total_pv_capex + total_pv_opex

        # ============================================================
        # 5. Total LCOH
        # ============================================================
        total_lcoh = total_pv_costs / total_pv_h2

        # ============================================================
        # 6. CAPEX vs OPEX LCOH split
        # ============================================================
        capex_lcoh = total_pv_capex / total_pv_h2
        opex_lcoh = total_pv_opex / total_pv_h2

        # ============================================================
        # 7. Individual CAPEX LCOH
        # ============================================================
        capex_lcoh_breakdown = {
            name: val / total_pv_h2
            for name, val in total_pv_capex_breakdown.items()
        }

        # ============================================================
        # 8. Individual OPEX LCOH
        # ============================================================
        opex_lcoh_breakdown = {
            name: val / total_pv_h2
            for name, val in total_pv_opex_breakdown.items()
        }

        # ============================================================
        # 9. Component-wise LCOH (CAPEX + OPEX) #TEST 11 - PENDING
        # ============================================================
        component_lcoh = {} #TEST 11 - PENDING

        # Components that exist in BOTH CAPEX and OPEX
        all_components = set(capex_items.keys()).union(set(opex_items.keys()))

        for comp in all_components:
            capex_val = total_pv_capex_breakdown.get(comp, 0.0)
            opex_val = total_pv_opex_breakdown.get(comp, 0.0)

            component_lcoh[comp] = (capex_val + opex_val) / total_pv_h2

        # ============================================================
        # 10. Store results
        # ============================================================
        self.discounting_results = {
            "total_pv_capex_breakdown": total_pv_capex_breakdown,
            "total_pv_opex_breakdown": total_pv_opex_breakdown,
            "total_pv_h2": total_pv_h2,
            "total_pv_capex": total_pv_capex,
            "total_pv_opex": total_pv_opex,
            "total_pv_costs": total_pv_costs,
        }

        self.levelized_cost_results = {
            "total_lcoh": total_lcoh,
            "capex_lcoh": capex_lcoh,
            "opex_lcoh": opex_lcoh,
            "capex_lcoh_breakdown": capex_lcoh_breakdown,
            "opex_lcoh_breakdown": opex_lcoh_breakdown,
            "component_lcoh": component_lcoh,
        }

        return {
            "economics_breakdown": breakdown,
            "discounting_results": self.discounting_results,
            "levelized_cost_results": self.levelized_cost_results,
        }
    

    # =========================================================================================
    # GHG Intensity
    # =========================================================================================

    def calculate_ghg_intensity(self):
        """
        Calculate system GHG intensity considering:
        - Grid electricity (used by electrolyser only)
        - Transport emissions

        Outputs:
        - tCO2/tH2
        - gCO2/kWh(H2)
        """

        # -------------------------
        # 1. Grid emissions
        # -------------------------
        total_grid_ghg_t = 0.0

        if self.config.get("integrate_grid", False):

            grid_energy_kWh = np.asarray(
                self.electrolyser_results
                .get("streams", {})
                .get("grid", {})
                .get("energy_used_kWh", np.zeros(8760)),
                dtype=float
            )
            # Grid GHG intensity (gCO2/kWh)
            grid_ghg_intensity = np.asarray(
                self.grid_summary.get("hourly_ghg_trend", np.zeros_like(grid_energy_kWh)),
                dtype=float
            )

            # Convert to tonnes CO2
            total_grid_ghg_t = np.sum(grid_energy_kWh * grid_ghg_intensity) / 1e6


        # -------------------------
        # 2. Transport emissions
        # -------------------------
        total_transport_ghg_t = 0.0

        if self.transport_results:
            total_transport_ghg_t = float(
                self.transport_results.get("total_ghg_per_year", 0.0)
            )


        # -------------------------
        # 3. Total emissions
        # -------------------------
        total_ghg_t = total_grid_ghg_t + total_transport_ghg_t


        # -------------------------
        # 4. Hydrogen production
        # -------------------------
        total_h2_kg = self._get_annual_h2_for_lcoh()

        if total_h2_kg <= 0:
            raise ValueError("Total H2 production is zero. Cannot compute GHG intensity.")

        total_h2_t = total_h2_kg / 1000.0


        # -------------------------
        # 5. Metrics
        # -------------------------
        ghg_t_per_tH2 = total_ghg_t / total_h2_t

        # Convert to gCO2/kWh (H2 basis)
        ghg_g_per_kWh = (ghg_t_per_tH2 / 33.333) * 1000.0


        return {
            "total_ghg_t_per_year": total_ghg_t,
            "grid_ghg_t_per_year": total_grid_ghg_t,
            "transport_ghg_t_per_year": total_transport_ghg_t,
            "ghg_t_per_tH2": ghg_t_per_tH2,
            "ghg_g_per_kWh": ghg_g_per_kWh
        }
    

    # =========================================================================================
    # CHECK for H2 Balance
    # =========================================================================================

    def check_annual_h2_balance(self):
        """
        Check whether annual hydrogen supply is sufficient
        to meet annual demand.
        """

        # --------------------------------------------------
        # H2 demand
        # --------------------------------------------------
        demand_kgph = np.asarray(
            self.config["hourly_demand_kgph"],
            dtype=float
        )

        annual_demand_kg = float(
            np.sum(demand_kgph)
        )

        # --------------------------------------------------
        # H2 production from electrolyser
        # --------------------------------------------------
        annual_production_kg = 0.0

        if self.electrolyser_results:
            annual_production_kg = float(
                self.electrolyser_results
                .get("totals", {})
                .get("H2_kg", 0.0)
            )

        # --------------------------------------------------
        # H2 supply available to downstream system
        # --------------------------------------------------
        annual_supply_kg = float(
            np.sum(self.h2_supply_kgph)
        )

        # --------------------------------------------------
        # Supply vs demand
        # --------------------------------------------------
        surplus_deficit_kg = (
            annual_supply_kg - annual_demand_kg
        )

        is_sufficient = (
            annual_supply_kg >= annual_demand_kg
        )

        if is_sufficient:
            message = (
                f"Annual hydrogen supply is sufficient. "
                f"Produced = {annual_production_kg:,.2f} kg/year, "
                f"supply = {annual_supply_kg:,.2f} kg/year, "
                f"demand = {annual_demand_kg:,.2f} kg/year, "
                f"surplus = {surplus_deficit_kg:,.2f} kg/year."
            )

        else:
            message = (
                f"Annual hydrogen supply is not sufficient. "
                f"Produced = {annual_production_kg:,.2f} kg/year, "
                f"supply = {annual_supply_kg:,.2f} kg/year, "
                f"demand = {annual_demand_kg:,.2f} kg/year, "
                f"deficit = {abs(surplus_deficit_kg):,.2f} kg/year."
            )

        return {
            "annual_production_kg": annual_production_kg,
            "annual_supply_kg": annual_supply_kg,
            "annual_demand_kg": annual_demand_kg,
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
        self.validate_energy_balance()
        # Run hydrogen storage only if enabled
        if self.config.get("use_storage", True):
            self.run_storage()
        else:
            self.storage_model = None
            self.storage_results = {}
        # Build common H2 supply stream
        self.build_h2_supply()
        self.run_transport()
        self.run_economics()
        ghg_results = self.calculate_ghg_intensity()
        annual_balance_results = self.check_annual_h2_balance()

        return {
            "scenario_name": self.config.get("scenario_name"),
            "rese_results": self.rese_results,
            "aggregated_results": self.aggregated_results,
            "grid_results": self.grid_results,
            "grid_summary": self.grid_summary,
            "ghg_results": ghg_results,
            "power_df": self.power_df,
            "grid_stream_kW": self.grid_stream_kW,
            "electrolyser_results": self.electrolyser_results,
            "storage_results": self.storage_results,
            "transport_results": self.transport_results,
            "economics_results": self.economics_results,
            "discounting_results": self.discounting_results,
            "levelized_cost_results": self.levelized_cost_results,
            "annual_balance_results": annual_balance_results,
            "no_storage_demand_fulfilled": self.no_storage_demand_fulfilled,
            "no_storage_total_h2_deficit_kg": self.no_storage_total_h2_deficit_kg,
            "no_storage_h2_deficit_kgph":self.no_storage_h2_deficit_kgph,
            "no_storage_h2_surplus_kgph":self.no_storage_h2_surplus_kgph,
            
        }