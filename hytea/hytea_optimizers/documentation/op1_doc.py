OP1_MIN_ELECTROLYSER_CAPACITY_DOC = """
OP1 – Minimum Electrolyser Capacity with Fixed Hydrogen Storage
===============================================================

Determine the minimum electrolyser capacity required to satisfy hydrogen
demand in all 8,760 hours of the year for a fixed hydrogen storage
capacity and other config parameters.

The function evaluates a sequence of electrolyser capacities over a
specified capacity range. For each capacity, it creates a copy of the
base HyTEA configuration, changes only the electrolyser capacity, runs
the complete HyTEA model, and evaluates the resulting hourly hydrogen
supply against the hourly hydrogen demand.

The first electrolyser capacity for which hydrogen supply satisfies
demand in every hour is identified as the minimum feasible capacity.

Parameters
----------
base_config : dict
    Base HyTEA configuration dictionary.

    The configuration must contain:

        - ``storage``
        - ``storage_sizing_option``
        - ``storage_capacity_tonnes``
        - ``hourly_demand_kgph``
        - ``electrolyser``

    The function does not modify ``base_config`` directly. A deep copy
    is created for each electrolyser capacity evaluated.

min_capacity : float, optional
    Minimum electrolyser capacity to evaluate, in MW.

    Default:
        1.0 MW

max_capacity : float, optional
    Maximum electrolyser capacity to evaluate, in MW.

    Default:
        10.0 MW

capacity_step : float, optional
    Increment between successive electrolyser capacity values, in MW.

    Default:
        0.5 MW

tolerance_kg : float, optional
    Numerical tolerance used when determining whether hourly hydrogen
    supply satisfies demand.

    An hourly deficit is counted only when:

        supply - demand < -tolerance_kg

    Default:
        1e-6 kg

Requirements
------------

The storage configuration must use fixed storage sizing:

    storage_sizing_option = "Tonnes"

A fixed storage capacity must also be supplied:

    storage_capacity_tonnes

The base configuration must contain:

    hourly_demand_kgph

The hourly demand profile must contain exactly 8,760 values.

Capacity search
---------------

The electrolyser capacity values are generated from ``min_capacity`` to
``max_capacity`` using ``capacity_step``.

For example:

    min_capacity = 1.0
    max_capacity = 3.0
    capacity_step = 0.5

produces:

    1.0, 1.5, 2.0, 2.5, 3.0 MW

Each capacity is evaluated independently.

Configuration handling
----------------------

For each electrolyser capacity, the base configuration is copied using
``deepcopy``.

Only the following configuration value is changed:

    config["electrolyser"]["electro_capacity"]

All other configuration parameters remain unchanged.

HyTEA model execution
---------------------

For every candidate electrolyser capacity, a new ``HyTEACore`` instance
is created.

The workflow is:

    model = HyTEACore()
    model.configure(config)
    result = model.evaluate()

The hydrogen supply profile is then obtained directly from:

    model.h2_supply_kgph

This is the hydrogen supply stream used by the HyTEA Core annual hydrogen
balance.

Hourly hydrogen balance
-----------------------

The function compares hourly hydrogen supply against the specified
hourly hydrogen demand.

The hourly difference is:

    hourly_difference_kg
        = supply_kgph - demand_kgph

An hourly deficit occurs when:

    hourly_difference_kg < -tolerance_kg

The number of deficit hours is:

    number_of_deficit_hours

The hourly deficit is calculated as:

    hourly_deficit_kg
        = max(demand_kgph - supply_kgph, 0)

The total annual hydrogen deficit is:

    total_deficit_kg
        = sum(hourly_deficit_kg)

Demand is considered satisfied for all 8,760 hours when:

    number_of_deficit_hours == 0

Worst hourly results
--------------------

The function also calculates the minimum and maximum hourly
supply-demand differences.

Minimum hourly difference:

    minimum_hourly_difference_kg
        = min(hourly_difference_kg)

Maximum hourly difference:

    maximum_hourly_difference_kg
        = max(hourly_difference_kg)

These values indicate the worst hourly hydrogen deficit and the largest
hourly hydrogen surplus, respectively.

Annual hydrogen results
-----------------------

The annual hydrogen balance is obtained from the HyTEA evaluation
result.

The function extracts:

    annual_production_kg
    annual_supply_kg
    annual_demand_kg

These are reported as:

    H2 produced (kg)
    H2 supplied (kg)
    H2 demand (kg)

Feasibility criterion
---------------------

A candidate electrolyser capacity is considered feasible only if
hydrogen demand is satisfied in every one of the 8,760 hours.

The first feasible capacity encountered in the capacity search is
selected as:

    minimum_electrolyser_capacity_mw

Once the first feasible capacity is found, the capacity search stops.

Therefore, the function returns the first feasible capacity according
to the specified capacity range and step size.

Results
-------

The function returns a dictionary containing:

``minimum_electrolyser_capacity_mw``
    Minimum feasible electrolyser capacity in MW.

    Returns ``None`` if no tested capacity satisfies hydrogen demand in
    all 8,760 hours.

``storage_capacity_t``
    Fixed hydrogen storage capacity used in the analysis, in tonnes.

``results``
    Pandas DataFrame containing the results for every electrolyser
    capacity evaluated before the first feasible capacity was found.

``minimum_result``
    Complete HyTEA result dictionary corresponding to the first feasible
    electrolyser capacity.

    Returns ``None`` if no feasible capacity is found.

Results DataFrame
-----------------

The ``results`` DataFrame contains the following columns:

    Electrolyser capacity (MW)
    Storage capacity (t)
    H2 produced (kg)
    H2 demand (kg)
    H2 supplied (kg)
    Number of deficit hours
    Total H2 deficit (kg)
    Minimum hourly supply-demand difference (kg)
    Maximum hourly supply-demand difference (kg)
    Demand satisfied all 8760 hours

No-feasible-capacity case
-------------------------

If none of the tested electrolyser capacities satisfies hydrogen demand
in all 8,760 hours, the function returns:

    minimum_electrolyser_capacity_mw = None

and:

    minimum_result = None

The results DataFrame still contains the evaluation results for all
tested capacities.

Typical usage
-------------

Example:

    result = op1_min_electrolyser_capacity(
        base_config,
        min_capacity=1.0,
        max_capacity=10.0,
        capacity_step=0.5
    )

The minimum feasible capacity can then be obtained using:

    result["minimum_electrolyser_capacity_mw"]

The capacity-scan results can be obtained using:

    result["results"]

The complete HyTEA result for the minimum feasible capacity can be
obtained using:

    result["minimum_result"]

Purpose within HyTEA
--------------------

OP1 is an optimisation/sizing analysis that determines the minimum
electrolyser capacity required for a fixed hydrogen storage capacity
while maintaining hourly hydrogen-demand satisfaction throughout the
year.

The optimisation varies only electrolyser capacity. Storage capacity
and all other model parameters remain fixed.
"""