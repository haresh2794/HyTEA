import numpy as np
import yaml


class HydrogenStorage:
    """
    Hydrogen storage model with full hourly outputs in tonnes and kg.

    """

    def __init__(self):
        # ---------------- Storage Defaults ----------------
        self.storage_defaults = {
            "Compressed Tanks": {"pressure_bar": 300, "temperature_C": 25, "a": 0, "b": 0.370511713, "com_liq_included":False},
            "Salt cavern":   {"pressure_bar": 200, "temperature_C": 25, "a": 0.195420825585994, "b": 0.125411409869413, "com_liq_included":True},
            "Lined rock cavern":{"pressure_bar": 150, "temperature_C": 25, "a": 0.126197258645584, "b": 0.200511784228375, "com_liq_included":True},
            "Liquid H2":        {"pressure_bar": 1,   "temperature_C": -253, "a": None, "b": None, "com_liq_included":False},
        }

        # ---------------- Inputs ----------------
        self.storage_method = None
        self.storage_capacity_tonnes = None  # optional override (tonnes) when storage_sizing_option="Tonnes"
        self.custom_specific_capex = None  # €/kg (optional override)
        self.capex_a = None
        self.capex_b = None
        self.electro_capacity = None
        self.avg_sec_electrolyser = None

        self.max_charge_rate_kgph = None     # kg/h
        self.max_discharge_rate_kgph = None  # kg/h

        self.storage_specific_capex = None
        self.boil_off_fraction_per_year = None  # fraction/year

        self.hourly_demand_kgph = None
        self.hourly_production_kgph = None
        self.fos = None
        self.com_liq_included = None
        self.p_in_bar = None
        self.energy_cost = None
        self.pout_bar = None
        self.liq_storage_sec = None
        self.sec_compressor = None
        self.total_storage_capex = None
        self.total_storage_opex = None
        self.outputs = None

        # Starting storage policy
        self.starting_storage_option = "Full storage"  # "Full storage" or "Hours"
        self.starting_storage_hours = 0.0              # only used if option == "Hours"
        # Starting storage
        self.starting_h2_storage_t = None  # None = start with full storage capacity

        # Storage sizing policy (capacity)
        self.storage_sizing_option = "Full storage"    # "Full storage" | "Hours" | "Tonnes"
        self.storage_hours = 0.0                       # used if storage_sizing_option == "Hours"

        # ---------------- Summary ----------------
        self.required_initial_storage_kg = None  # kg (buffer)
        self.required_capacity_kg = None         # kg (sized)

        # ---------------- Hourly Outputs (rates, tph) ----------------
        self.hourly_demand_tph = None
        self.hourly_production_tph = None
        self.h2_additions_tph = None                 # production - demand (tph)
        self.production_to_storage_tph = None
        self.production_to_demand_tph = None
        self.demand_shortfall_tph = None
        self.storage_to_demand_tph = None
        self.supply_tph = None
        self.storage_inflows_tph = None              # same as production_to_storage_tph
        self.storage_outflows_tph = None             # same as storage_to_demand_tph

        # ---------------- Hourly Outputs (inventories, tonnes) ----------------
        self.starting_storage_t = None
        self.actual_storage_t = None
        self.ideal_storage_t = None
        self.storage_no_init_t = None

        # ---------------- Hourly Outputs (kg versions where useful) ----------------
        self.h2_additions_kgph = None
        self.storage_no_init_kg = None
        self.actual_storage_kg = None
        self.boil_off_kg = None
        self._lookup_boost_sec_table = {
                            0:  (0.00433, 4.13),
                            15: (0.00367, 1.72),
                            30: (0.00333, 1.13),
                            60: (0.00300, 0.68)
                        }

        # ---------------- Hourly Outputs (loss, tonnes per step) ----------------
        self.boil_off_t = None  # tonnes lost during the hour

        # ---------------- Cumulatives (tonnes) ----------------
        self.cumulative_production_t = None
        self.cumulative_demand_t = None
        self.cumulative_supply_t = None
        self.compressor_specific_capex =None
        self.total_compressor_capex = None



    #---Derivations--------
    def _calc_compressor_spec_capex(self, pout_bar, Q2_kgph):
        """
        Compressor CAPEX for compression from p_in_bar to pout_bar
        """
        table = {
            0:  (95.164748, 126.052692, -0.340193, -0.340175),
            15: (68.951461, 79.237823,  -0.339972, -0.340180),
            30: (64.657575, 77.772504,  -0.339985, -0.339835),
            60: (61.065051, 68.250099,  -0.340003, -0.339968),
        }

        pin = self.p_in_bar
        Q = Q2_kgph


        if pin not in table:
            raise ValueError("P0_bar must be one of: 0, 15, 30, 60 barg")

        A200, A500, B200, B500 = table[pin]

        f = (pout_bar - 200) / (500 - 200)

        A = A200 + f * (A500 - A200)
        B = B200 + f * (B500 - B200)

        return 1000 * A * Q**B



    def calc_sec_boost(self, P_target):
        """
        Specific compression energy (kWh/kg) from p_in_bar to P_target.
        """
        if self.p_in_bar not in self._lookup_boost_sec_table:
            raise ValueError("p_in_bar must be one of: 0, 15, 30, 60 barg")

        slope, intercept = self._lookup_boost_sec_table[self.p_in_bar]

        if P_target <= self.p_in_bar:
            return 0.0

        return slope * (P_target - self.p_in_bar) + intercept

    def _capex_liquid_h2(self, capacity_kg):
        capacity_tonnes = capacity_kg / 1000.0
        lh2_expr = (30000000.0 * (capacity_tonnes ** 0.67)) / (capacity_kg * 1000.0)
        return max(22.0, lh2_expr)


    def _capex_ab_scaling(self, capacity_kg):
        if self.capex_a is None or self.capex_b is None:
            raise ValueError(f"No CAPEX parameters defined for storage type '{self.storage_method}'")
        return 0.9 * 10 ** (
            1.0 / (self.capex_a * np.log10(capacity_kg) + self.capex_b))
    
    def _default_electro_capacity(self):
        return 4  # MW   
    
    def _default_avg_sec_electrolyser(self, capacity):
        """
        Average electrolyser specific energy consumption (SEC)
        y = c * x^b
        """
        c = 0.018577706
        b = -0.028315417

        return (1/c) * (capacity ** b)
    
    def _default_liq_storage_sec(self):
            liq_h2_initial_sizing = 1000*self.electro_capacity*(1+(10/self.avg_sec_electrolyser))/(self.avg_sec_electrolyser+10)
            x = min(25.495937660557*liq_h2_initial_sizing**(-0.116967960344646),0.45*33.3)

            return x

    # -----------------------------------------------------
    # CONFIGURATION
    # -----------------------------------------------------
    def configure(self, config=None, config_file=None):
        if config is not None:
            cfg = config
        elif config_file is not None:
            with open(config_file, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        else:
            cfg = {}

        self.storage_method = cfg.get("storage_method", "Compressed Tanks")
        if self.storage_method not in self.storage_defaults:
            raise ValueError(f"Unknown storage_method: {self.storage_method}")

        defaults = self.storage_defaults[self.storage_method]

        self.capex_a = defaults.get("a", None)
        self.capex_b = defaults.get("b", None)
        self.custom_specific_capex = cfg.get("custom_specific_capex", None)
        if self.custom_specific_capex is not None:
            self.custom_specific_capex = float(self.custom_specific_capex)


        # Storage sizing (capacity)
        self.storage_sizing_option = cfg.get("storage_sizing_option", "Full storage")  # Full storage | Hours | Tonnes
        self.storage_hours = float(cfg.get("storage_hours", 0.0))                      # if Hours
        cap_t = cfg.get("storage_capacity_tonnes", None)                               # if Tonnes
        self.storage_capacity_tonnes = None if cap_t is None else float(cap_t)
        self.fos = float(cfg.get("fos", 1.1))
        self.p_in_bar = cfg.get("p_in_bar", 15)
        self.energy_cost = cfg.get("energy_cost", 0.10) # €/kWh
        self.pout_bar = cfg.get("pout_bar", defaults["pressure_bar"])

        self.com_liq_included = cfg.get("com_liq_included", defaults["com_liq_included"])

        # Optional: allow starting storage policy to be configured too
        #self.starting_storage_option = cfg.get("starting_storage_option", "Full storage")
        #self.starting_storage_hours = float(cfg.get("starting_storage_hours", 0.0))
        # Optional: actual starting storage in tonnes
        self.starting_h2_storage_t = cfg.get("starting_h2_storage_t", None)

        if self.starting_h2_storage_t is not None:
            self.starting_h2_storage_t = float(self.starting_h2_storage_t)

        self.sec_compressor = cfg.get("sec_compressor", self.calc_sec_boost(self.pout_bar))
     

        # Rate limits (default infinite if not provided)
        self.max_charge_rate_kgph = cfg.get("max_charge_rate_kgph", np.inf)
        self.max_discharge_rate_kgph = cfg.get("max_discharge_rate_kgph", np.inf)

        # Boil-off: fraction per year 
        if self.storage_method == "Liquid H2":
            self.boil_off_fraction_per_year = float(cfg.get("boil_off_fraction_per_year", 0.01))
        else:
            self.boil_off_fraction_per_year = float(cfg.get("boil_off_fraction_per_year", 0.0))

        self.hourly_demand_kgph = np.array(cfg.get("hourly_demand_kgph", np.zeros(8760)), dtype=float)
        self.hourly_production_kgph = np.array(cfg.get("hourly_production_kgph", np.zeros(8760)), dtype=float)

        if self.hourly_demand_kgph.shape != self.hourly_production_kgph.shape:
            raise ValueError(
                f"hourly_demand_kgph and hourly_production_kgph must be same length. "
                f"Got {len(self.hourly_demand_kgph)} vs {len(self.hourly_production_kgph)}."
            )
        
        self.electro_capacity = cfg.get(
            'electro_capacity',
            self._default_electro_capacity()
        )

        self.avg_sec_electrolyser = cfg.get(
            'avg_sec_electrolyser',
            self._default_avg_sec_electrolyser(self.electro_capacity)
        )

        if self.storage_method == "Liquid H2":
            self.liq_storage_sec = cfg.get("liq_storage_sec", self._default_liq_storage_sec())

    # -----------------------------------------------------
    # HOURLY ANALYSIS 
    # -----------------------------------------------------
    def hourly_analysis(self):
        if self.hourly_demand_kgph is None or self.hourly_production_kgph is None:
            raise ValueError("Run configure() first.")

        demand_kgph = self.hourly_demand_kgph
        prod_kgph = self.hourly_production_kgph
        n = len(demand_kgph)

        fos = float(self.fos) if self.fos is not None else 1.1

        # ---------- Sizing (kg) ----------
        additions_kg = prod_kgph - demand_kgph            # kg per hour-step 
        cumulative_additions_kg = np.cumsum(additions_kg) # kg
        prod_tph = prod_kgph / 1000.0
        cumulative_production_t = np.cumsum(prod_tph)

        self.required_initial_storage_kg = max(
            0.0,
            -float(np.min(cumulative_additions_kg)) * fos
        )

        ideal_storage_curve_kg = (
            self.required_initial_storage_kg + cumulative_additions_kg
        )

        self.required_capacity_kg = max(
            self.required_initial_storage_kg,
            float(np.max(ideal_storage_curve_kg))
        )

        # ---------- Capacimiytty selection ----------
        opt = str(self.storage_sizing_option).strip().lower()

        if opt in ["full storage", "full", "auto"]:
            capacity_kg = self.required_capacity_kg

        elif opt in ["hours", "hour"]:
            if self.storage_hours <= 0:
                raise ValueError("storage_sizing_option='Hours' needs storage_hours > 0")
            capacity_kg = self.storage_hours * demand_kgph[0] * fos  # kg/h * h = kg

        elif opt in ["tonnes", "tonne", "t"]:
            if self.storage_capacity_tonnes is None:
                raise ValueError("storage_sizing_option='Tonnes' needs storage_capacity_tonnes")
            capacity_kg = self.storage_capacity_tonnes * 1000.0

        else:
            raise ValueError(f"Unknown storage_sizing_option: {self.storage_sizing_option}")
        

        if capacity_kg < self.required_capacity_kg:

            if self.required_initial_storage_kg > 0:
                warning_message = (
                    f"Warning: selected storage capacity ({capacity_kg:.2f} kg) "
                    f"is smaller than the required storage capacity "
                    f"({self.required_capacity_kg:.2f} kg). "
                    f"A storage capacity of at least "
                    f"{self.required_capacity_kg:.2f} kg "
                    f"({self.required_capacity_kg / 1000:.2f} tonnes) "
                    f"would be required to fully satisfy the demand."
                )

            else:
                warning_message = (
                    f"Warning: selected storage capacity ({capacity_kg:.2f} kg) "
                    f"is smaller than the required storage capacity "
                    f"({self.required_capacity_kg:.2f} kg). "
                    f"The selected storage "
                    f"capacity is insufficient to store the full production surplus. "
                    f"Some surplus hydrogen may therefore be curtailed. "
                    f"A storage capacity of at least "
                    f"{self.required_capacity_kg:.2f} kg "
                    f"({self.required_capacity_kg / 1000:.2f} tonnes) "
                    f"would be required to store the full surplus."
                )

            print(warning_message)

        else:
            warning_message = None


        
        cap_t = capacity_kg / 1000.0

        
        if capacity_kg <= 0:

            # No physical storage system
            self.storage_specific_capex = 0.0
            self.total_storage_capex = 0.0

            self.compressor_specific_capex = 0.0
            self.total_compressor_capex = 0.0

        else:
            # ----------spec Storage CAPEX calculation ----------
            if self.custom_specific_capex is not None:
                self.storage_specific_capex = self.custom_specific_capex

            elif self.storage_method == "Liquid H2":
                self.storage_specific_capex = self._capex_liquid_h2(capacity_kg)

            else:
                self.storage_specific_capex = self._capex_ab_scaling(capacity_kg)

            
            """
            # ----------Total Storage CAPEX calculation ----------

            if self.com_liq_included:
                self.total_storage_capex = self.storage_specific_capex * capacity_kg - self.total_compressor_capex
            else:
                self.total_storage_capex = self.storage_specific_capex * capacity_kg

            """
        """
        #------------Storage OPEX calculation--------------
        if self.storage_method == "Liquid H2":

            #calculated differently
            self.total_storage_opex = self.total_storage_capex*0.02 #+ self.liq_storage_sec*self.energy_cost*sum(prod_kgph)
            
        else:
            self.total_storage_opex = self.total_storage_capex*0.02 #+ self.sec_compressor*self.energy_cost*sum(prod_kgph)
        
        """



        
        req_init_t = self.required_initial_storage_kg / 1000.0
        
        #minimum_h2_stored_t = np.min(np.minimum(ideal_storage_curve_kg, demand_kgph)) / 1000

        """
        TEST 6 ISSUE
        In the Excel sheet, the supply and demand do not equalize. The problem was 
        with the minimum H2 stored. Initially, this was considered to be the minimum of 
        idealized storage np.min(ideal_storage_curve_kg)/1000, but it should actually be the minimum of demand or idealized 
        storage. This ensures that, as long as storage does not go below zero, the supply 
        remains equal to the required demand. minimum_h2_stored_t = np.min(np.minimum(ideal_storage_curve_kg, demand_kgph)) / 1000
        Equalizing supply and demand can be adjusted using the fos.
        """
        


        # ---------- Convert to rates (tph) ----------
        demand_tph = demand_kgph / 1000.0
       
        additions_tph = (prod_kgph - demand_kgph) / 1000.0

        boil_frac_per_hour = (self.boil_off_fraction_per_year / 8760.0) if self.boil_off_fraction_per_year is not None else 0.0

        # ---------- Allocate arrays ----------
        starting_storage_t = np.zeros(n)
        actual_storage_t = np.zeros(n)

        prod_to_storage_tph = np.zeros(n)
        prod_to_demand_tph = np.zeros(n)
        demand_remaining_tph = np.zeros(n)
        shortfall_tph = np.zeros(n)
        storage_to_demand_tph = np.zeros(n)
        supply_tph = np.zeros(n)

        boil_off_t = np.zeros(n)
        

        
        # ---------- Starting storage t=0 ----------
        """
        start_opt = str(self.starting_storage_option).strip().lower()

        if start_opt == "full storage":
            # Start with the actual selected physical storage capacity
            starting_storage_t[0] = cap_t

        else:
            # Hours option
            starting_storage_t[0] = (
                float(self.starting_storage_hours)
                * demand_tph[0]
                * fos
            )

        """
        # ---------- Starting storage t=0 ----------
        if self.starting_h2_storage_t is None:
            # Default: start with full storage capacity
            starting_storage_t[0] = cap_t
        else:
            # User-defined actual starting storage
            starting_storage_t[0] = self.starting_h2_storage_t

                # Starting inventory cannot exceed physical storage capacity
        if starting_storage_t[0] > cap_t:
            raise ValueError(
                f"Starting storage ({starting_storage_t[0]:.3f} t) "
                f"exceeds storage capacity ({cap_t:.3f} t). "
                "Increase storage capacity or reduce starting_h2_storage_t."
            )

        # ---------- Chain simulation ----------
        for t in range(n):
            s_start = starting_storage_t[t]
            p = prod_tph[t]
            d = demand_tph[t]

            # Production -> Storage first REPLACED
            # Production -> Demand first
            prod_to_demand_tph[t] = min(p, d)

            # Production surplus -> Storage
            surplus_tph = max(0.0, p - prod_to_demand_tph[t])

            available_capacity_t = max(
                0.0,
                cap_t - s_start
            )

            prod_to_storage_tph[t] = min(
                surplus_tph,
                available_capacity_t
            )

            # Demand shortfall
            demand_remaining_tph[t] = max(0.0, d - prod_to_demand_tph[t])

            

            # Storage -> Demand 
            # Storage -> Demand
            available_storage_t = max(
                0.0,
                s_start
            )

            storage_to_demand_tph[t] = min(
                demand_remaining_tph[t],
                available_storage_t
            ) 
            #Changed after minimum storage issue
            #====INVALID Correction CORRECTED after TEST 6 ====================================================================================

            # Supply
            supply_tph[t] = prod_to_demand_tph[t] + storage_to_demand_tph[t]

            shortfall_tph[t] = max( 0.0, d - supply_tph[t])

            # Actual storage 
            pre_boil = s_start + prod_to_storage_tph[t] - storage_to_demand_tph[t]
            boil_off_t[t] = pre_boil * boil_frac_per_hour
            s_end = max(0.0,pre_boil - boil_off_t[t])

            actual_storage_t[t] = s_end

            # Feed to next starting storage
            if t < n - 1:
                starting_storage_t[t + 1] = s_end
        
        """
        # ---------- Compressor / Liquefaction CAPEX ----------
        max_hourly_storage_inflow_kgph = np.max(prod_to_storage_tph) * 1000.0

        if max_hourly_storage_inflow_kgph > 0:

            if self.storage_method == "Liquid H2":
                compressor_spec_capex = (
                    0.9
                    * 35280.8215583011
                    * max_hourly_storage_inflow_kgph ** (-0.197333784307813)
                )
            else:
                compressor_spec_capex = self._calc_compressor_spec_capex(
                    self.pout_bar,
                    max_hourly_storage_inflow_kgph
                )

            self.compressor_specific_capex = compressor_spec_capex
            self.total_compressor_capex = (
                compressor_spec_capex * max_hourly_storage_inflow_kgph
            )

        else:
            self.compressor_specific_capex = 0.0
            self.total_compressor_capex = 0.0
        """
        # ---------- Compressor / Liquefaction CAPEX ----------

        # Compressor is upstream of the split between demand and storage.
        # Therefore, both production -> demand and production -> storage
        # pass through the compressor.

        max_compression_flow_kgph = np.max(
            (prod_to_demand_tph + prod_to_storage_tph) * 1000.0
        )
        compressed_kgph = (
            prod_to_demand_tph + prod_to_storage_tph
        ) * 1000.0

        annual_compressed_h2_kg = np.sum(compressed_kgph)

        if max_compression_flow_kgph > 0:

            if self.storage_method == "Liquid H2":

                compressor_spec_capex = (
                    0.9
                    * 35280.8215583011
                    * max_compression_flow_kgph ** (-0.197333784307813)
                )

            else:

                compressor_spec_capex = self._calc_compressor_spec_capex(
                    self.pout_bar,
                    max_compression_flow_kgph
                )

            self.compressor_specific_capex = compressor_spec_capex

            self.total_compressor_capex = (
                compressor_spec_capex * max_compression_flow_kgph
            )

        else:

            self.compressor_specific_capex = 0.0
            self.total_compressor_capex = 0.0


        # ---------- Total Storage CAPEX calculation ----------

        if capacity_kg <= 0:

            self.total_storage_capex = 0.0

        elif self.com_liq_included:

            self.total_storage_capex = (
                self.storage_specific_capex * capacity_kg
                - self.total_compressor_capex
            )

        else:

            self.total_storage_capex = (
                self.storage_specific_capex * capacity_kg
            )
        #------------Compressor OPEX calculation--------------

        if self.storage_method == "Liquid H2":

            #calculated differently
            self.total_compressor_opex = self.total_compressor_capex*0.02 + self.liq_storage_sec*self.energy_cost*annual_compressed_h2_kg
            
        else:
            self.total_compressor_opex = self.total_compressor_capex*0.02 + self.sec_compressor*self.energy_cost*annual_compressed_h2_kg
        

        # ------------ Storage OPEX calculation ------------

        self.total_storage_opex = (
            self.total_storage_capex * 0.02
        )

        # ---------- Derived inventories for reporting ----------
        storage_no_init_kg = cumulative_additions_kg
        storage_no_init_t = storage_no_init_kg / 1000.0
        ideal_storage_t = ideal_storage_curve_kg / 1000.0

        # ---------- Cumulatives (tonnes) ----------
        
        cumulative_demand_t = np.cumsum(demand_tph)
        cumulative_supply_t = np.cumsum(supply_tph)

        # ---------- Store outputs ----------
        # Rates
        self.hourly_demand_tph = demand_tph
        self.hourly_production_tph = prod_tph
        self.h2_additions_tph = additions_tph

        self.production_to_storage_tph = prod_to_storage_tph
        self.production_to_demand_tph = prod_to_demand_tph
        self.demand_shortfall_tph = shortfall_tph
        self.storage_to_demand_tph = storage_to_demand_tph
        self.supply_tph = supply_tph
        self.storage_inflows_tph = prod_to_storage_tph
        self.storage_outflows_tph = -storage_to_demand_tph

        # Inventories (tonnes)
        self.starting_storage_t = starting_storage_t
        self.actual_storage_t = actual_storage_t
        self.ideal_storage_t = ideal_storage_t
        self.storage_no_init_t = storage_no_init_t

        # Loss
        self.boil_off_t = boil_off_t
        self.boil_off_kg = boil_off_t * 1000.0

        # kg series that match your previous naming expectations
        self.h2_additions_kgph = (prod_kgph - demand_kgph)
        self.storage_no_init_kg = storage_no_init_kg
        self.actual_storage_kg = actual_storage_t * 1000.0

        # Cumulatives (tonnes)
        self.cumulative_production_t = cumulative_production_t
        self.cumulative_demand_t = cumulative_demand_t
        self.cumulative_supply_t = cumulative_supply_t
        # ---------- Collect all outputs into dictionary ----------
        self.outputs = {
            # Scalars
            "required_initial_storage_kg": self.required_initial_storage_kg,
            "required_capacity_kg": self.required_capacity_kg,
            "storage_specific_capex": self.storage_specific_capex,
            "compressor_specific_capex": self.compressor_specific_capex,
            "total_compressor_capex": self.total_compressor_capex,
            "total_compressor_opex":self.total_compressor_opex,
            "total_storage_capex": self.total_storage_capex,
            "total_storage_opex": self.total_storage_opex,

            # Hourly inputs
            "hourly_demand_kgph": self.hourly_demand_kgph,
            "hourly_production_kgph": self.hourly_production_kgph,

            # Hourly rates (tph)
            "hourly_demand_tph": self.hourly_demand_tph,
            "hourly_production_tph": self.hourly_production_tph,
            "h2_additions_tph": self.h2_additions_tph,
            "production_to_storage_tph": self.production_to_storage_tph,
            "production_to_demand_tph": self.production_to_demand_tph,
            "demand_shortfall_tph": self.demand_shortfall_tph,
            "storage_to_demand_tph": self.storage_to_demand_tph,
            "supply_tph": self.supply_tph,
            "storage_inflows_tph": self.storage_inflows_tph,
            "storage_outflows_tph": self.storage_outflows_tph,

            # Inventories (tonnes)
            "starting_storage_t": self.starting_storage_t,
            "actual_storage_t": self.actual_storage_t,
            "ideal_storage_t": self.ideal_storage_t,
            "storage_no_init_t": self.storage_no_init_t,
            "warning": warning_message,

            # kg series
            "h2_additions_kgph": self.h2_additions_kgph,
            "storage_no_init_kg": self.storage_no_init_kg,
            "actual_storage_kg": self.actual_storage_kg,

            # Loss
            "boil_off_t": self.boil_off_t,
            "boil_off_kg": self.boil_off_kg,

            # Cumulatives
            "cumulative_production_t": self.cumulative_production_t,
            "cumulative_demand_t": self.cumulative_demand_t,
            "cumulative_supply_t": self.cumulative_supply_t,
        }

        return self.outputs