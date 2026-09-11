HYDROGEN_TRUCK_TRANSPORT_DOC = """
HydrogenTruckTransport
======================

Hydrogen truck transportation model for estimating the technical, economic,
and environmental performance of transporting hydrogen by road.

The model supports:

    - Diesel tractor trucks
    - Fuel-cell electric tractor trucks (FCEV_now and FCEV_2030)
    - Compressed hydrogen trailers
    - Liquid hydrogen trailers
    - Hydrogen compression/booster requirements
    - Minimum truck fleet sizing
    - Annual hydrogen transported
    - Annual truck mileage
    - Truck and trailer CAPEX
    - Truck and trailer OPEX
    - Fuel consumption and fuel cost
    - Driver and employee costs
    - Trailer recertification costs
    - Trailer operation and maintenance costs
    - Fuel-related GHG emissions

The model operates primarily on an annual basis, while fleet sizing uses
an hourly hydrogen mass-flow profile when one is supplied.

Typical workflow
----------------

Create and configure the transport model:

    transport = HydrogenTruckTransport()

    transport.configure({
        "truck_type": "Diesel",
        "transport_method": "Compressed",
        "P0_bar": 15,
        "P1_bar": 300,
        "P2_bar": 350,
        "Q1_kgph": 72.29,
        "Q2_kgph": 54.17,
        "distance_km": 100,
        "truck_speed_kmh": 60,
    })

Then evaluate the configured system:

    results = transport.evaluate()

The returned ``results`` dictionary contains the principal per-truck,
fleet-level, booster, hydrogen throughput, and transportation cost metrics.

Configuration
-------------

The ``configure()`` method accepts either a Python dictionary or a YAML
configuration file.

Dictionary:

    transport.configure(config)

YAML file:

    transport.configure(config_file="transport.yaml")

If neither is supplied, an empty configuration is used and model defaults
are applied.

Core transport parameters
-------------------------

``P0_bar``
    Electrolyser hydrogen outlet pressure in bar.

``P1_bar``
    Hydrogen storage pressure in bar.

``P2_bar``
    Hydrogen transport/trailer pressure in bar.

``Q1_kgph``
    Maximum hydrogen flow rate between P0 and P1 in kg/h.

``Q2_kgph``
    Maximum hydrogen flow rate between P1 and P2 in kg/h.

``distance_km``
    One-way transportation distance between the hydrogen production/storage
    facility and the destination.

``truck_speed_kmh``
    Truck travelling speed in km/h.

Default values are:

    P0_bar = 15 bar
    P1_bar = 300 bar
    P2_bar = 350 bar
    Q1_kgph = 72.29 kg/h
    Q2_kgph = 54.17 kg/h
    distance_km = 100 km
    truck_speed_kmh = 60 km/h

Truck types
-----------

The model supports three tractor configurations:

``Diesel``
    Conventional diesel tractor.

``FCEV_now``
    Fuel-cell electric tractor representing the current FCEV case.

``FCEV_2030``
    Fuel-cell electric tractor representing the 2030 FCEV case.

Each truck type has default values for:

    - Tractor CAPEX
    - Specific fuel consumption
    - Fuel price
    - Fuel-related GHG intensity
    - Number of drivers
    - Other employees per truck
    - Employee salary

These values can be overridden through the configuration dictionary.

Transport methods
-----------------

Two trailer/transport methods are supported:

``Compressed``
    Compressed gaseous hydrogen transported using high-pressure trailers.

``Liquid``
    Liquid hydrogen transported using liquid-hydrogen trailers.

The selected method is controlled by:

    "transport_method": "Compressed"

or:

    "transport_method": "Liquid"

Compressed hydrogen transport
-----------------------------

For compressed hydrogen, the trailer load capacity and trailer CAPEX are
selected from a pressure-dependent table.

The available reference transport pressures are:

    200 bar
    250 bar
    350 bar
    450 bar
    500 bar

If the requested ``P2_bar`` does not exactly match one of these values,
the nearest available pressure is used to determine the trailer load
capacity and trailer CAPEX.

The compressed trailer defaults include:

    - Trailer O&M cost per km
    - Trailer filling time
    - Hydrogen load capacity
    - Trailer CAPEX
    - Annual recertification fraction

Liquid hydrogen transport
-------------------------

For liquid hydrogen transport, the model uses:

    - A fixed base trailer CAPEX
    - A default trailer filling time
    - Trailer O&M cost per km
    - Trailer recertification fraction
    - A configurable trailer hydrogen load

The default liquid trailer hydrogen load is 4600 kg.

No transport booster compressor is included for liquid hydrogen transport.

Hydrogen compression / booster
------------------------------

For compressed hydrogen transport, a booster compressor is required when:

    P2_bar > P1_bar

The model distinguishes between:

    1. Storage enabled:
       P0 -> P1 compression is handled by the storage system, while the
       transport booster handles P1 -> P2.

    2. Storage not requiring an intermediate compression stage:
       The transport compressor handles the complete P0 -> P2 compression.

The booster model calculates:

    - Specific compressor CAPEX
    - Booster CAPEX
    - Booster OPEX
    - Specific electricity consumption

Specific compressor CAPEX is calculated using pressure-dependent
interpolation between the available compressor reference pressures.

Booster specific energy consumption is calculated from a lookup table
based on the electrolyser outlet pressure ``P0_bar`` and the target
pressure.

Minimum truck fleet calculation
-------------------------------

The ``_calc_min_trailers()`` method calculates the minimum number of
trailers/trucks required to satisfy the hydrogen transport profile.

The calculation uses hourly hydrogen mass flow and accounts for:

    - Hydrogen entering trailer filling
    - Carry-over hydrogen from the previous hour
    - Trailer loading capacity
    - Completely filled trailers
    - Trailers currently being filled
    - Trailers in transit
    - Round-trip transportation time
    - Trailer filling time

If no hourly mass-flow profile is supplied, the model creates a constant
8760-hour profile using ``Q2_kgph``.

The basic hourly logic is:

    mass entering filling
        = current-hour hydrogen flow + previous-hour carry-over

    trailers required
        = mass entering filling / trailer load capacity

    completely filled trailers
        = floor(trailers required)

    trailers being filled
        = ceil(trailers required)

Carry-over hydrogen is retained and added to the following hour.

Transit time is calculated from:

    one-way travel time
    + trailer filling time
    + return travel time
    + 1 hour

The number of trailers required in transit is determined from previously
dispatched, completely filled trailers within the calculated transit
window.

The minimum fleet size is the maximum total number of trailers required
in any hour:

    number_of_trucks
        = max(trailers in transit + trailers being filled)

The method also stores hourly fleet-sizing arrays as object attributes
for reporting and debugging.

Annual transport metrics
------------------------

The ``_calc_annual_truck_metrics()`` method calculates annual hydrogen
transportation metrics from the hourly trailer dispatch results.

The total annual hydrogen transported is:

    total_annual_h2_transported_kg
        = number of completely filled trailers
          × trailer load capacity

Hydrogen transported per truck per year is:

    tonnes_per_truck_kg
        = total annual hydrogen transported
          / number of trucks

The annual number of turns per truck is:

    turns_per_truck
        = total completed trailer fills
          / number of trucks

The total number of completed trailer fills is stored as:

    number_of_fills

The annual round-trip distance per truck is:

    annual_distance_per_truck_km
        = total completed trailer fills
          × 2 × one-way distance
          / number of trucks

The total annual fleet distance is:

    total_annual_fleet_distance
        = total completed trailer fills
          × 2 × one-way distance

Economic calculations
---------------------

The ``evaluate()`` method calculates transportation costs at both
individual-truck and fleet level.

Trailer CAPEX per truck:

    capex_per_truck
        = trailer CAPEX

Tractor CAPEX is converted to an annual OPEX-equivalent using:

    tractor_capex_as_opex
        = tractor CAPEX × 0.8 / 5

The factor 0.8 accounts for the assumed resale value and the five-year
period used for annualisation.

Fuel cost per truck is:

    fuel_per_truck
        = specific fuel consumption
          × fuel price
          × annual distance

Salary per truck is:

    salary_per_truck
        = (drivers per truck + other employees per truck)
          × employee salary

Trailer recertification cost is:

    recertification_per_truck
        = trailer CAPEX × recertification fraction

Other trailer O&M cost is:

    other_o_n_m_per_truck
        = trailer O&M cost per km
          × annual distance

Total OPEX per truck is:

    opex_per_truck
        = tractor annualised CAPEX
          + fuel cost
          + salary
          + recertification
          + other O&M

Fleet-level costs are calculated by multiplying the relevant per-truck
value by the required number of trucks.

Booster economics
-----------------

For compressed hydrogen transportation with a positive booster
requirement:

    booster CAPEX
        = specific booster CAPEX × Q2_kgph

Booster annual OPEX is:

    booster OPEX
        = booster CAPEX × 0.02

Total transportation CAPEX is:

    transportation_capex
        = booster CAPEX + truck fleet CAPEX

Total transportation OPEX is:

    transportation_opex
        = booster OPEX + truck fleet OPEX

If no compressed-hydrogen booster is required, the booster CAPEX and
booster OPEX are zero.

For liquid hydrogen transport, booster CAPEX and booster OPEX are zero.

Environmental calculation
--------------------------

Fuel-related GHG emissions are calculated using the tractor fuel
consumption, fuel GHG intensity, and annual distance.

Fuel emissions per truck are converted from grams of CO2 to tonnes of
CO2 per year.

Fleet emissions are:

    total_ghg_per_year
        = fuel emissions per truck
          × number of trucks

For FCEV configurations, the default fuel GHG intensity is zero in the
current model configuration.

Important model attributes
---------------------------

After configuration and evaluation, the object contains key input,
intermediate, and output attributes including:

Transport configuration:

    truck_type
    transport_method
    P0_bar
    P1_bar
    P2_bar
    Q1_kgph
    Q2_kgph
    distance_km
    truck_speed_kmh
    number_of_trucks

Trailer:

    trailer_load_kg
    trailer_capex
    trailer_fill_time_h
    trailer_om_per_km
    recertification_fraction

Booster:

    boost_spec_capex
    sec_boost_kWh_per_kg
    booster_capex_total
    booster_opex_total
    booster_spec_elec_consumption

Annual transport:

    total_annual_h2_transported_kg
    tonnes_per_truck_kg
    turns_per_truck
    number_of_fills
    annual_distance_per_truck_km
    total_annual_fleet_distance

Truck economics:

    capex_per_truck
    tractor_capex_as_opex
    fuel_per_truck
    salary_per_truck
    recertification_per_truck
    other_o_n_m_per_truck
    opex_per_truck

Fleet economics:

    truck_fleet_capex
    truck_fleet_opex
    transportation_capex
    transportation_opex

Environmental:

    total_ghg_per_year

Hourly fleet-sizing outputs
---------------------------

When ``_calc_min_trailers()`` is executed, the following hourly arrays
are stored:

    mass_into_fill_kg
    trailers_needed_each_hour
    trailers_completely_filled_each_hour
    trailers_being_filled_each_hour
    mass_to_next_hour_fill_kg
    trailers_in_transit_each_hour
    total_trailers_needed_each_hour

The calculated total transit time is stored as:

    total_transit_time_h

These arrays are useful for analysing trailer utilisation, filling,
dispatch, and fleet requirements over the year.

Evaluate output
---------------

``evaluate()`` returns a dictionary containing:

    annual_distance_per_truck_km
    capex_per_truck
    tractor_capex_as_opex
    fuel_per_truck
    salary_per_truck
    recertification_per_truck
    other_o_n_m_per_truck
    opex_per_truck
    number_of_trucks
    truck_fleet_capex
    truck_fleet_opex
    transportation_capex
    transportation_opex
    total_ghg_per_year
    booster_capex_total
    booster_opex_total
    boost_spec_capex
    booster_spec_elec_consumption
    P2_bar
    total_fuel
    total_salary
    total_recertification
    total_other_o_n_m
    total_tractor_capex_as_opex
    total_annual_h2_transported_kg
    number_of_fills
    total_annual_fleet_distance

Units
-----

Pressure:
    bar

Hydrogen flow:
    kg/h

Hydrogen transported:
    kg/year

Distance:
    km or km/year

Truck speed:
    km/h

Fuel/electricity:
    kWh/km or kWh/kg

CAPEX:
    EUR

OPEX:
    EUR/year

Fuel cost:
    EUR/year

GHG emissions:
    tCO2/year

Booster specific CAPEX:
    EUR/(kg/h)

Booster specific electricity:
    kWh/kg H2

Model role within HyTEA
------------------------

HydrogenTruckTransport represents the road transportation component of
the HyTEA hydrogen supply chain.

Within the broader HyTEA workflow, the transport model receives hydrogen
production/storage information from the upstream system and determines
the truck fleet and transportation requirements needed to deliver the
hydrogen.

The model can therefore be used downstream of the electrolyser and
hydrogen storage models to calculate:

    - Hydrogen transport capacity
    - Required truck fleet size
    - Annual hydrogen transported
    - Truck utilisation
    - Transportation CAPEX
    - Transportation OPEX
    - Booster compression requirements
    - Transport-related GHG emissions

The resulting transportation metrics can subsequently be incorporated
into the wider HyTEA techno-economic assessment.
"""