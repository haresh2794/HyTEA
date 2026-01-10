import pandas as pd
import yaml
import numpy as np
from importlib import resources #allows to access files that are included inside a package.

class RenewableElectricity:
    """RES-E component for HyTEA library:
    calculates hourly output, cumulative energy, average capacity factor, CAPEX, and OPEX.
    """

    def __init__(self):
        # Core attributes
        self.capacity_mw = 100          # Installed capacity in MW
        self.capex_per_mw = 2500        # CAPEX in €/MW
        self.opex_per_mw = 0.03 * 2500 # OPEX in €/MW
        self.hourly_cf_file = None      # Path to hourly CF CSV
        self.hourly_cf = None           # Loaded hourly CF array

        # Computed attributes (filled on evaluate)
        self.hourly_output_mw = None
        self.cumulative_energy_gwh_total = None
        self.cumulative_energy_gwh_hourly = None
        self.avg_capacity_factor = None
        self.capex = None
        self.opex = None

    def show_defaults(self):
        """Show default values and units for user reference."""
        defaults = {
            'capacity_mw': 'MW, default 100',
            'capex_per_mw': '€/MW, default 2500',
            'opex_per_mw': '€/MW, default 0.03*CAPEX',
            'hourly_cf_file': 'CSV path, default packaged sample_wind_cf.csv'
        }
        for k, v in defaults.items():
            print(f"{k}: {v}")

    def configure(self, config=None, config_file=None, csv_file=None):
        """Load configuration from YAML file, dictionary, or defaults."""
        # Load user config or defaults
        if config is None and config_file is not None:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

        cfg = config if config is not None else {}
        self.capacity_mw = cfg.get('capacity_mw', self.capacity_mw)
        self.capex_per_mw = cfg.get('capex_per_mw', self.capex_per_mw)
        self.opex_per_mw = cfg.get('opex_per_mw', self.opex_per_mw)

        if csv_file is not None:
            self.hourly_cf_file = csv_file
        elif self.hourly_cf_file is None:
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


    def evaluate(self):
        """Run all core methods and store results as attributes."""
        
        self.hourly_output_mw = self.calculate_hourly_output()
        self.cumulative_energy_gwh_total = self.cumulative_energy_gwh(hourly=False)
        self.cumulative_energy_gwh_hourly = self.cumulative_energy_gwh(hourly=True)
        self.avg_capacity_factor = self.average_capacity_factor()
        self.capex = self.get_capex_opex('capex')
        self.opex = self.get_capex_opex('opex')

