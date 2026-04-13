import numpy as np
import pandas as pd
import yaml
from importlib import resources  # allows access to files included in the package

#All files developed and tested on COLAB and pasted

class Grid:
    """Grid electricity component for HyTEA library:
    calculates weighted RES-E CF, electricity price trends, GHG intensity, 
    and purchase/sales prices.
    """

    def __init__(self):
        # Core attributes
        self.hourly_cf_mul = None         # np.array, multiple CFs in one array
        self.ratios = [1]                 # ratio between CFs
        self.avg_grid_price = 100         # €/MWh
        self.difference = 50              # €/MWh
        self.ghg_avg = 300                # gCO2/kWh
        self.peak_hours = (17, 18)        # zero-based hour indices

        # Computed attributes (filled on evaluate)
        self.hourly_weighted_cf = None
        self.hourly_price_trend = None
        self.hourly_purchase_price_trend = None
        self.hourly_sales_price_trend = None
        self.hourly_ghg_trend = None
        
        self.avg_price_trend = None
        self.avg_ghg_trend = None

    def show_defaults(self):
        """Show the default values and units for user reference."""
        defaults = {
            'ratios': 'list, ratio between CFs, default [1]',
            'avg_grid_price': '€/MWh, default 100',
            'difference': '€/MWh, default 50',
            'ghg_avg': 'gCO2/kWh, default 300',
            'peak_hours': 'tuple of hours (0-23), default (17,18)',
            'hourly_cf_mul': 'np.array of CFs, shape=(8760, n_sources), default loaded from package CSV'
        }
        for k, v in defaults.items():
            print(f"{k}: {v}")

    def configure(self, config=None, hourly_cf_mul=None, config_file=None):
        """Load configuration from YAML file, dictionary, or defaults."""
        # Load user config or defaults
        if config is None and config_file is not None:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

        cfg = config if config is not None else {}
        self.ratios = cfg.get('ratios', self.ratios)
        self.avg_grid_price = cfg.get('avg_grid_price', self.avg_grid_price)
        self.difference = cfg.get('difference', self.difference)
        self.ghg_avg = cfg.get('ghg_avg', self.ghg_avg)
        self.peak_hours = cfg.get('peak_hours', self.peak_hours)

        # Load hourly CF
        if hourly_cf_mul is not None:
            self.hourly_cf_mul = np.asarray(hourly_cf_mul, dtype=float)
        elif self.hourly_cf_mul is None:
            with resources.path("hytea.data", "hourly_cf_mul.csv") as p:
                df = pd.read_csv(p)
                self.hourly_cf_mul = df.values.astype(float)

    def weighted_res_e_cf(self):
        """
        Calculate weighted hourly RES-E capacity factor using provided ratios.

        hourly_cf_mul: list of numpy arrays (CF1, CF2, CF3, ...)
        ratios: list of ratios (r1, r2, r3, ...)
                where r_i corresponds to CF_(i+1)/CF1 ratio
        
        Example:
            Weighted CF = (CF1 + r1*CF2 + r2*CF3 ... ) / (1 + r1 + r2 ...)
        """
        # Convert CFs to numpy arrays
        hourly_cfs = [np.array(cf) for cf in self.hourly_cf_mul]

        # Ensure CF1 exists
        cf1 = hourly_cfs[0]

        # Numerator starts with CF1
        numerator = np.array(cf1, dtype=float)

        # Apply ratios to CF2, CF3...
        for cf, r in zip(hourly_cfs[1:], self.ratios):
            numerator += r * cf

        # Denominator = 1 + sum of ratios
        denominator = 1 + sum(self.ratios)

        return numerator / denominator
  

    def grid_electricity_price_trend(self):
        """
        Electricity price trend over 8760 hours.

        price[h] = 1               if h is a peak hour
                = 1 - weighted_cf[h] otherwise

        Peak hours are zero-based (17 = 17:00–17:59).
        """

        # Compute weighted RES-E capacity factor (8760 values)
        weighted_cf = self.weighted_res_e_cf()

        # Hour of day (0–23 repeated)
        hour_of_day = np.arange(len(weighted_cf)) % 24

        # Identify peak hours
        is_peak_hour = np.isin(hour_of_day, self.peak_hours)

        # Apply pricing logic
        price = np.where(is_peak_hour, 1.0, 1.0 - weighted_cf)

        return price

    def grid_electricity_ghg_trend(self):
        """
        Electricity ghg intensity trend over 8760 hours.

        """

        # Compute weighted RES-E capacity factor (8760 values)
        weighted_cf = self.weighted_res_e_cf()


        # Apply pricing logic
        ghg_trend = 1.0 - weighted_cf

        return ghg_trend

    def purchase_price(self):
        """Scale the grid electricity price according to the price trend."""
        if self.avg_grid_price is None:
            raise ValueError("avg_grid_price must be set before calling this method.")
        price_trend = self.grid_electricity_price_trend()
        self.avg_price_trend = np.mean(price_trend)

        #return avg_trend, The values are different compared to the excel sheet as the avg_trend value is different, this is because in the excel sheet only peak change for day 1 was considered, here it is repeated each day
        return (price_trend / self.avg_price_trend) * self.avg_grid_price


    def sales_price(self):
        """Calculate the grid sales price by subtracting the difference from purchase price."""
        if self.difference is None:
            raise ValueError("difference must be set before calling this method.")
        return self.purchase_price() - self.difference


    def ghg_intensity(self):
        """Scale the grid electricity GHG intensity according to the trend."""
        if self.ghg_avg is None:
            raise ValueError("ghg_avg must be set before calling this method.")
        ghg_trend = self.grid_electricity_price_trend()
        self.avg_ghg_trend = np.mean(ghg_trend)
        return (ghg_trend / self.avg_ghg_trend) * self.ghg_avg


    def evaluate(self):
        """Run all core methods, store results as attributes, and return dictionary."""
        
        h_weighted_cf = self.weighted_res_e_cf()
        h_price_trend = self.grid_electricity_price_trend()
        h_purchase_price_trend = self.purchase_price()
        h_sales_price_trend = self.sales_price()
        h_ghg_trend = self.ghg_intensity()

        self.hourly_weighted_cf = h_weighted_cf
        self.hourly_price_trend = h_price_trend
        self.hourly_purchase_price_trend = h_purchase_price_trend
        self.hourly_sales_price_trend = h_sales_price_trend
        self.hourly_ghg_trend = h_ghg_trend

        return {
            "hourly_weighted_cf": h_weighted_cf,
            "hourly_price_trend":  h_price_trend,
            "hourly_purchase_price_trend": h_purchase_price_trend,
            "hourly_sales_price_trend": h_sales_price_trend,
            "hourly_ghg_trend": h_ghg_trend,
            "avg_ghg_trend": self.avg_ghg_trend,
            "avg_price_trend" :self.avg_price_trend
        }