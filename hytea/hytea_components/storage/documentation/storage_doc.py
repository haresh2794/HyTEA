HYDROGEN_STORAGE_DOC = """
HydrogenStorage
===============

Hydrogen storage model for the HyTEA library.

The HydrogenStorage class models the hourly operation, sizing, CAPEX,
OPEX, compression requirements, hydrogen inventory, hydrogen supply,
demand shortfall, and boil-off losses associated with hydrogen storage.

The model supports:

- Compressed Tanks
- Salt cavern
- Lined rock cavern
- Liquid H2

Typical workflow
----------------

1. Create the storage model:

    storage = HydrogenStorage()

2. Configure the storage system:

    storage.configure(config={
        "storage_method": "Compressed Tanks",
        "pout_bar": 300,
        "energy_cost": 0.10,
        "storage_sizing_option": "Full storage"
    })

3. Provide hourly hydrogen demand and production through the
   configuration dictionary.

4. Run the hourly storage analysis:

    results = storage.hourly_analysis()

The returned dictionary contains scalar results, hourly hydrogen flows,
storage inventories, losses, CAPEX/OPEX results, and cumulative
production, demand, and supply.

Storage methods
---------------

The supported storage methods are:

- ``Compressed Tanks``
- ``Salt cavern``
- ``Lined rock cavern``
- ``Liquid H2``

Each storage method has default pressure, temperature, CAPEX parameters,
and an indication of whether compression/liquefaction costs are included
in the storage CAPEX relationship.

Configuration
-------------

The ``configure()`` method accepts either a Python dictionary or a YAML
configuration file.

Example:

    storage.configure(config={
        "storage_method": "Compressed Tanks",
        "storage_sizing_option": "Tonnes",
        "storage_capacity_tonnes": 2,
        "energy_cost": 0.25,
        "pout_bar": 300,
        "hourly_demand_kgph": demand,
        "hourly_production_kgph": production
    })

Main configuration parameters
-----------------------------

``storage_method``
    Storage technology. Supported options are ``Compressed Tanks``,
    ``Salt cavern``, ``Lined rock cavern``, and ``Liquid H2``.

``storage_sizing_option``
    Determines how physical storage capacity is selected.

    Supported options:

    - ``Full storage``: automatically sizes storage according to the
      calculated required capacity.
    - ``Hours``: sizes storage according to a specified number of hours
      of demand.
    - ``Tonnes``: uses a user-defined storage capacity in tonnes.

``storage_hours``
    Number of hours of demand used when
    ``storage_sizing_option="Hours"``.

``storage_capacity_tonnes``
    User-defined storage capacity in tonnes when
    ``storage_sizing_option="Tonnes"``.

``fos``
    Factor of safety applied when determining the required initial
    storage and required storage capacity.

``p_in_bar``
    Hydrogen inlet pressure in barg.

``pout_bar``
    Hydrogen outlet/storage pressure in bar.

``energy_cost``
    Electricity cost in €/kWh used for compression or liquefaction
    operating costs.

``custom_specific_capex``
    Optional user-defined storage-specific CAPEX in €/kg.

``max_charge_rate_kgph``
    Maximum hydrogen charging rate in kg/h. Defaults to infinity.

``max_discharge_rate_kgph``
    Maximum hydrogen discharge rate in kg/h. Defaults to infinity.

``boil_off_fraction_per_year``
    Annual boil-off fraction. By default this is 1%/year for Liquid H2
    and 0%/year for the other storage technologies.

``hourly_demand_kgph``
    Hourly hydrogen demand in kg/h.

``hourly_production_kgph``
    Hourly hydrogen production in kg/h.

The demand and production arrays must have the same length.

Starting storage
----------------

``starting_h2_storage_t``
    Initial physical hydrogen inventory in tonnes.

If this is not specified, the model starts with the full selected storage
capacity.

The starting inventory cannot exceed the physical storage capacity.

Electrolyser parameters
-----------------------

``electro_capacity``
    Electrolyser capacity in MW used for default Liquid H2 sizing.

``avg_sec_electrolyser``
    Average electrolyser specific energy consumption used for default
    Liquid H2 storage energy calculations.

Liquid hydrogen
---------------

For ``Liquid H2``, the model can determine a default liquefaction
specific energy requirement using the configured electrolyser capacity
and average electrolyser SEC.

A user-defined ``liq_storage_sec`` can also be supplied.

Storage sizing
--------------

The model first calculates the hourly hydrogen additions:

    additions = production - demand

The cumulative additions are then used to determine the required initial
storage:

    required_initial_storage
        = max(0, -min(cumulative additions) × FOS)

The ideal storage curve is calculated as:

    ideal_storage
        = required_initial_storage + cumulative additions

The required storage capacity is the maximum of the required initial
storage and the maximum ideal storage level.

The selected physical storage capacity can then be determined using
``Full storage``, ``Hours``, or ``Tonnes``.

If a user-selected capacity is smaller than the calculated required
capacity, a warning is returned in the results.

Hourly storage operation
------------------------

The model prioritises direct production to hydrogen demand.

For each hour:

1. Production is supplied directly to demand.
2. Production surplus is sent to storage.
3. Remaining demand is supplied from storage.
4. Any remaining demand becomes a demand shortfall.
5. Storage boil-off is calculated.
6. The resulting inventory becomes the starting inventory for the
   following hour.

Important hourly outputs include:

``production_to_demand_tph``
    Hydrogen production supplied directly to demand in tonnes/h.

``production_to_storage_tph``
    Hydrogen production sent into storage in tonnes/h.

``storage_to_demand_tph``
    Hydrogen withdrawn from storage to satisfy demand in tonnes/h.

``supply_tph``
    Total hydrogen supplied to demand in tonnes/h.

``demand_shortfall_tph``
    Unmet hydrogen demand in tonnes/h.

``actual_storage_t``
    Actual physical hydrogen inventory in tonnes after the hourly
    storage operation and boil-off.

``starting_storage_t``
    Storage inventory at the beginning of each hour.

``ideal_storage_t``
    Idealised storage trajectory based on cumulative production and
    demand.

``boil_off_t``
    Hydrogen lost through boil-off during each hour in tonnes.

Compression and liquefaction
----------------------------

The model determines the maximum hourly hydrogen flow passing through
compression/liquefaction.

For non-Liquid-H2 storage, compressor-specific CAPEX is calculated from
the configured inlet pressure, outlet pressure, and maximum compression
flow.

For Liquid H2, a separate liquefaction CAPEX relationship is used.

The compressor CAPEX is based on the maximum hourly compressed hydrogen
flow.

The model also calculates annual compressed hydrogen throughput for
compression/liquefaction OPEX.

CAPEX
-----

The model calculates:

``storage_specific_capex``
    Storage CAPEX per kg.

``total_storage_capex``
    Total storage CAPEX.

``compressor_specific_capex``
    Compressor/liquefaction CAPEX per unit of maximum hourly flow.

``total_compressor_capex``
    Total compressor/liquefaction CAPEX.

For storage technologies where compression/liquefaction is included in
the storage-specific CAPEX relationship, the compressor CAPEX is
subtracted when calculating total storage CAPEX.

OPEX
----

Storage OPEX is calculated as 2% of total storage CAPEX.

Compressor/liquefaction OPEX consists of:

- 2% of compressor/liquefaction CAPEX
- electricity consumption multiplied by the configured electricity cost
  and annual compressed hydrogen throughput

For Liquid H2, the configured or calculated liquid-hydrogen specific
energy requirement is used.

Results
-------

``hourly_analysis()`` returns a dictionary containing:

Scalar results
~~~~~~~~~~~~~~

- ``required_initial_storage_kg``
- ``required_capacity_kg``
- ``storage_specific_capex``
- ``compressor_specific_capex``
- ``total_compressor_capex``
- ``total_compressor_opex``
- ``total_storage_capex``
- ``total_storage_opex``

Hourly inputs
~~~~~~~~~~~~~

- ``hourly_demand_kgph``
- ``hourly_production_kgph``

Hourly flow rates
~~~~~~~~~~~~~~~~~

All rates below are in tonnes/h:

- ``hourly_demand_tph``
- ``hourly_production_tph``
- ``h2_additions_tph``
- ``production_to_storage_tph``
- ``production_to_demand_tph``
- ``demand_shortfall_tph``
- ``storage_to_demand_tph``
- ``supply_tph``
- ``storage_inflows_tph``
- ``storage_outflows_tph``

Hourly inventories
~~~~~~~~~~~~~~~~~~

Inventories are provided in tonnes:

- ``starting_storage_t``
- ``actual_storage_t``
- ``ideal_storage_t``
- ``storage_no_init_t``

Additional kg-based outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``h2_additions_kgph``
- ``storage_no_init_kg``
- ``actual_storage_kg``

Losses
~~~~~~

- ``boil_off_t``
- ``boil_off_kg``

Cumulative outputs
~~~~~~~~~~~~~~~~~~

- ``cumulative_production_t``
- ``cumulative_demand_t``
- ``cumulative_supply_t``

Warning
~~~~~~~

``warning`` contains a warning message if the selected storage capacity
is smaller than the calculated required capacity.

Units summary
-------------

+-------------------------------+----------+
| Quantity                      | Unit     |
+-------------------------------+----------+
| Storage capacity              | kg / t   |
| Hydrogen demand               | kg/h     |
| Hydrogen production           | kg/h     |
| Hydrogen flow rates            | t/h      |
| Hydrogen inventory             | t        |
| Hydrogen losses                | t / kg   |
| Specific storage CAPEX         | €/kg     |
| Total storage CAPEX            | €        |
| Specific compressor CAPEX      | €/kg/h   |
| Total compressor CAPEX         | €        |
| Electricity cost               | €/kWh    |
+-------------------------------+----------+

Notes
-----

The ``HydrogenStorage`` model performs the storage-system calculation
independently. It can be used with hydrogen production and demand
profiles generated by other HyTEA components and orchestrated through
the HyTEA core model.
"""