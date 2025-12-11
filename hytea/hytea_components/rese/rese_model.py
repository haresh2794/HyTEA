import pandas as pd
import yaml
import numpy as np
from importlib import resources #allows to access files that are included inside a package.

class RenewableElectricity:

    """RES-E component for HyTEA library: calculates hourly output, cumulative energy, average capacity factor, capex, and opex."""

    def __init__(self):
        self.hourly_cf = None
        self.capacity_mw = None
        self.capex_per_mw = None
        self.opex_per_mw = None
        self.hourly_cf_file = None


    def configure(self, config=None, config_file=None, csv_file=None):

        """Load configuration from YAML file or use defaults or use overides from user"""

        if config is not None:
            cfg = config
        elif config_file is not None:
            with open(config_file, 'r') as f:
                cfg = yaml.safe_load(f)
        else:
            # Default values if nothing is provided
            cfg = {
                'capacity_mw': 100,       # default capacity
                'capex_per_mw': 2500,     # default CAPEX
                'opex_per_mw': 0.03*2500  # default OPEX
            }
            

        self.capacity_mw = cfg.get('capacity_mw')
        self.capex_per_mw = cfg.get('capex_per_mw')
        self.opex_per_mw = cfg.get('opex_per_mw')

        if csv_file is not None:
            self.hourly_cf_file = csv_file
        else:
            with resources.path('hytea.data', 'sample_wind_cf.csv') as p:
                self.hourly_cf_file = str(p)



    def calculate_hourly_output(self):

        """Calculate hourly electricity output in MW from capacity factor data sheet and installed capacity"""

        df = pd.read_csv(self.hourly_cf_file)
        self.hourly_cf = df['cf'].values
        return self.hourly_cf * self.capacity_mw

    def cumulative_energy_gwh(self, hourly=False):

        """
        Calculate cumulative energy produced in GWh. If hourly=True, return array of cumulative GWh over time. If hourly=False, return total GWh as single number.
        
        """

        hourly_output = self.calculate_hourly_output()
        cumulative = np.cumsum(hourly_output) / 1000
        return cumulative if hourly else cumulative[-1]

    def average_capacity_factor(self):
        
        """Calculate average capacity factor"""

        return self.hourly_cf.mean()

    def get_capex_opex(self):

        """Calculate CAPEX and OPEX of RES-E based on installed capacity"""

        return {
            'capex': self.capacity_mw * self.capex_per_mw,
            'opex': self.capacity_mw * self.opex_per_mw
        }


