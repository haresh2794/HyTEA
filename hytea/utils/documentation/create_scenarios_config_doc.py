CREATE_SCENARIO_CONFIG_DOC = """
Create a scenario configuration from a base HyTEA configuration.

The function creates an independent copy of the supplied base
configuration and applies only the scenario-specific changes.

Nested dictionaries are merged recursively. This means that when a
nested configuration section is changed, only the specified parameters
are updated while all other parameters from the base configuration are
retained.

The original ``base_config`` is not modified.

Parameters
----------
base_config : dict
    Base configuration dictionary from which the scenario configuration
    is created.

    The function creates a deep copy of this dictionary before applying
    any changes.

scenario_name : str, optional
    Name assigned to the scenario.

    If provided, it is stored in the returned configuration as:

        config["scenario_name"] = scenario_name

    If ``None``, no scenario name is added or changed.

**changes : dict
    Scenario-specific configuration changes supplied as keyword
    arguments.

    Changes may be provided at any level of the configuration.

    If both the existing value in ``base_config`` and the supplied value
    are dictionaries, the dictionaries are merged recursively.

    Otherwise, the supplied value replaces the existing value.

Recursive merging
-----------------

Nested dictionaries are updated recursively.

For example, given:

    base_config = {
        "electrolyser": {
            "electro_capacity": 5,
            "technology": "ALK",
            "pressure_bar": 30
        }
    }

and:

    changes = {
        "electrolyser": {
            "electro_capacity": 10
        }
    }

the resulting configuration is:

    {
        "electrolyser": {
            "electro_capacity": 10,
            "technology": "ALK",
            "pressure_bar": 30
        }
    }

Only ``electro_capacity`` is changed. The other electrolyser parameters
are retained from the base configuration.

Replacement behaviour
---------------------

If the supplied value is not a dictionary, or the corresponding value
in the base configuration is not a dictionary, the supplied value
replaces the existing value.

For example:

    changes = {
        "electrolyser": {
            "technology": "PEM"
        }
    }

replaces the existing value of ``technology`` while leaving the other
electrolyser parameters unchanged.

A complete dictionary can also replace a non-dictionary value.

Deep-copy behaviour
-------------------

The function uses ``deepcopy(base_config)`` before applying changes.

Consequently, modifications made to the returned scenario configuration
do not modify the original base configuration through shared nested
dictionary references.

Scenario name
-------------

When ``scenario_name`` is supplied, it is explicitly stored at the
top level of the returned configuration:

    config["scenario_name"] = scenario_name

The scenario name is therefore available to downstream HyTEA model
components that use the configuration.

Returns
-------
dict
    A new scenario configuration containing:

    - all parameters from the base configuration,
    - the supplied scenario name, if provided, and
    - the specified scenario-specific changes.

The returned dictionary is independent of the original ``base_config``.

Typical usage
-------------

Create a scenario with a different electrolyser capacity:

    scenario_config = create_scenario_config(
        base_config,
        scenario_name="10 MW Electrolyser",
        electrolyser={
            "electro_capacity": 10
        }
    )

Create a scenario with changes to multiple components:

    scenario_config = create_scenario_config(
        base_config,
        scenario_name="High Renewable Scenario",
        electrolyser={
            "electro_capacity": 10
        },
        storage={
            "storage_capacity_tonnes": 5
        }
    )

Create a scenario without specifying a name:

    scenario_config = create_scenario_config(
        base_config,
        electrolyser={
            "electro_capacity": 8
        }
    )

Purpose within HyTEA
--------------------

``create_scenario_config`` provides a convenient way to generate
alternative HyTEA model scenarios from a common base configuration.

It avoids the need to manually duplicate the complete configuration
for every scenario and allows scenario analyses to specify only the
parameters that differ from the base case.

This is particularly useful for sensitivity analyses, technology
comparisons, capacity scenarios, storage scenarios, and other
configuration-based modelling studies.
"""