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

    # ---------- Default calculation methods ----------

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

    def _default_sec_compression(self):
        # default compressor specific energy consumption
        return 0.86

    def _default_sec_transport(self):
        # default transport specific energy consumption
        return 0.69

    def _default_water_consumption(self):
        # default water consumption
        return 0.0015

    def _default_annual_improvement(self):
        return 1.001

    def _default_install_year(self):
        return 2030

    def _default_LHV(self):
        return 33.33

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
            'sec_electrolyser',
            self._default_avg_sec_electrolyser(self.electro_capacity)
        )

        self.sec_compression = cfg.get(
            'sec_compression', #should be from stroage
            self._default_sec_compression()
        )

        self.sec_transport = cfg.get(
            'sec_transport', # value should come from transport throught core
            self._default_sec_transport()
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



    def h2_from_energy_kWh(self, energy_kWh,sec_electrolyser):
        total_sec = sec_electrolyser + self.sec_compression
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





    def evaluate_multiple_streams(self, power_df):
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

        hours = len(power_df)

        # ======================
        # Power domain (kW)
        # ======================
        add_percentage = (self.sec_compression)/self.avg_sec_electrolyser #Additional percentage for compression/liquefaction & transportation (self.sec_compression+self.sec_transport ???? )/self.avg_sec_electrolyser
        total_power_kW = power_df.sum(axis=1).values
        actual_capacity = self.electro_capacity*(1+add_percentage)
        power_used_kW = np.minimum(total_power_kW, actual_capacity)
        power_curtailed_kW = total_power_kW - power_used_kW

        # ======================
        # Energy domain (kWh) – Δt = 1 h
        # ======================
        energy_used_kWh = power_used_kW.copy()
        load = power_used_kW/self.electro_capacity
        efficiency = self.electrolyser_efficiency(load*100, self.electro_capacity, self.install_year)

        sec_electrolyser = self.LHV_h2/efficiency

        # ======================
        # Hydrogen production (kg/h)
        # ======================
        h2_hourly_kg = self.h2_from_energy_kWh(energy_used_kWh,sec_electrolyser)

        # ======================
        # Downstream processes (hourly)
        # ======================
        compression_energy_kWh = h2_hourly_kg * self.sec_compression
        transport_energy_kWh = h2_hourly_kg * self.sec_transport
        water_m3 = h2_hourly_kg * self.water_consumption

        # ======================
        # Stream-level allocation (hourly)
        # ======================
        stream_results = {}

        for col in power_df.columns:
            stream_power_kW = power_df[col].values

            share = np.divide(
                stream_power_kW,
                total_power_kW,
                out=np.zeros_like(stream_power_kW),
                where=total_power_kW > 0
            )

            stream_power_used_kW = share * power_used_kW
            stream_power_curtailed_kW = stream_power_kW - stream_power_used_kW

            stream_energy_used_kWh = stream_power_used_kW.copy()

            stream_h2_kg = share * h2_hourly_kg

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
            "capacity_factor": energy_used_kWh.sum() / (actual_capacity * hours)
        }

        # ======================
        # Output
        # ======================
        return {
            "hourly": {
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
            },
            "streams": stream_results,
            "totals": totals
        }



