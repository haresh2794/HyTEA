import numpy as np
import pandas as pd
import yaml
from importlib import resources  # allows access to files included in the package


class ALKElectrolyser:
    """
    Single electrolyser fed by multiple energy streams
    Hourly resolution
    Power in kW, energy in kWh
    """

    def __init__(self):
        self.electro_capacity = None
        self.avg_sec_electrolyser = None
        self.sec_compression = None
        self.sec_transport = None
        self.water_consumption = None
        self.efficiency = None
        self.annual_improvement = None
        self.install_year = None
        self.size_factors = {
            1: 0.908995449,
            5: 0.999894994,
            20: 1.020301014,
            100: 1.041557285
        }
        self.spec_capex = None
        self.opex_per = None
        self.outlet_pressure = None
        # Totals
        self.total_energy_electrolysis_kWh = None
        self.total_h2_kg = None
        self.total_energy_curtailed_kWh = None
        self.total_compression_energy_kWh = None
        self.total_transport_energy_kWh = None
        self.total_water_m3 = None
        self.capacity_factor = None
        self.capex = None
        self.opex = None

        # Stream-level
        self.streams_power_used_kW = {}
        self.streams_power_used_MW = {}
        self.streams_power_curtailed_kW = {}
        self.streams_power_curtailed_MW = {}
        self.streams_energy_used_kWh = {}
        self.streams_energy_used_MWh = {}
        self.streams_H2_kg ={}
        self.streams_totals_energy_used_kWh = {}
        self.streams_totals_energy_curtailed_kWh = {}
        self.streams_totals_H2_kg = {}

        #hourly
        self.hourly_total_power_kW = None
        self.hourly_power_used_kW = None
        self.hourly_power_curtailed_kW = None
        self.hourly_energy_used_kWh = None
        self.hourly_H2_kg = None
        self.hourly_compression_energy_kWh = None
        self.hourly_transport_energy_kWh = None
        self.hourly_water_m3 = None
        self.hourly_efficiency = None
        self.hourly_sec_electrolyser = None
        self.hourly_load = None

        #calculating the energy for storage for inclusion in H2 production energy requirement
        self.storage_defaults = {
            "Compressed Tanks": {"pressure_bar": 300, "temperature_C": 25},
            "Salt cavern(s)":   {"pressure_bar": 200, "temperature_C": 25},
            "Lined rock cavern":{"pressure_bar": 150, "temperature_C": 25},
            "Liquid H2":        {"pressure_bar": 1,   "temperature_C": -253},
        }
        
        self.transport_pressure = None

        self._lookup_boost_sec_table = {
                            0:  (0.00433, 4.13),
                            15: (0.00367, 1.72),
                            30: (0.00333, 1.13),
                            60: (0.00300, 0.68)
                        }
       

    # ---------- Default calculation methods ----------

    def _default_electro_capacity(self):
        return 4  # MW

    def _default_spec_capex(self):

        x =886.8145256
        y = -0.164384223

        return x*self.electro_capacity**y #€/kW
    
    def _default_opex_per(self):
        return 0.03 #fraction of capex
    
    def _default_outlet_pressure(self):
        return 15 #bar
    
    def _default_avg_sec_electrolyser(self, capacity):
        """
        Average electrolyser specific energy consumption (SEC)
        y = c * x^b
        """
        c = 0.018577706
        b = -0.028315417

        return (1/c) * (capacity ** b)

    def _default_water_consumption(self):
        # default water consumption
        return 0.0015

    def _default_annual_improvement(self):
        return 1.001

    def _default_install_year(self):
        return 2030

    def _default_LHV(self):
        return 33.33
    
    def _default_liq_storage_sec(self):
            
        liq_h2_initial_sizing = liq_h2_initial_sizing = 1000 * self.electro_capacity * (1 + (10 / self.avg_sec_electrolyser)) / (self.avg_sec_electrolyser + 10)
        x = min(25.495937660557*liq_h2_initial_sizing**(-0.116967960344646),0.45*33.3)

        return x
    
    def calc_sec_boost(self, P_target):
        """
        Specific compression energy (kWh/kg) from outlet_pressure to P_target.
        """
        if self.outlet_pressure not in self._lookup_boost_sec_table:
            raise ValueError("outlet_pressure must be one of: 0, 15, 30, 60 barg")

        slope, intercept = self._lookup_boost_sec_table[self.outlet_pressure]

        if P_target <= self.outlet_pressure:
            return 0.0
        
        return slope * (P_target - self.outlet_pressure) + intercept
    
    def _default_transport_pressure(self):
        return 350

    # ---------- Configuration loader ----------

    def configure(self, config=None, config_file=None):
        """Load configuration and compute missing defaults"""

        # Load user config
        if config is not None:
            cfg = config
        elif config_file is not None:
            with open(config_file, 'r') as f:
                cfg = yaml.safe_load(f)
        else:
            cfg = {}

        # ---- Stage 1: resolve electrolyser size ----
        self.electro_capacity = cfg.get(
            'electro_capacity',
            self._default_electro_capacity()
        )

        # ---- Stage 2: compute dependent defaults ----

        self.avg_sec_electrolyser = cfg.get(
            'avg_sec_electrolyser',
            self._default_avg_sec_electrolyser(self.electro_capacity)
        )


        self.water_consumption = cfg.get(
            'water_consumption', #specific water consumption
            self._default_water_consumption()
        )

        self.annual_improvement = cfg.get(
            'annual_improvement',
            self._default_annual_improvement()
        )

        self.install_year = cfg.get(
            'install_year',
            self._default_install_year()
        )
        self.LHV_h2 = cfg.get(
            'LHV',
            self._default_LHV()
        )

        self.spec_capex = cfg.get(
            'spec_capex',
            self._default_spec_capex()
        )
        self.opex_per = cfg.get(
            'opex_per',
            self._default_opex_per()
        )

        self.outlet_pressure = cfg.get(
            'outlet_pressure',
            self._default_outlet_pressure()
        )

        #-------storage_ energy consumption

        self.storage_method = cfg.get("storage_method", "Compressed Tanks")
        if self.storage_method not in self.storage_defaults:
            raise ValueError(f"Unknown storage_method: {self.storage_method}")

        defaults_store = self.storage_defaults[self.storage_method]
        self.pout_bar = cfg.get("pout_bar", defaults_store["pressure_bar"])

        if self.storage_method == "Liquid H2":
            self.sec_compression = cfg.get(
            'sec_compression', #should be from stroage
            self._default_liq_storage_sec())
        else: 
            self.sec_compression = cfg.get('sec_compression',self.calc_sec_boost(self.pout_bar) )


        #-----Transport specific energy consumption-------------

        if self.storage_method == "Liquid H2":
            self.transport_pressure = cfg.get('transport_pressure', 0)
            self.sec_transport= cfg.get('sec_transport',0)
        else: 
            self.transport_pressure  = cfg.get('transport_pressure', self._default_transport_pressure())
            self.sec_transport= cfg.get('sec_transport',max(0.0, self.calc_sec_boost(self.transport_pressure) - self.calc_sec_boost(self.pout_bar)))
            
    def get_actual_input_capacity_kW(self):
        """
        Return the maximum total power input accepted by the electrolyser system [kW],
        including compression and transport energy overheads.
        """
        electro_capacity_kW = self.electro_capacity * 1000
        add_percentage = (self.sec_compression + self.sec_transport) / self.avg_sec_electrolyser
        return electro_capacity_kW * (1 + add_percentage)

    def show_defaults(self):
        """
        Show all configurable parameters with their default values and units.
        Returns a dictionary that can be directly used in `configure()`.
        """
        defaults_with_units = {
            'electro_capacity': (self._default_electro_capacity(), 'MW'),
            'avg_sec_electrolyser': (self._default_avg_sec_electrolyser(self._default_electro_capacity()), 'kWh/kg H2'),
            'water_consumption': (self._default_water_consumption(), 'm3/kg H2'),
            'annual_improvement': (self._default_annual_improvement(), 'fraction'),
            'install_year': (self._default_install_year(), ''),
            'LHV': (self._default_LHV(), 'kWh/kg')
        }
        print("===== ALK Electrolyser Configurable Defaults =====")
        for key, (value, unit) in defaults_with_units.items():
            unit_str = f" ({unit})" if unit else ""
            print(f"{key}{unit_str}: {value}")

        print("\nYou can override these in object_name.configure(config=...) using a dictionary, e.g.:")
        print("config = { 'electro_capacity': 10, 'sec_compression': 0.9, ... }")

        # Return dictionary without units for direct use
        return {key: value for key, (value, _) in defaults_with_units.items()}

    def h2_from_energy_kWh(self, energy_kWh,sec_electrolyser):
        total_sec = sec_electrolyser + self.sec_compression+self.sec_transport
        return energy_kWh / total_sec



    def _nearest_size(self, size_mw):
        """Pick nearest available electrolyser size (MW)"""
        return min(self.size_factors.keys(), key=lambda x: abs(x - size_mw))
    
    def electrolyser_efficiency(self, load_pct, size_mw, install_year):
        """Vectorised efficiency (fraction) for percentage load"""
        load = np.asarray(load_pct)
        nearest_size = self._nearest_size(size_mw)
        factor = self.size_factors[nearest_size]
        improvement_term = self.annual_improvement ** (install_year - 2020)

        eff = np.zeros_like(load, dtype=float)

        # Region 1: load <= 10%
        mask_low = load <= 10
        eff[mask_low] = (
            factor
            * (1.3786 * load[mask_low] - 0.0011)
            * improvement_term
        )

        # Region 2: load > 10%
        mask_high = ~mask_low
        eff[mask_high] = (
            factor
            * (
                -0.0000044 * load[mask_high] ** 4
                + 0.0012571 * load[mask_high] ** 3
                - 0.132294 * load[mask_high] ** 2
                + 6.0664467 * load[mask_high]
                - 34.860097
            )
            * improvement_term
        )

        return eff / 100  # convert % to fraction





    def evaluate(self, power_df):
        """
        Parameters
        ----------
        power_df : DataFrame
            Hourly power values [kW], columns = streams

        Returns
        -------
        dict
            Hourly arrays + totals (unit consistent)
        """
        if not isinstance(power_df, pd.DataFrame):
            raise TypeError("power_df must be a pandas DataFrame.")

        if power_df.isnull().any().any():
            raise ValueError("power_df contains NaN values.")

        if (power_df < 0).any().any():
            raise ValueError("power_df must not contain negative values.")
        
        hours = len(power_df)
        self.streams_power_used_kW = {}
        self.streams_power_used_MW = {}
        self.streams_power_curtailed_kW = {}
        self.streams_power_curtailed_MW = {}
        self.streams_energy_used_kWh = {}
        self.streams_energy_used_MWh = {}
        self.streams_H2_kg = {}
        self.streams_totals_energy_used_kWh = {}
        self.streams_totals_energy_curtailed_kWh = {}
        self.streams_totals_H2_kg = {}

       
        # ======================
        # Power domain (kW)
        # ======================
        add_percentage = (self.sec_compression+self.sec_transport)/self.avg_sec_electrolyser #Additional percentage for compression/liquefaction & transportation (self.sec_compression+self.sec_transport ???? )/self.avg_sec_electrolyser
        total_power_kW = power_df.sum(axis=1).values
        electro_capacity_kW = self.electro_capacity * 1000
        actual_capacity_kW = electro_capacity_kW * (1 + add_percentage)
        power_used_kW = np.minimum(total_power_kW, actual_capacity_kW)
        power_curtailed_kW = total_power_kW - power_used_kW

       
        # ======================
        # Energy domain (kWh) – Δt = 1 h
        # ======================
        energy_used_kWh = power_used_kW.copy()
       
        load = power_used_kW / electro_capacity_kW
        efficiency = self.electrolyser_efficiency(load * 100, self.electro_capacity, self.install_year)
        efficiency = np.where(power_used_kW > 0, efficiency, 0.0)

        sec_electrolyser = np.where(
            efficiency > 0,
            self.LHV_h2 / efficiency,
            np.inf
        )

        # ======================
        # Hydrogen production (kg/h)
        # ======================
        h2_hourly_kg = np.where(
            energy_used_kWh > 0,
            self.h2_from_energy_kWh(energy_used_kWh, sec_electrolyser),
            0.0
)

        
      
        # ======================
        # Downstream processes (hourly)
        # ======================
        compression_energy_kWh = h2_hourly_kg * self.sec_compression
        transport_energy_kWh = h2_hourly_kg * self.sec_transport
        water_m3 = h2_hourly_kg * self.water_consumption



        # ======================
        # Stream-level allocation (hourly) - priority-based
        # ======================
        stream_results = {}

        # Remaining electrolyser power to allocate (hourly)
        remaining_power_kW = power_used_kW.copy()

        #Capex and OPEX

        capex = self.spec_capex*self.electro_capacity*1000
        opex = self.opex_per*capex


        for col in power_df.columns:
            stream_power_kW = power_df[col].values

            # Allocate as much as possible from this stream
            stream_power_used_kW = np.minimum(stream_power_kW, remaining_power_kW)

            # Power curtailed from this stream is what couldn't be used
            stream_power_curtailed_kW = stream_power_kW - stream_power_used_kW

            # Update remaining electrolyser power for the next stream
            remaining_power_kW -= stream_power_used_kW

            # Energy used and H2 produced from this stream
            stream_energy_used_kWh = stream_power_used_kW.copy()
            stream_h2_kg = self.h2_from_energy_kWh(stream_energy_used_kWh, sec_electrolyser)

            # Store results in dictionary exactly like before
            stream_results[col] = {
                "power_used_kW": stream_power_used_kW,
                "power_curtailed_kW": stream_power_curtailed_kW,
                "energy_used_kWh": stream_energy_used_kWh,
                "H2_kg": stream_h2_kg,
                "totals": {
                    "energy_used_kWh": stream_energy_used_kWh.sum(),
                    "energy_curtailed_kWh": stream_power_curtailed_kW.sum(),
                    "H2_kg": stream_h2_kg.sum()
                }
            }

            # Also store as class attributes if you want object-style access
            self.streams_power_used_kW[col] = stream_power_used_kW
            self.streams_power_used_MW[col] = stream_power_used_kW / 1000
            self.streams_power_curtailed_kW[col] = stream_power_curtailed_kW
            self.streams_power_curtailed_MW[col] = stream_power_curtailed_kW / 1000
            self.streams_energy_used_kWh[col] = stream_energy_used_kWh
            self.streams_energy_used_MWh[col] = stream_energy_used_kWh / 1000
            self.streams_H2_kg[col] = stream_h2_kg
            self.streams_totals_energy_used_kWh[col] = stream_energy_used_kWh.sum()
            self.streams_totals_energy_curtailed_kWh[col] = stream_power_curtailed_kW.sum()
            self.streams_totals_H2_kg[col] = stream_h2_kg.sum()

        

        # ======================
        # Totals
        # ======================
        totals = {
            "energy_electrolysis_kWh": energy_used_kWh.sum(),
            "H2_kg": h2_hourly_kg.sum(),

            "energy_curtailed_kWh": power_curtailed_kW.sum(),
            "compression_energy_kWh": compression_energy_kWh.sum(),
            "transport_energy_kWh": transport_energy_kWh.sum(),
            "water_m3": water_m3.sum(),
            "capacity_factor": energy_used_kWh.sum() / (actual_capacity_kW * hours),
            "capex":capex,
            "opex":opex,
            "outlet_pressure": self.outlet_pressure,
            "electrolyser_spec_capex": self.spec_capex
        }
    
        # ======================
        # Store totals as object attributes
        # ======================
        self.total_energy_electrolysis_kWh = energy_used_kWh.sum()
        self.total_h2_kg = h2_hourly_kg.sum()
        self.total_energy_curtailed_kWh = power_curtailed_kW.sum()
        self.total_compression_energy_kWh = compression_energy_kWh.sum()
        self.total_transport_energy_kWh = transport_energy_kWh.sum()
        self.total_water_m3 = water_m3.sum()
        self.capacity_factor = energy_used_kWh.sum() / (actual_capacity_kW * hours)
        self.capex = capex
        self.opex = opex
        # ======================
        # hourly
        # ======================
        hourly = {
                "total_power_kW": total_power_kW,
                "power_used_kW": power_used_kW,
                "power_curtailed_kW": power_curtailed_kW,
                "energy_used_kWh": energy_used_kWh,
                "H2_kg": h2_hourly_kg,
                "compression_energy_kWh": compression_energy_kWh,
                "transport_energy_kWh": transport_energy_kWh,
                "water_m3": water_m3,
                "efficiency": efficiency,
                "sec_electrolyser": sec_electrolyser,
                "load": load
            }
        # ======================
        # Store hourly as object attributes
        # ======================   
        self.hourly_total_power_kW = total_power_kW
        self.hourly_power_used_kW = power_used_kW
        self.hourly_power_curtailed_kW = power_curtailed_kW
        self.hourly_energy_used_kWh = energy_used_kWh
        self.hourly_H2_kg = h2_hourly_kg
        self.hourly_compression_energy_kWh = compression_energy_kWh
        self.hourly_transport_energy_kWh = transport_energy_kWh
        self.hourly_water_m3 = water_m3
        self.hourly_efficiency = efficiency
        self.hourly_sec_electrolyser = sec_electrolyser
        self.hourly_load = load
        # ======================
        # Output
        # ======================
        return {
            "hourly": hourly,
            "streams": stream_results,
            "totals": totals
        }





