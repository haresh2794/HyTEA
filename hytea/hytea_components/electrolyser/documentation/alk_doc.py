ALK_ELECTROLYSER_DOC = """
ALKElectrolyser
===============

Alkaline electrolyser model for the HyTEA library.

The ALKElectrolyser represents a single electrolyser supplied by one or
more electricity streams at hourly resolution.

The model calculates:

- Hourly electricity consumption
- Hydrogen production
- Electrolyser efficiency
- Electrolyser specific energy consumption (SEC)
- Compression energy
- Hydrogen transport energy
- Water consumption
- Electricity curtailment
- Capacity factor
- Electrolyser CAPEX and OPEX
- Stream-level electricity and hydrogen allocation

Power is represented in kW and energy in kWh unless otherwise stated.

Typical workflow
----------------

Create the electrolyser:

    electrolyser = ALKElectrolyser()

Configure it:

    electrolyser.configure(config={
        "electro_capacity": 10,
        "outlet_pressure": 15
    })

Provide an hourly electricity DataFrame:

    results = electrolyser.evaluate(power_df)

The ``power_df`` DataFrame should contain hourly electricity available
from one or more electricity streams.

Configuration
-------------

The ``configure()`` method accepts either a Python dictionary or a YAML
configuration file.

Main parameters
---------------

``electro_capacity``
    Electrolyser installed capacity in MW.

``avg_sec_electrolyser``
    Average electrolyser specific energy consumption in kWh/kg H2.

    If not provided, it is calculated from the electrolyser capacity.

``water_consumption``
    Specific water consumption in m3/kg H2.

``annual_improvement``
    Annual improvement factor used in the electrolyser efficiency
    calculation.

``install_year``
    Electrolyser installation year used to calculate the efficiency
    improvement term.

``LHV``
    Lower heating value of hydrogen in kWh/kg H2.

``spec_capex``
    Electrolyser specific CAPEX in €/kW.

``opex_per``
    Electrolyser OPEX as a fraction of CAPEX.

``outlet_pressure``
    Hydrogen outlet pressure in bar.

Storage and downstream energy
-----------------------------

The electrolyser model can include the energy required for hydrogen
compression/liquefaction and transport.

``storage_method``
    Hydrogen storage technology.

Supported options are:

- ``Compressed Tanks``
- ``Salt cavern``
- ``Lined rock cavern``
- ``Liquid H2``

``pout_bar``
    Storage pressure in bar.

``sec_compression``
    Compression or liquefaction specific energy consumption in kWh/kg H2.

If not supplied, the value is calculated according to the storage method.

``transport_pressure``
    Hydrogen transport pressure in bar.

``sec_transport``
    Transport-related specific energy consumption in kWh/kg H2.

If not supplied, this is calculated from the transport and storage
pressures.

Actual electrolyser input capacity
----------------------------------

The method ``get_actual_input_capacity_kW()`` calculates the maximum
total electricity input accepted by the electrolyser system, including
compression and transport energy requirements.

The additional energy requirement is calculated from:

    (sec_compression + sec_transport) / avg_sec_electrolyser

The resulting capacity is returned in kW.

Hourly evaluation
-----------------

The main calculation is performed using:

    results = electrolyser.evaluate(power_df)

``power_df`` must be a pandas DataFrame containing hourly electricity
availability in kW.

Each column represents a separate electricity stream.

For example:

    power_df = pd.DataFrame({
        "Wind": wind_power,
        "Solar": solar_power,
        "Grid": grid_power
    })

The model:

1. Sums the available electricity from all streams.
2. Applies the maximum electrolyser input capacity.
3. Determines electricity used and curtailed electricity.
4. Calculates electrolyser load.
5. Calculates load-dependent electrolyser efficiency.
6. Calculates hourly electrolyser SEC.
7. Calculates hydrogen production.
8. Calculates compression/liquefaction energy.
9. Calculates transport energy.
10. Calculates water consumption.
11. Allocates electricity use between individual streams.
12. Calculates CAPEX and OPEX.
13. Returns hourly, stream-level, and total results.

Efficiency
----------

Electrolyser efficiency is calculated as a function of:

- Electrolyser load
- Electrolyser size
- Installation year
- Annual efficiency improvement

The ``electrolyser_efficiency()`` method is vectorised and accepts
load values as percentages.

The returned efficiency is expressed as a fraction.

Specific energy consumption
----------------------------

Hourly electrolyser SEC is calculated from hydrogen LHV and efficiency:

    SEC = LHV_H2 / efficiency

The resulting SEC is expressed in kWh/kg H2.

Hydrogen production
-------------------

Hydrogen production is calculated from electricity consumption and the
total specific energy requirement:

    total_SEC =
        electrolyser_SEC
        + compression_SEC
        + transport_SEC

Hydrogen production is returned in kg/h.

Stream allocation
-----------------

When multiple electricity streams are supplied, the model allocates
electricity according to the order of the columns in ``power_df``.

For each stream, the model calculates:

- Power used
- Power curtailed
- Energy used
- Hydrogen produced
- Total energy used
- Total energy curtailed
- Total hydrogen produced

The stream-level results are available under:

    results["streams"]

Hourly results
--------------

The hourly results are available under:

    results["hourly"]

The following outputs are provided:

``total_power_kW``
    Total available electricity from all streams in kW.

``power_used_kW``
    Electricity used by the electrolyser system in kW.

``power_curtailed_kW``
    Electricity that cannot be used in kW.

``energy_used_kWh``
    Hourly electricity consumption in kWh.

``H2_kg``
    Hourly hydrogen production in kg.

``compression_energy_kWh``
    Hourly compression/liquefaction energy consumption in kWh.

``transport_energy_kWh``
    Hourly hydrogen transport energy consumption in kWh.

``water_m3``
    Hourly water consumption in m3.

``efficiency``
    Hourly electrolyser efficiency as a fraction.

``sec_electrolyser``
    Hourly electrolyser specific energy consumption in kWh/kg H2.

``load``
    Hourly electrolyser load as a fraction of nominal electrolyser
    capacity.

Stream results
--------------

The stream-level results are available under:

    results["streams"]

For each electricity stream, the following outputs are provided:

``power_used_kW``
    Hourly electricity used from the stream.

``power_curtailed_kW``
    Hourly electricity curtailed from the stream.

``energy_used_kWh``
    Hourly energy used from the stream.

``H2_kg``
    Hourly hydrogen production attributed to the stream.

``totals``
    Dictionary containing total energy used, total energy curtailed,
    and total hydrogen production for the stream.

Total results
-------------

The total results are available under:

    results["totals"]

They include:

``energy_electrolysis_kWh``
    Total electricity used for the electrolyser.

``H2_kg``
    Total hydrogen produced in kg.

``energy_curtailed_kWh``
    Total electricity curtailed.

``compression_energy_kWh``
    Total compression/liquefaction energy consumption.

``transport_energy_kWh``
    Total transport energy consumption.

``water_m3``
    Total water consumption.

``capacity_factor``
    Electrolyser-system capacity factor.

``capex``
    Total electrolyser CAPEX.

``opex``
    Total electrolyser OPEX.

``outlet_pressure``
    Configured electrolyser outlet pressure.

``electrolyser_spec_capex``
    Electrolyser-specific CAPEX in €/kW.

Object attributes
-----------------

After ``evaluate()`` has been executed, the main results are also
available as object attributes.

Examples include:

    electrolyser.total_h2_kg
    electrolyser.capacity_factor
    electrolyser.capex
    electrolyser.opex
    electrolyser.hourly_H2_kg
    electrolyser.hourly_power_used_kW
    electrolyser.hourly_power_curtailed_kW
    electrolyser.hourly_efficiency
    electrolyser.hourly_sec_electrolyser
    electrolyser.streams_H2_kg

Units
-----

- Electrolyser capacity: MW
- Electricity power: kW
- Electricity energy: kWh
- Hydrogen production: kg/h
- Hydrogen total production: kg
- Specific energy consumption: kWh/kg H2
- Water consumption: m3/kg H2
- CAPEX: €
- Specific CAPEX: €/kW
- Pressure: bar
- Efficiency: fraction
- Load: fraction
- Capacity factor: fraction
"""