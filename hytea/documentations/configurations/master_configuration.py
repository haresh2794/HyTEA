MASTER_CONFIG_DOC = """
HyTEA Master Configuration
===========================

This is the master configuration template for setting up a HyTEA
hydrogen supply chain model.

The configuration is organised into the following sections:

    General
    Renewable Electricity Sources
    Grid
    Electrolyser
    Hydrogen Demand
    Hydrogen Storage
    Hydrogen Transport
    Water
    Economics

Users can modify the parameters marked as user inputs. Parameters not
specified in the configuration use the default values defined within
the corresponding HyTEA model.

----------------------------------------------------------------------
1. GENERAL
----------------------------------------------------------------------

scenario_name : str
    Name of the scenario being modelled.

use_storage : bool
    Enable or disable hydrogen storage.

    True  = hydrogen storage is included.
    False = hydrogen storage is not included.

integrate_grid : bool
    Enable or disable electricity imports from the grid.

    True  = grid electricity can be imported.
    False = renewable electricity only.

    If not specified, the model default is used.

----------------------------------------------------------------------
2. RENEWABLE ELECTRICITY SOURCES
----------------------------------------------------------------------

The ``rese_sources`` section defines the renewable electricity sources
available to the hydrogen production system.

Each renewable source is defined separately and can be configured as
wind or solar.

Example::

    "rese_sources": {

        "wind_1": {
            "rese_type": "wind",
            "capacity_mw": 100,
            "csv_file": "wind_1_cf.csv",
            "include_in_boundary": True
        },

        "solar_1": {
            "rese_type": "solar",
            "capacity_mw": 100,
            "csv_file": "solar_1_cf.csv",
            "include_in_boundary": True
        },

        "solar_2": {
            "rese_type": "solar",
            "capacity_mw": 150,
            "csv_file": "solar_2_cf.csv",
            "include_in_boundary": True
        }
    }

rese_type : str
    Renewable electricity technology.

    Options:
        "wind"
        "solar"

capacity_mw : float
    Installed renewable electricity capacity in MW.

csv_file : str
    Path to the hourly renewable electricity capacity factor profile.

include_in_boundary : bool
    Determines whether the renewable electricity generator is included
    within the techno-economic assessment boundary.

    True  = renewable generation is included in the TEA boundary.
    False = renewable electricity is treated as an external input.

price_eur_per_mwh : float, optional
    Electricity purchase price in €/MWh when the renewable source is
    outside the TEA boundary.

capex_per_mw : float, optional
    User-defined renewable electricity CAPEX in €/MW.

opex_per_mw : float, optional
    User-defined renewable electricity OPEX in €/MW.

priority_electricity_export : bool, optional
    Determines whether electricity export priority or an export cap
    is applied.

electricity_export_cap_mw : float, optional
    Maximum electricity export capacity in MW when
    ``priority_electricity_export=True``.

----------------------------------------------------------------------
3. GRID
----------------------------------------------------------------------

The ``grid`` section controls grid electricity integration.

max_grid_price : float, optional
    Maximum electricity price accepted from the grid in €/MWh.

max_grid_ghg : float, optional
    Maximum grid electricity GHG intensity accepted by the model.

use_grid_during_peak_hours : bool
    Determines whether grid electricity use is restricted during
    peak hours.

    True  = apply peak-hour restriction.
    False = ignore peak-hour restriction.

peak_hours : tuple
    Hours during which the peak-hour restriction applies.

avg_grid_price : float
    Default average grid electricity price in €/MWh.

use_fixed_rate : bool, optional
    Determines whether a fixed electricity rate is used.

----------------------------------------------------------------------
4. ELECTROLYSER
----------------------------------------------------------------------

The ``electrolyser`` section defines the electrolyser configuration.

type : str
    Electrolyser technology.

    "ALK" = Alkaline electrolyser.
    "PEM" = Proton Exchange Membrane electrolyser.

    PEM is currently under development and has not yet been validated
    in the HyTEA model.

electro_capacity : float
    Electrolyser capacity in MW.

avg_sec_electrolyser : float, optional
    Specific electricity consumption of the electrolyser.

water_consumption : float, optional
    Specific water consumption.

annual_improvement : float, optional
    Annual electrolyser efficiency improvement factor.

install_year : int, optional
    Year in which the electrolyser is installed.

LHV : float, optional
    Lower heating value of hydrogen in kWh/kg.

spec_capex : float, optional
    User-defined specific electrolyser CAPEX.

opex_per : float, optional
    User-defined electrolyser operating cost.

outlet_pressure : float, optional
    Electrolyser hydrogen outlet pressure in bar.

----------------------------------------------------------------------
5. HYDROGEN DEMAND
----------------------------------------------------------------------

hourly_demand_kgph : array-like
    Hourly hydrogen demand profile in kg/h.

The demand profile should contain 8760 hourly values for a standard
annual simulation.

The demand profile can be generated using the HyTEA demand profile
function or supplied by the user.

----------------------------------------------------------------------
6. HYDROGEN STORAGE
----------------------------------------------------------------------

The ``storage`` section defines the hydrogen storage system.

storage_method : str
    Hydrogen storage technology.

    "Compressed Tanks" = compressed hydrogen tanks.
    "Salt cavern"      = salt cavern storage.
    "Lined rock cavern" = lined rock cavern storage.
    "Liquid H2"        = liquid hydrogen storage.

storage_sizing_option : str, optional
    Storage sizing method.

    "Full storage" = model determines the required storage capacity.
    "Tonnes"       = user specifies storage capacity in tonnes.

storage_hours : float, optional
    Storage duration in hours.

    Currently under development and not yet validated.

storage_capacity_tonnes : float, optional
    Storage capacity in tonnes when using the ``Tonnes`` sizing option.

fos : float, optional
    Factor of safety used in storage sizing.

p_in_bar : float, optional
    Storage inlet pressure in bar.

pout_bar : float, optional
    Storage outlet pressure in bar.

energy_cost : float
    Energy cost associated with storage in €/kWh.

sec_compressor : float, optional
    User-defined compressor specific energy consumption.

max_charge_rate_kgph : float, optional
    Maximum storage charging rate in kg/h.

max_discharge_rate_kgph : float, optional
    Maximum storage discharge rate in kg/h.

custom_specific_capex : float, optional
    User-defined storage specific CAPEX in €/kg.

boil_off_fraction_per_year : float, optional
    Annual hydrogen boil-off fraction.

starting_storage_option : str, optional
    Initial storage condition.

    "empty"  = storage starts empty.
    "hours"  = storage starts with a specified number of hours of demand.

starting_storage_hours : float, optional
    Initial storage expressed as hours of hydrogen demand.

The demand profile is automatically supplied to the storage model.

----------------------------------------------------------------------
7. HYDROGEN TRANSPORT
----------------------------------------------------------------------

The ``transport`` section defines hydrogen transportation parameters.

truck_type : str
    Truck technology.

    "Diesel"   = diesel truck.
    "FCEV_now" = fuel-cell electric vehicle using current technology.
    "FCEV_2030" = fuel-cell electric vehicle based on 2030 assumptions.

transport_method : str
    Hydrogen transportation method.

    "Compressed" = compressed hydrogen.
    "Liquid"     = liquid hydrogen.

distance_km : float
    One-way transport distance in kilometres.

truck_speed_kmh : float
    Average truck speed in km/h.

P0_bar : float, optional
    Hydrogen pressure at the electrolyser outlet.

P1_bar : float, optional
    Hydrogen storage pressure.

P2_bar : float, optional
    Hydrogen transport pressure.

These pressure values are normally derived automatically by HyTEA.

The following parameters can also be provided as user-defined inputs:

tractor_capex
spec_fuel_kWh_per_km
fuel_price_per_kWh
fuel_ghg_gCO2_per_kWh
drivers_per_truck
other_employees_per_truck
employee_salary

If these parameters are not provided, the corresponding model defaults
or calculated values are used.

----------------------------------------------------------------------
8. WATER
----------------------------------------------------------------------

The ``water`` section defines water-related economic parameters.

water_cost_eur_per_m3 : float, optional
    Cost of water in €/m³.

If not specified, the default value defined by the HyTEA model is used.

----------------------------------------------------------------------
9. ECONOMICS
----------------------------------------------------------------------

The ``economics`` section defines the main techno-economic assumptions.

discount_rate : float, optional
    Project discount rate.

construction_years : int, optional
    Construction period in years.

project_life_years : int, optional
    Project operating lifetime in years.

decommissioning_fraction : float, optional
    Decommissioning cost expressed as a fraction of the relevant
    capital expenditure.

energy_management_factor : float, optional
    Energy management cost factor.

interconnection_factor : float, optional
    Electrical interconnection cost factor.

engineering_factor : float, optional
    Engineering cost factor.

If these parameters are not specified, HyTEA uses the model defaults.

----------------------------------------------------------------------
EXAMPLE
----------------------------------------------------------------------

A basic HyTEA configuration can be created as follows::

    config = {

        "scenario_name": "Masterclass Scenario",

        "use_storage": True,

        "rese_sources": {

            "wind": {
                "rese_type": "wind",
                "capacity_mw": 100,
                "csv_file": "wind_cf.csv",
                "include_in_boundary": True,
            },
        },

        "grid": {
            "use_grid_during_peak_hours": True,
            "peak_hours": (17, 18),
            "avg_grid_price": 50,
        },

        "electrolyser": {
            "type": "ALK",
            "electro_capacity": 4,
        },

        "hourly_demand_kgph": hourly_demand_kgph,

        "storage": {
            "storage_method": "Compressed Tanks",
            "energy_cost": 0.25,
        },

        "transport": {
            "truck_type": "Diesel",
            "transport_method": "Compressed",
            "distance_km": 100,
            "truck_speed_kmh": 60,
        },

        "water": {},

        "economics": {},
    }

----------------------------------------------------------------------
CONFIGURATION PRINCIPLE
----------------------------------------------------------------------

Users only need to specify parameters that they want to change.

Parameters omitted from the configuration are automatically assigned
the default values defined by the corresponding HyTEA model.

For a complete list of available parameters and their descriptions,
use this configuration documentation.
"""