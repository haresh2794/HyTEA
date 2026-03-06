import numpy as np


class DiscountingModel:
    """
    Generic discounting model for time-series values.

    Can be used for:
    - costs
    - hydrogen production
    - electricity generation
    - emissions

    Supports:
    - multi-year construction
    - recurring annual values during operation
    - additional values at specified years
    - optional decommissioning at end of project life
    """

    def __init__(self):

        # inputs
        self.discount_rate = None
        self.construction_years = None
        self.project_life_years = None

        self.initial_value = 0.0
        self.annual_value = 0.0
        self.additional_values = {}

        self.decommissioning_fraction = 0.0

        # outputs
        self.years = None
        self.values = None
        self.discount_factors = None
        self.discounted_values = None

        self.operation_start_year = None
        self.decommissioning_year = None
        self.decommissioning_value = None
        self.decommissioning_pv = None

        self.total_present_value = None

    def configure(self, config):

        self.discount_rate = config.get("discount_rate", 0.06)
        self.construction_years = config.get("construction_years", 1)
        self.project_life_years = config.get("project_life_years", 20)

        self.initial_value = config.get("initial_value", 0.0)
        self.annual_value = config.get("annual_value", 0.0)

        self.additional_values = config.get("additional_values", {})
        self.decommissioning_fraction = config.get("decommissioning_fraction", 0.0)

    def build_values(self):

        if self.construction_years < 1:
            raise ValueError("construction_years must be at least 1.")

        self.operation_start_year = self.construction_years
        self.decommissioning_year = self.construction_years + self.project_life_years

        self.years = np.arange(0, self.decommissioning_year + 1)
        values = np.zeros(len(self.years), dtype=float)

        # spread initial value equally across construction years
        annual_construction_value = self.initial_value / self.construction_years
        values[0:self.construction_years] += annual_construction_value

        # recurring annual value starts after construction
        if self.project_life_years >= 1:
            values[
                self.operation_start_year : self.operation_start_year + self.project_life_years
            ] += self.annual_value

        # additional values at specific years
        # assumed absolute year numbering from year 0
        for year, value in self.additional_values.items():
            if 0 <= year <= self.decommissioning_year:
                values[year] += value

        # decommissioning at end of operating life
        self.decommissioning_value = self.initial_value * self.decommissioning_fraction
        values[self.decommissioning_year] += self.decommissioning_value

        self.values = values
        return self.values

    def build_discount_factors(self):

        self.discount_factors = 1 / ((1 + self.discount_rate) ** self.years)
        return self.discount_factors

    def evaluate(self):

        self.build_values()
        self.build_discount_factors()

        self.discounted_values = self.values * self.discount_factors
        self.total_present_value = float(np.sum(self.discounted_values))

        self.decommissioning_pv = float(
            self.decommissioning_value /
            ((1 + self.discount_rate) ** self.decommissioning_year)
        )

        return {
            "years": self.years,
            "values": self.values,
            "discount_factors": self.discount_factors,
            "discounted_values": self.discounted_values,
            "construction_years": self.construction_years,
            "operation_start_year": self.operation_start_year,
            "decommissioning_year": self.decommissioning_year,
            "decommissioning_value": self.decommissioning_value,
            "decommissioning_pv": self.decommissioning_pv,
            "total_present_value": self.total_present_value,
        }