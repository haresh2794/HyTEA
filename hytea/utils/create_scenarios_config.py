from copy import deepcopy

from .documentation.create_scenarios_config_doc import CREATE_SCENARIO_CONFIG_DOC


def create_scenario_config(base_config, scenario_name=None, **changes):
   
    def recursive_update(base, updates):

        for key, value in updates.items():

            if (
                isinstance(value, dict)
                and isinstance(base.get(key), dict)
            ):
                recursive_update(
                    base[key],
                    value
                )

            else:
                base[key] = value

    config = deepcopy(base_config)

    if scenario_name is not None:
        config["scenario_name"] = scenario_name

    recursive_update(config, changes)

    return config


create_scenario_config.__doc__ = CREATE_SCENARIO_CONFIG_DOC