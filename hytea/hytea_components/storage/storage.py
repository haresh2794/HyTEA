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
            "Salt cavern(s)":   {"pressure_bar": 200, "temperature_C": 25, "a": 0.195420825585994, "b": 0.125411409869413, "com_liq_included":True},
            "Lined rock cavern":{"pressure_bar": 150, "temperature_C": 25, "a": 0.126197258645584, "b": 0.200511784228375, "com_liq_included":True},
            "Liquid H2":        {"pressure_bar": 1,   "temperature_C": -253, "a": None, "b": None, "com_liq_included":False},
        }

        # ---------------- Inputs ----------------
        self.storage_method = None
        self.storage_capacity_tonnes = None  # optional override (tonnes) when storage_sizing_option="Tonnes"
        self.custom_specific_capex = None  # €/kg (optional override)
        self.capex_a = None
        self.capex_b = None

        self.max_charge_rate_kgph = None     # kg/h
        self.max_discharge_rate_kgph = None  # kg/h

        self.storage_specific_capex = None
        self.boil_off_fraction_per_year = None  # fraction/year

        self.hourly_demand_kgph = None
        self.hourly_production_kgph = None
        self.fos = None
        self.com_liq_included = None
        self.P0_bar = None
        self.energy_cost = None
        self.pout_bar = None
        # Starting storage policy
        self.starting_storage_option = "Full storage"  # "Full storage" or "Hours"
        self.starting_storage_hours = 0.0              # only used if option == "Hours"

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
        Compressor CAPEX for compression from P0_bar to pout_bar
        """
        table = {
            0:  (95.16475, 126.05269, -0.34019),
            15: (68.95146, 79.23782, -0.33997),
            30: (64.65757, 77.77250, -0.33998),
            60: (61.065, 68.250, -0.340),
        }

        pin = self.P0_bar
        Q = Q2_kgph

       

        if pin not in table:
            raise ValueError("P0_bar must be one of: 0, 15, 30, 60 barg")

        A200, A500, B = table[pin]

        A = A200 + (pout_bar - 200) / (500 - 200) * (A500 - A200)

        return 1000 * A * Q**B



    def calc_sec_boost(self, P_target):
        """
        Specific compression energy (kWh/kg) from P0_bar to P_target.
        """
        if self.P0_bar not in self._lookup_boost_sec_table:
            raise ValueError("P0_bar must be one of: 0, 15, 30, 60 barg")

        slope, intercept = self._lookup_boost_sec_table[self.P0_bar]

        if P_target <= self.P0_bar:
            return 0.0

        return slope * (P_target - self.P0_bar) + intercept

    def _capex_liquid_h2(self, capacity_kg):
        capacity_tonnes = capacity_kg / 1000.0
        lh2_expr = (30000000.0 * (capacity_tonnes ** 0.67)) / (capacity_kg * 1000.0)
        return max(22.0, lh2_expr)


    def _capex_ab_scaling(self, capacity_kg):
        if self.capex_a is None or self.capex_b is None:
            raise ValueError(f"No CAPEX parameters defined for storage type '{self.storage_method}'")
        return 0.9 * 10 ** (
            1.0 / (self.capex_a * np.log10(capacity_kg) + self.capex_b))
        
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
        self.P0_bar = cfg.get("P0_bar", 15)
        self.energy_cost = cfg.get("energy_cost", 0.25) # €/kWh
        self.pout_bar = cfg.get("pout_bar", defaults["pressure_bar"])

        self.com_liq_included = cfg.get("com_liq_included", defaults["com_liq_included"])

        # Optional: allow starting storage policy to be configured too
        self.starting_storage_option = cfg.get("starting_storage_option", "Full storage")
        self.starting_storage_hours = float(cfg.get("starting_storage_hours", 0.0))

        self.sec_compressor = cfg.get("storage_com_sec", self.calc_sec_boost(self.pout_bar))

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

        self.required_initial_storage_kg = max(0.0, -float(np.min(cumulative_additions_kg))) * fos

        ideal_storage_curve_kg = self.required_initial_storage_kg + cumulative_additions_kg
        self.required_capacity_kg = float(np.max(ideal_storage_curve_kg))

        # ---------- Capacity selection ----------
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

        # Ensure capacity >= required initial buffer
        if capacity_kg < self.required_initial_storage_kg:
            print("Storage insufficient: capacity < required initial buffer. Adjusting to required initial.")
            capacity_kg = self.required_initial_storage_kg
        
        cap_t = capacity_kg / 1000.0
      
        # ---------- CAPEX calculation ----------
        if self.custom_specific_capex is not None:
            self.storage_specific_capex = self.custom_specific_capex

        elif self.storage_method == "Liquid H2":
            self.storage_specific_capex = self._capex_liquid_h2(capacity_kg)

        else:
            self.storage_specific_capex = self._capex_ab_scaling(capacity_kg)

        
        max_hourly_prod_kgph = np.max(prod_kgph)

        # ---------- Compressor / Liquefaction CAPEX ----------
        if self.storage_method == "Liquid H2":
            #calculated differently
           
            compressor_spec_capex = 0.9*35280.8215583011*max_hourly_prod_kgph**(-0.197333784307813)
        else:
            
            compressor_spec_capex = self._calc_compressor_spec_capex(self.pout_bar,max_hourly_prod_kgph)


        self.compressor_specific_capex = compressor_spec_capex
        self.total_compressor_capex = compressor_spec_capex * max_hourly_prod_kgph

        if self.com_liq_included:
            self.total_storage_capex = self.storage_specific_capex * capacity_kg*self.fos + self.total_compressor_capex
        else:
            self.total_storage_capex = self.storage_specific_capex * capacity_kg*self.fos


        #------------OPEX calculation--------------
        if self.storage_method == "Liquid H2":
            #calculated differently
            self.total_storage_opex = self.total_storage_capex*0.02 + min(25.495937660557*max_hourly_prod_kgph**(-0.116967960344646),0.45*33.3)*self.energy_cost*sum(prod_kgph)
            
        else:
            self.total_storage_opex = self.total_storage_capex*0.02 + self.sec_compressor*self.energy_cost*sum(prod_kgph)

        
        req_init_t = self.required_initial_storage_kg / 1000.0
        


        # ---------- Convert to rates (tph) ----------
        demand_tph = demand_kgph / 1000.0
       
        additions_tph = (prod_kgph - demand_kgph) / 1000.0

        boil_frac_per_hour = (self.boil_off_fraction_per_year / 8760.0) if self.boil_off_fraction_per_year is not None else 0.0

        # ---------- Allocate arrays ----------
        starting_storage_t = np.zeros(n)
        actual_storage_t = np.zeros(n)

        prod_to_storage_tph = np.zeros(n)
        prod_to_demand_tph = np.zeros(n)
        shortfall_tph = np.zeros(n)
        storage_to_demand_tph = np.zeros(n)
        supply_tph = np.zeros(n)

        boil_off_t = np.zeros(n)

        # ---------- Starting storage t=0  ----------
        start_opt = str(self.starting_storage_option).strip().lower()
        if start_opt == "full storage":
            starting_storage_t[0] = req_init_t
        else:
            # Hours option: hours * demand_per_hour * fos
            starting_storage_t[0] = float(self.starting_storage_hours) * demand_tph[0] * fos

        # ---------- Chain simulation ----------
        for t in range(n):
            s_start = starting_storage_t[t]
            p = prod_tph[t]
            d = demand_tph[t]

            # Production -> Storage first
            if s_start + p > cap_t*self.fos:
                prod_to_storage_tph[t] = cap_t - s_start
            else:
                prod_to_storage_tph[t] = p

            # Production -> Demand gets the remainder
            prod_to_demand_tph[t] = p - prod_to_storage_tph[t]

            # Demand shortfall
            shortfall_tph[t] = max(0.0, d - prod_to_demand_tph[t])

            # Storage -> Demand 
            if s_start - shortfall_tph[t] > req_init_t/self.fos:
                storage_to_demand_tph[t] = shortfall_tph[t]
            else:
                storage_to_demand_tph[t] = min(shortfall_tph[t],s_start - req_init_t/self.fos)

            # Supply
            supply_tph[t] = prod_to_demand_tph[t] + storage_to_demand_tph[t]

            # Actual storage 
            pre_boil = s_start + prod_to_storage_tph[t] - storage_to_demand_tph[t]
            boil_off_t[t] = pre_boil * boil_frac_per_hour
            s_end = pre_boil - boil_off_t[t]

            actual_storage_t[t] = s_end

            # Feed to next starting storage
            if t < n - 1:
                starting_storage_t[t + 1] = s_end

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
        self.storage_outflows_tph = storage_to_demand_tph

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