RENEWABLE_ELECTRICITY_DOC = """
Renewable Electricity (RES-E) component for the HyTEA library.

The RenewableElectricity class represents a renewable electricity
generation source, such as wind or solar, within the HyTEA techno-economic
assessment framework.

The class uses an hourly capacity-factor time series together with the
installed renewable electricity capacity to calculate:

Hourly renewable electricity generation
Total cumulative annual electricity generation
Hourly cumulative electricity generation
Average capacity factor
Renewable electricity CAPEX
Renewable electricity OPEX

The calculated results can be accessed through the class attributes or
through the dictionary returned by evaluate().

Typical workflow

A renewable electricity model is normally used in the following order::

rese = RenewableElectricity()

rese.configure(
    config={
        "rese_type": "wind",
        "capacity_mw": 100,
        "capex_per_mw": 2500000,
        "opex_per_mw": 75000
    },
    csv_file="wind_cf.csv"
)

results = rese.evaluate()

The returned results dictionary contains the hourly generation,
cumulative generation, capacity factor, CAPEX, and OPEX.

The class can also be used through the HyTEA core model, where multiple
renewable electricity sources can be configured and evaluated
independently.

Configuration

Configuration can be supplied in one of three ways:

Directly as a Python dictionary using config.
From a YAML configuration file using config_file.
Using the class defaults when neither is provided.

A CSV file containing hourly capacity-factor data can be supplied using
csv_file.

Parameters

config : dict, optional
Python dictionary containing the renewable electricity configuration.

Supported configuration parameters include:

``rese_type``
    Renewable electricity technology.

    Supported values are:

    - ``"wind"``
    - ``"solar"``

    Default is ``"wind"``.

``capacity_mw``
    Installed renewable electricity capacity in MW.

    Default is ``100 MW``.

``capex_per_mw``
    Capital expenditure per MW of installed capacity in €/MW.

    If not provided, the class uses technology-specific defaults:

    - Wind: ``€2,500,000/MW``
    - Solar: ``€1,000,000/MW``

``opex_per_mw``
    Annual operating expenditure per MW of installed capacity in €/MW.

    If not provided, the class uses technology-specific defaults:

    - Wind: ``3%`` of wind CAPEX per MW
    - Solar: ``2%`` of solar CAPEX per MW

Example::

    config = {
        "rese_type": "wind",
        "capacity_mw": 100,
        "capex_per_mw": 2500000,
        "opex_per_mw": 75000
    }

config_file : str, optional
Path to a YAML configuration file.

If ``config`` is not provided and ``config_file`` is provided, the
YAML file is loaded using ``yaml.safe_load()``.

Example YAML structure::

    rese_type: wind
    capacity_mw: 100
    capex_per_mw: 2500000
    opex_per_mw: 75000

csv_file : str, optional
Path to the CSV file containing the hourly capacity-factor data.

If supplied, this file takes priority over the packaged default
sample capacity-factor file.

The CSV file must contain a column named ``cf``.

Example::

    hour,cf
    1,0.32
    2,0.41
    3,0.38
    ...

The ``cf`` values represent the hourly renewable electricity
capacity factor.
Hourly capacity-factor input

The class expects the CSV file to contain a column named cf.

The capacity factor is a dimensionless value representing the fraction
of installed capacity available during each hour.

For example, for an installed capacity of 100 MW:

capacity factor = 0.50

gives:

hourly generation = 0.50 × 100 MW = 50 MW

The hourly generation is therefore calculated from::

hourly_output_mw = hourly_capacity_factor × capacity_mw

The resulting hourly generation is stored in MW.

Attributes

rese_type : str
Renewable electricity technology type.

Default is ``"wind"``.

capacity_mw : float
Installed renewable electricity capacity in MW.

Default is ``100 MW``.

capex_per_mw : float
Capital expenditure per MW of installed capacity in €/MW.

opex_per_mw : float
Annual operating expenditure per MW of installed capacity in €/MW.

hourly_cf_file : str
Path to the CSV file containing the hourly capacity-factor data.

hourly_cf : numpy.ndarray
Hourly capacity-factor time series loaded from the CSV file.

hourly_output_mw : numpy.ndarray
Hourly renewable electricity generation in MW.

cumulative_energy_gwh_total : float
Total cumulative renewable electricity generation in GWh.

cumulative_energy_gwh_hourly : numpy.ndarray
Cumulative renewable electricity generation in GWh at each hour.

avg_capacity_factor : float
Average capacity factor over the supplied hourly time series.

capex : float
Total renewable electricity CAPEX in €.

opex : float
Total annual renewable electricity OPEX in €.

Methods

show_defaults()
Display the default renewable electricity parameters and their
associated units.

configure(config=None, config_file=None, csv_file=None)
Configure the renewable electricity model using a dictionary,
YAML file, or default values.

calculate_hourly_output()
Load the hourly capacity-factor data and calculate hourly
renewable electricity generation in MW.

cumulative_energy_gwh(hourly=False)
Calculate cumulative renewable electricity generation in GWh.

If ``hourly=False``, the total cumulative generation is returned.

If ``hourly=True``, an array containing cumulative generation at
each hour is returned.

average_capacity_factor()
Calculate the average capacity factor of the hourly capacity-factor
time series.

get_capex_opex()
Calculate total renewable electricity CAPEX and annual OPEX.

evaluate()
Run all core renewable electricity calculations and return the
results as a dictionary.

Method details

show_defaults()

Displays the default values used by the renewable electricity model.

Example::

    rese.show_defaults()

The displayed information includes:

- Renewable electricity type
- Installed capacity
- CAPEX
- OPEX
- Hourly capacity-factor file

configure()
~~~~~~~~~~~
Configures the renewable electricity model.

Configuration can be supplied directly as a dictionary::

    rese.configure(
        config={
            "rese_type": "wind",
            "capacity_mw": 100
        }
    )

Alternatively, a YAML file can be supplied::

    rese.configure(
        config_file="rese_config.yaml"
    )

An hourly capacity-factor CSV file can be supplied separately::

    rese.configure(
        config={
            "rese_type": "wind",
            "capacity_mw": 100
        },
        csv_file="wind_cf.csv"
    )

If no CSV file is provided, the class uses the packaged
``sample_wind_cf.csv`` file as the default input.

Technology-specific CAPEX and OPEX defaults are selected according to
``rese_type``.

For wind:

    CAPEX = €2,500,000/MW

    OPEX = 3% of CAPEX per MW

For solar:

    CAPEX = €1,000,000/MW

    OPEX = 2% of CAPEX per MW

calculate_hourly_output()

Reads the capacity-factor CSV file and calculates hourly renewable
electricity generation.

The calculation is::

hourly_output_mw = hourly_cf × capacity_mw

where:

hourly_cf is dimensionless
capacity_mw is in MW
hourly_output_mw is in MW

The hourly capacity-factor data are also stored in the
hourly_cf attribute.

Example::

hourly_output = rese.calculate_hourly_output()

The returned value is a NumPy array containing hourly generation in MW.

cumulative_energy_gwh()

Calculates cumulative renewable electricity generation.

The hourly generation is first calculated in MW. Because the model uses
hourly time steps, the numerical MW values correspond to MWh generated
during each one-hour period.

The cumulative energy is calculated as::

    cumulative_energy_gwh = cumsum(hourly_output_mw) / 1000

When ``hourly=False``:

    A single value representing total cumulative generation in GWh
    is returned.

Example::

    total_generation = rese.cumulative_energy_gwh()

When ``hourly=True``:

    A NumPy array containing cumulative generation at each hour is
    returned.

Example::

    cumulative_generation = rese.cumulative_energy_gwh(
        hourly=True
    )

average_capacity_factor()

Calculates the arithmetic mean of the hourly capacity-factor
time series.

The result is dimensionless.

Example::

average_cf = rese.average_capacity_factor()

For example, a result of:

0.35

corresponds to an average capacity factor of:

35%

get_capex_opex()

Calculates total renewable electricity CAPEX and annual OPEX based on
installed capacity.

CAPEX is calculated as::

    CAPEX = capacity_mw × capex_per_mw

OPEX is calculated as::

    OPEX = capacity_mw × opex_per_mw

The method returns a dictionary::

    {
        "capex": ...,
        "opex": ...
    }

CAPEX is expressed in € and OPEX is expressed as annual €.

Example::

    costs = rese.get_capex_opex()

evaluate()
~~~~~~~~~~
Runs all core renewable electricity calculations.

The method calculates:

1. Hourly renewable electricity generation
2. Total cumulative energy
3. Hourly cumulative energy
4. Average capacity factor
5. CAPEX
6. OPEX

The calculated values are stored as class attributes and returned as a
dictionary.

Example::

    results = rese.evaluate()

Returned results
----------------
The ``evaluate()`` method returns a dictionary with the following
structure::

    {
        "hourly_output_mw": ...,
        "cumulative_energy_gwh_total": ...,
        "cumulative_energy_gwh_hourly": ...,
        "avg_capacity_factor": ...,
        "capex": ...,
        "opex": ...
    }

The meaning and units of each output are:

``hourly_output_mw``
    NumPy array containing hourly renewable electricity generation
    in MW.

``cumulative_energy_gwh_total``
    Total renewable electricity generation over the modeled period
    in GWh.

``cumulative_energy_gwh_hourly``
    NumPy array containing cumulative renewable electricity generation
    in GWh at each hour.

``avg_capacity_factor``
    Average capacity factor as a dimensionless value.

``capex``
    Total renewable electricity CAPEX in €.

``opex``
    Annual renewable electricity OPEX in €.

Example
-------
Complete standalone example::

    from hytea.hytea_components.rese.rese_model import RenewableElectricity

    rese = RenewableElectricity()

    rese.configure(
        config={
            "rese_type": "wind",
            "capacity_mw": 100
        },
        csv_file="wind_cf.csv"
    )

    results = rese.evaluate()

    print(results["avg_capacity_factor"])
    print(results["capex"])
    print(results["opex"])

    hourly_generation = results["hourly_output_mw"]
    cumulative_generation = results[
        "cumulative_energy_gwh_hourly"
    ]

Multiple renewable sources
--------------------------
The ``RenewableElectricity`` class represents one renewable electricity
source at a time.

For example, a HyTEA system can create separate instances for wind and
solar:

    wind = RenewableElectricity()

    solar = RenewableElectricity()

Each source can have its own:

- Technology type
- Installed capacity
- Capacity-factor profile
- CAPEX
- OPEX

The individual source results can then be combined by the HyTEA core
model.

Relationship with HyTEA Core
-----------------------------
Within ``HyTEACore``, each configured renewable electricity source is
handled independently.

The core model:

1. Reads the ``rese_sources`` configuration.
2. Creates a ``RenewableElectricity`` instance for each source.
3. Configures each source.
4. Evaluates each source.
5. Stores the resulting output in ``rese_results``.

This allows multiple renewable sources, such as wind and solar, to be
used within the same HyTEA scenario.

Units summary
-------------
+-------------------------------+----------------+
| Parameter / output            | Unit           |
+-------------------------------+----------------+
| ``capacity_mw``               | MW             |
| ``capex_per_mw``              | €/MW           |
| ``opex_per_mw``               | €/MW/year      |
| ``hourly_cf``                 | dimensionless  |
| ``hourly_output_mw``          | MW             |
| ``cumulative_energy_gwh``     | GWh            |
| ``avg_capacity_factor``       | dimensionless  |
| ``capex``                     | €              |
| ``opex``                      | €/year         |
+-------------------------------+----------------+

Notes
-----
The class assumes that the supplied capacity-factor data represent
hourly values.

The CSV input must contain a column named ``cf``.

The installed renewable electricity capacity is specified in MW.

Hourly renewable electricity generation is calculated in MW and is
used as the basis for the cumulative energy calculation.

The ``RenewableElectricity`` class performs the renewable generation
and basic renewable techno-economic calculations. Additional system
operations, such as grid integration, electrolyser dispatch, hydrogen
storage, transport, and system-level economics, are handled by other
HyTEA components.
"""
