HYTEA_CORE_DOC = """
HyTEACore
=========

Core orchestration model for the HyTEA library.

HyTEACore coordinates the main components of a hydrogen production and
delivery system and passes information between the individual component
models.

The current system boundary includes:

- Renewable electricity (RESE)
- Optional grid electricity
- Electrolyser
- Hydrogen storage
- Hydrogen truck transport
- Economics
- Discounting
- Levelised cost of hydrogen (LCOH)
- GHG intensity
- Hydrogen supply-demand balance

The core model is responsible for configuring, running, validating, and
connecting the individual HyTEA component models.

Typical workflow
----------------

Create the core model:

    scenario = HyTEACore()

Provide the system configuration:

    scenario.configure(config)

Run the complete scenario:

    results = scenario.evaluate()

The ``evaluate()`` method executes the main HyTEA workflow and returns
a dictionary containing the results from the individual components.

Configuration
-------------
==================================================
NOTE: Check master configuration at 
from hytea.documentations import show_master_config
show_master_config()
==================================================

The ``configure()`` method accepts a configuration dictionary.

Example high-level structure:

    config = {
        "scenario_name": "Example Scenario",

        "rese_sources": {
            "wind": {
                ...
            },
            "solar": {
                ...
            }
        },

        "integrate_grid": True,

        "grid": {
            ...
        },

        "electrolyser": {
            ...
        },

        "storage": {
            ...
        },

        "transport": {
            ...
        },

        "economics": {
            ...
        },

        "hourly_demand_kgph": [...]
    }

The exact configuration parameters for each component are handled by
the corresponding component model.

Validation
----------

``validate_config()`` checks the minimum required configuration.

The configuration must contain:

- ``rese_sources``
- ``electrolyser``

``rese_sources`` must be a non-empty dictionary.

If ``integrate_grid=True``, a ``grid`` configuration must also be
provided.

Renewable electricity
---------------------

``run_rese_sources()`` creates and evaluates one
``RenewableElectricity`` model for each configured renewable electricity
source.

Multiple sources can therefore be included, for example:

    "rese_sources": {
        "wind": {...},
        "solar": {...}
    }

Each source is stored separately in:

    self.rese_models

and its evaluated results are stored in:

    self.rese_results

The method returns:

    rese_results

where each key corresponds to a renewable electricity source.

RESE aggregation
----------------

``aggregate_rese_results()`` combines the individual renewable
electricity sources into a single aggregated time series.

The aggregated results include:

- Combined hourly renewable electricity output in MW
- Total RESE CAPEX
- Total RESE OPEX
- Combined cumulative energy in GWh
- Total cumulative energy in GWh

The aggregated results are stored in:

    self.aggregated_results

Grid electricity
---------------

Grid integration is optional.

``run_grid()`` runs the grid model only when:

    integrate_grid = True

Before running the grid model, ``build_hourly_cf_mul()`` creates the
renewable electricity capacity-factor array required by the grid model.

The grid model provides information including:

- Hourly weighted renewable capacity factor
- Hourly electricity price trend
- Hourly grid purchase price
- Hourly grid sales price
- Hourly GHG intensity
- Average weighted capacity factor
- Average purchase price
- Average sales price
- Average GHG intensity

The grid results are stored in:

    self.grid_results

and selected summary values are stored in:

    self.grid_summary

Electrolyser
------------

``setup_electrolyser()`` configures the electrolyser according to the
``type`` specified in the electrolyser configuration.

Supported electrolyser models include:

- ``ALK``: alkaline electrolyser
- ``PEM``: PEM electrolyser

If no type is specified, the default is ALK.

The configured electrolyser model is stored in:

    self.electrolyser_model

RESE power input
----------------

``build_rese_power_df()`` creates the renewable electricity input
DataFrame required by the electrolyser.

The DataFrame:

- Contains one column per RESE source
- Uses hourly electricity values
- Is expressed in kW

The underlying RESE model produces hourly output in MW. The core model
converts this to kW for electrolyser input.

Electricity export priority
---------------------------

A renewable electricity source can optionally have electricity export
priority.

Relevant configuration parameters include:

``priority_electricity_export``
    Determines whether part of the renewable electricity output is
    reserved for export.

``electricity_export_cap_mw``
    Maximum export power in MW.

The exported electricity is stored separately in:

    self.rese_export_streams

The remaining renewable electricity is supplied to the electrolyser.

Grid residual power
-------------------

``build_grid_stream()`` calculates the residual grid electricity
required to reach the electrolyser's actual input capacity.

The grid is only used when:

    integrate_grid = True

The required residual electricity is subject to user-defined limits
including:

- Maximum grid electricity price
- Maximum grid GHG intensity
- Optional peak-hour blocking

The grid stream is stored in:

    self.grid_stream_kW

The resulting grid electricity is expressed in kW.

Complete electrolyser power input
----------------------------------

``build_power_df_for_electrolyser()`` combines:

- Renewable electricity streams
- Optional grid electricity

into a single DataFrame.

The resulting DataFrame is stored in:

    self.power_df

and is passed to the electrolyser model.

Running the electrolyser
------------------------

``run_electrolyser()``:

1. Configures the electrolyser if necessary.
2. Builds the complete power input DataFrame.
3. Runs the configured electrolyser model.
4. Stores the resulting outputs.

The results are stored in:

    self.electrolyser_results

Hydrogen storage
----------------

``build_storage_config()`` creates the storage configuration using:

- User-provided storage configuration
- Hydrogen demand from the system configuration
- Hydrogen production from the electrolyser
- Electrolyser capacity
- Average electrolyser SEC

The resulting configuration is passed to ``HydrogenStorage``.

``run_storage()`` runs the hydrogen storage model.

Storage results are stored in:

    self.storage_results

Storage can be disabled using:

    "use_storage": False

When storage is disabled, the electrolyser hydrogen production is used
directly as the downstream hydrogen supply.

Hydrogen supply
---------------

``build_h2_supply()`` creates the common hourly hydrogen supply stream
used by downstream components.

If storage is enabled:

    H2 supply = storage supply

If storage is disabled:

    H2 supply = electrolyser H2 production

The common supply stream is stored in:

    self.h2_supply_kgph

The unit is kg/h.

No-storage demand check
-----------------------

When storage is disabled, ``check_h2_demand_when_no_storage()`` compares
hourly hydrogen production with hourly hydrogen demand.

It calculates:

- Hourly hydrogen deficit
- Hourly hydrogen surplus
- Total annual hydrogen deficit
- Whether annual hydrogen demand is fulfilled

The results are stored in:

    self.no_storage_h2_deficit_kgph
    self.no_storage_h2_surplus_kgph
    self.no_storage_total_h2_deficit_kg
    self.no_storage_demand_fulfilled

Transport
---------

``build_transport_config()`` creates the transport configuration using
upstream system information.

The core model can automatically determine:

- Electrolyser outlet pressure
- Storage pressure
- Average hydrogen supply
- Maximum hydrogen supply

``run_transport()`` configures and evaluates the
``HydrogenTruckTransport`` model.

Transport results are stored in:

    self.transport_results

Economics
---------

The economic calculation is performed through:

    run_economics()

The economic workflow includes:

1. Building the CAPEX/OPEX breakdown.
2. Determining the annual hydrogen denominator.
3. Discounting CAPEX.
4. Discounting OPEX.
5. Discounting hydrogen production/delivery.
6. Calculating total LCOH.
7. Calculating CAPEX and OPEX contributions to LCOH.
8. Calculating component-level LCOH contributions.

Cost breakdown
--------------

``build_cost_breakdown()`` calculates CAPEX and OPEX contributions from:

- RESE
- Electrolyser
- Grid electricity
- Compressor/liquefier
- Energy management
- Interconnection
- Engineering
- Other costs
- Storage
- Transport
- Water

The resulting breakdown is stored in:

    self.economics_results

The model supports two LCOH denominator options:

``produced``
    Uses hydrogen produced by the electrolyser.

``delivered``
    Uses hydrogen delivered to the downstream system.

The option is controlled through:

    economics["h2_lcoh_basis"]

Discounting
-----------

The core model uses ``DiscountingModel`` to calculate present values.

``_discount_single_cost_item()`` discounts a single CAPEX or OPEX item.

``_discount_hydrogen()`` discounts the annual hydrogen denominator.

The discounted results are stored in:

    self.discounting_results

Levelised cost
--------------

The levelised cost results are stored in:

    self.levelized_cost_results

The main LCOH outputs include:

``total_lcoh``
    Total levelised cost of hydrogen.

``capex_lcoh``
    CAPEX contribution to LCOH.

``opex_lcoh``
    OPEX contribution to LCOH.

``capex_lcoh_breakdown``
    Individual CAPEX contributions.

``opex_lcoh_breakdown``
    Individual OPEX contributions.

``component_lcoh``
    Combined CAPEX and OPEX LCOH contribution for each component.

GHG intensity
-------------

``calculate_ghg_intensity()`` calculates system-level hydrogen GHG
intensity.

The calculation includes:

- Grid electricity emissions
- Hydrogen transport emissions

The main outputs are:

``total_ghg_t_per_year``
    Total annual system GHG emissions in tonnes CO2/year.

``grid_ghg_t_per_year``
    Annual grid-related GHG emissions.

``transport_ghg_t_per_year``
    Annual transport-related GHG emissions.

``ghg_t_per_tH2``
    GHG intensity in tonnes CO2 per tonne H2.

``ghg_g_per_kWh``
    GHG intensity expressed in gCO2/kWh of hydrogen energy.

Hydrogen balance
----------------

``check_annual_h2_balance()`` checks whether annual hydrogen supply is
sufficient to meet annual hydrogen demand.

The calculation compares:

- Annual hydrogen demand
- Annual electrolyser hydrogen production
- Annual hydrogen supply available to downstream components

The method returns:

- Annual production
- Annual supply
- Annual demand
- Surplus or deficit
- Sufficiency flag
- Descriptive message

Complete scenario evaluation
----------------------------

The complete system is evaluated using:

    results = scenario.evaluate()

The workflow is:

1. Validate configuration.
2. Run RESE sources.
3. Aggregate RESE results.
4. Run the grid model if enabled.
5. Configure the electrolyser.
6. Run the electrolyser.
7. Validate the electrolyser energy balance.
8. Run storage if enabled.
9. Build the common hydrogen supply stream.
10. Run transport.
11. Run economics.
12. Calculate GHG intensity.
13. Check the annual hydrogen balance.
14. Return all major results.

Returned results
----------------

``evaluate()`` returns a dictionary containing:

``scenario_name``
    Scenario name.

``rese_results``
    Individual renewable electricity source results.

``aggregated_results``
    Aggregated renewable electricity results.

``grid_results``
    Detailed grid model results.

``grid_summary``
    Selected grid summary metrics.

``ghg_results``
    System GHG intensity results.

``power_df``
    Final stream-wise electricity DataFrame supplied to the
    electrolyser.

``grid_stream_kW``
    Hourly grid electricity stream in kW.

``electrolyser_results``
    Electrolyser results.

``storage_results``
    Hydrogen storage results.

``transport_results``
    Hydrogen transport results.

``economics_results``
    CAPEX/OPEX breakdown.

``discounting_results``
    Present-value calculations.

``levelized_cost_results``
    LCOH results.

``annual_balance_results``
    Annual hydrogen supply-demand balance.

``no_storage_demand_fulfilled``
    Indicates whether demand is fulfilled when storage is disabled.

``no_storage_total_h2_deficit_kg``
    Total annual hydrogen deficit when storage is disabled.

``no_storage_h2_deficit_kgph``
    Hourly hydrogen deficit when storage is disabled.

``no_storage_h2_surplus_kgph``
    Hourly hydrogen surplus when storage is disabled.

Main object attributes
----------------------

The core model stores the main component models and results as object
attributes.

Examples include:

    scenario.rese_models
    scenario.rese_results
    scenario.aggregated_results
    scenario.grid_model
    scenario.grid_results
    scenario.electrolyser_model
    scenario.electrolyser_results
    scenario.storage_model
    scenario.storage_results
    scenario.transport_model
    scenario.transport_results
    scenario.power_df
    scenario.economics_results
    scenario.discounting_results
    scenario.levelized_cost_results

Component relationships
-----------------------

The main information flow through the core model is:

    RESE
      ↓
    Grid assessment
      ↓
    Electrolyser power input
      ↓
    Hydrogen production
      ↓
    Storage
      ↓
    Hydrogen supply
      ↓
    Transport
      ↓
    Economics / LCOH / GHG

Grid electricity is optional.

Storage is optional.

The core model acts primarily as an orchestration layer. Detailed
component calculations remain within the individual HyTEA component
classes.
"""