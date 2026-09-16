GRID_DOC = """
Grid Electricity Component
==========================

Overview
--------
The Grid component represents the grid electricity system used in HyTEA.

The component calculates:

* Weighted renewable electricity capacity factor
* Hourly grid electricity price trend
* Hourly grid electricity purchase price
* Hourly grid electricity sales price
* Hourly grid electricity GHG intensity

The Grid component can be configured using a Python dictionary, a YAML
configuration file, or the default configuration values.

Main Class
----------
Grid

Example
-------
from hytea.hytea_components.grid.grid_model import Grid

grid = Grid()

grid.configure(
    config={
        "ratios": [1],
        "avg_grid_price": 100,
        "difference": 50,
        "ghg_avg": 234,
        "peak_hours": (17, 18)
    }
)

results = grid.evaluate()


Configuration
-------------
The Grid component accepts the following configuration parameters.

ratios
------
Type:
    list

Default:
    [0]

Description:
    Ratios used to calculate the weighted renewable electricity
    capacity factor.

    The first capacity factor is treated as the reference capacity
    factor. Each ratio corresponds to the subsequent capacity factor.

    For example:

        ratios = [0.5, 0.5]

    corresponds to:

        Weighted CF =
        (CF1 + 0.5*CF2 + 0.5*CF3) / (1 + 0.5 + 0.5)


avg_grid_price
---------------
Type:
    float

Unit:
    EUR/MWh

Default:
    100

Description:
    Average grid electricity purchase price used to scale the
    hourly electricity price trend.


difference
----------
Type:
    float

Unit:
    EUR/MWh

Default:
    50

Description:
    Difference between the grid electricity purchase price and
    the grid electricity sales price.

    The sales price is calculated as:

        Sales price = Purchase price - Difference


ghg_avg
-------
Type:
    float

Unit:
    gCO2/kWh

Default:
    234

Description:
    Average grid electricity GHG intensity used to scale the
    hourly GHG intensity trend.


peak_hours
----------
Type:
    tuple

Unit:
    hour of day (0-23)

Default:
    (17, 18)

Description:
    Hours identified as peak electricity price hours.

    The hours use zero-based indexing. For example:

        17 = 17:00-17:59
        18 = 18:00-18:59


hourly_cf_mul
-------------
Type:
    numpy array

Expected shape:
    (8760, n_sources)

Description:
    Hourly capacity factor data used to calculate the weighted
    renewable electricity capacity factor.

    If hourly_cf_mul is not supplied during configuration, the
    component loads the default hourly capacity factor data from:

        hytea.data/hourly_cf_mul.csv


Configuration Methods
---------------------
configure(config=None, hourly_cf_mul=None, config_file=None)

Loads the Grid configuration.

Parameters
----------
config:
    dict, optional

    Python dictionary containing the Grid configuration.

hourly_cf_mul:
    array-like, optional

    User-provided hourly capacity factor data.

config_file:
    str, optional

    Path to a YAML configuration file.

If no configuration or hourly capacity factor data are supplied,
the component uses its default values and packaged hourly capacity
factor data.


Methods
-------
show_defaults()
    Displays the default Grid configuration parameters and units.

configure()
    Configures the Grid component using a dictionary, YAML file,
    or default values.

weighted_res_e_cf()
    Calculates the weighted hourly renewable electricity capacity
    factor.

grid_electricity_price_trend()
    Calculates the normalised hourly grid electricity price trend.

grid_electricity_ghg_trend()
    Calculates the normalised hourly grid electricity GHG trend.

purchase_price()
    Calculates the hourly grid electricity purchase price.

sales_price()
    Calculates the hourly grid electricity sales price.

ghg_intensity()
    Calculates the hourly grid electricity GHG intensity.

evaluate()
    Runs all Grid calculations and returns the results.


Weighted Renewable Electricity Capacity Factor
-----------------------------------------------
The weighted renewable electricity capacity factor is calculated
using the available hourly capacity factor profiles and the
specified ratios.

For capacity factors CF1, CF2, CF3, etc.:

    Weighted CF =
    (CF1 + r1*CF2 + r2*CF3 + ...)
    /
    (1 + r1 + r2 + ...)

where:

    CF1
        First/reference capacity factor.

    CF2, CF3, ...
        Additional capacity factor profiles.

    r1, r2, ...
        Ratios specified in the configuration.

The resulting weighted capacity factor contains one value for
each hour in the input data.


Grid Electricity Price Trend
----------------------------
The hourly grid electricity price trend is calculated using the
weighted renewable electricity capacity factor.

For each hour:

    Price trend = 1

if the hour is a specified peak hour.

Otherwise:

    Price trend = 1 - Weighted CF

Peak hours are identified using the configured peak_hours tuple.

The default peak hours are:

    (17, 18)


Grid Electricity Purchase Price
-------------------------------
The hourly purchase price is calculated by scaling the normalised
grid electricity price trend to the configured average grid
electricity price.

First, the average price trend is calculated:

    Average price trend = mean(price trend)

The hourly purchase price is then:

    Purchase price =
    (Price trend / Average price trend)
    * Average grid price

The resulting values are in EUR/MWh.


Grid Electricity Sales Price
----------------------------
The grid electricity sales price is calculated by subtracting the
configured difference from the hourly purchase price.

    Sales price =
    Purchase price - Difference

The resulting values are in EUR/MWh.


Grid Electricity GHG Intensity
------------------------------
The hourly grid electricity GHG intensity is calculated by scaling
the GHG trend to the configured average grid GHG intensity.

The GHG trend is based on the weighted renewable electricity
capacity factor:

    GHG trend = 1 - Weighted CF

The average GHG trend is calculated as:

    Average GHG trend = mean(GHG trend)

The hourly GHG intensity is then:

    GHG intensity =
    (GHG trend / Average GHG trend)
    * Average GHG intensity

The resulting values are in gCO2/kWh.


Evaluation
----------
The evaluate() method runs all Grid calculations and stores the
results as class attributes.

The following calculations are performed:

1. Weighted renewable electricity capacity factor
2. Grid electricity price trend
3. Grid electricity purchase price
4. Grid electricity sales price
5. Grid electricity GHG intensity

Example:

    results = grid.evaluate()


Outputs
-------
The evaluate() method returns a dictionary containing:

hourly_weighted_cf
    Hourly weighted renewable electricity capacity factor.

hourly_price_trend
    Normalised hourly grid electricity price trend.

hourly_purchase_price_trend
    Hourly grid electricity purchase price in EUR/MWh.

hourly_sales_price_trend
    Hourly grid electricity sales price in EUR/MWh.

hourly_ghg_trend
    Hourly grid electricity GHG intensity in gCO2/kWh.

avg_ghg_trend
    Average value of the GHG trend used for scaling.

avg_price_trend
    Average value of the price trend used for scaling.


Class Attributes
----------------
After evaluate(), the following attributes contain the calculated
results:

hourly_weighted_cf
    Hourly weighted renewable electricity capacity factor.

hourly_price_trend
    Normalised hourly electricity price trend.

hourly_purchase_price_trend
    Hourly grid electricity purchase price.

hourly_sales_price_trend
    Hourly grid electricity sales price.

hourly_ghg_trend
    Hourly grid electricity GHG intensity.

avg_price_trend
    Average hourly price trend.

avg_ghg_trend
    Average hourly GHG trend.


Default Values
--------------
The default Grid configuration is:

    ratios:
        [0]

    avg_grid_price:
        100 EUR/MWh

    difference:
        50 EUR/MWh

    ghg_avg:
        234 gCO2/kWh

    peak_hours:
        (17, 18)

    hourly_cf_mul:
        Loaded from the packaged hourly_cf_mul.csv file.


Accessing Documentation
-----------------------
The Grid class documentation can be accessed using Python's
help() function:

    from hytea.hytea_components.grid.grid_model import Grid

    help(Grid)

The documentation can also be accessed using:

    print(Grid.__doc__)


Typical Workflow
----------------
A typical Grid workflow is:

    from hytea.hytea_components.grid.grid_model import Grid

    grid = Grid()

    grid.configure(
        config={
            "ratios": [1],
            "avg_grid_price": 100,
            "difference": 50,
            "ghg_avg": 234,
            "peak_hours": (17, 18)
        }
    )

    results = grid.evaluate()

The results can then be accessed using:

    results["hourly_weighted_cf"]

    results["hourly_purchase_price_trend"]

    results["hourly_sales_price_trend"]

    results["hourly_ghg_trend"]


Notes
-----
The Grid component uses 8760 hourly values when the packaged
hourly capacity factor dataset is used.

Peak hours are specified using zero-based hour-of-day indexing.

The hourly electricity price trend and GHG intensity trend are
derived from the weighted renewable electricity capacity factor.
"""