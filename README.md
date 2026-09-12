# HyTEA

## Hydrogen Techno-Economic Assessment Tool

HyTEA is a techno-economic assessment and decision-support tool for evaluating hydrogen production and supply systems, including renewable electricity, grid electricity, electrolysis, hydrogen storage, transport, economics, and greenhouse gas emissions.

**Developed by the ERIN Research Group**
**University of Galway**

**Lead:**
Prof. Rory Monaghan
Dr. Haresh Jayashankar

---

# Funding

HyTEA has been developed as part of the **HYDEA project**, funded by the **European Union** and **Interreg Atlantic Area**. (https://www.eu-hydea.eu/)

---

# Contact

For questions regarding HyTEA, its documentation, implementation, or use, please contact:

Prof. Rory Monaghan
rory.monaghan@universityofgalway.ie

Dr. Haresh Jayashankar
haresankar.jayasankar@universityofgalway.ie

**ERIN Research Group**
**University of Galway**


# How to Cite HyTEA

If you use HyTEA in a publication, report, presentation, or other academic work, please cite the software as follows:

Monaghan, R., & Jayashankar, H. (2026). HyTEA – Hydrogen Techno-Economic Assessment Tool. University of Galway. HYDEA Project, European Union and Interreg Atlantic Area. https://www.eu-hydea.eu/

---

# Getting Started

The recommended way to start using HyTEA is through the **Scenario Analysis Template** in Google Colab.

If you are using HyTEA for the first time, follow this order:

1. **Scenario Analysis Template**
2. **Master Configuration**
3. **Class and function documentation**
4. **Component-specific documentation**
5. **Optimisation and analysis tools**

The Scenario Analysis Template provides the practical workflow for configuring and running HyTEA scenarios in Google Colab.

---

# 1. Scenario Analysis Template

Start with the **Scenario Analysis Template**.

The template demonstrates the recommended workflow for:

* Importing HyTEA
* Creating a scenario configuration
* Modifying scenario parameters
* Configuring `HyTEACore`
* Running a scenario
* Accessing model results
* Creating multiple scenarios
* Comparing scenarios
* Analysing LCOH and GHG results
* Generating plots
* Exporting scenario results

A typical HyTEA workflow is:

```python
from hytea.hytea_core import HyTEACore

scenario_1 = HyTEACore()

scenario_1.configure(config_1)

results_1 = scenario_1.evaluate()
```

For multiple scenarios:

```python
scenario_1 = HyTEACore()
scenario_1.configure(config_1)
results_1 = scenario_1.evaluate()

scenario_2 = HyTEACore()
scenario_2.configure(config_2)
results_2 = scenario_2.evaluate()
```

**Start with the Scenario Analysis Template before working directly with the individual components.**

---

# 2. Master Configuration

The Master Configuration explains the overall HyTEA configuration structure and the parameters used to define a hydrogen production and supply scenario.

The master configuration documentation is located at:

```text
documentations/master_config.py
```

The configuration template is located at:

```text
documentations/configurations/master_configuration.py
```
Use the master configuration to understand:

* Renewable electricity configurations
* Grid configurations
* Electrolyser configurations
* Storage configurations
* Transport configurations
* Economics configurations
* Hydrogen demand
* Other scenario-level settings

When creating a new scenario, use the master configuration as the starting point and modify only the parameters required for the scenario.

---

# 3. Documentation for Classes and Functions

Documentation for the HyTEA classes and supporting functions is available through Python's `help()` function and the `__doc__` attribute.

In Google Colab:

```python
help(HyTEACore)
```

or:

```python
print(HyTEACore.__doc__)
```

The same approach can be used for individual components:

```python
help(RenewableElectricity)
```

```python
help(ALKElectrolyser)
```

```python
help(HydrogenStorage)
```

```python
help(HydrogenTruckTransport)
```

and for supporting functions:

```python
help(create_scenario_config)
```

```python
help(plot_lcoh_scenarios)
```

```python
help(plot_ghg_intensity_scenarios)
```

This is the recommended way to check the parameters, inputs, outputs, and usage of individual HyTEA classes and functions without needing to inspect the implementation source code.

---

# 4. HyTEA Core

The main system-level model is:

```text
hytea_core/
└── core.py
```

The main class is:

```python
HyTEACore
```

The core coordinates the different HyTEA components and runs the overall hydrogen supply-chain model.

Use:

```python
help(HyTEACore)
```

for the detailed documentation.

The external documentation for the core is located at:

```text
hytea_core/documentation/core_doc.py
```

---

# 5. HyTEA Components

The main HyTEA components are organised under:

```text
hytea_components/
```

## Renewable Electricity

Location:

```text
hytea_components/rese/
```

Main model:

```text
hytea_components/rese/rese_model.py
```

Documentation:

```text
hytea_components/rese/documentation/rese_model_doc.py
```

Main class:

```python
RenewableElectricity
```

---

## Grid Electricity

Location:

```text
hytea_components/grid/
```

Main model:

```text
hytea_components/grid/grid_model.py
```

Main class:

```python
Grid
```

Use:

```python
help(Grid)
```

for the available documentation.

---

## Electrolyser

Location:

```text
hytea_components/electrolyser/
```

Models:

```text
hytea_components/electrolyser/alk.py
hytea_components/electrolyser/pem.py
```

The available electrolyser models include:

```python
ALKElectrolyser
PEMElectrolyser
```

ALK documentation:

```text
hytea_components/electrolyser/documentation/alk_doc.py
```

Use:

```python
help(ALKElectrolyser)
```

or:

```python
help(PEMElectrolyser)
```

---

## Hydrogen Storage

Location:

```text
hytea_components/storage/
```

Models include:

```text
storage.py
salt_cavern.py
liquid_storage.py
```

Main storage class:

```python
HydrogenStorage
```

Documentation:

```text
hytea_components/storage/documentation/storage_doc.py
```

Use:

```python
help(HydrogenStorage)
```

for the detailed documentation.

---

## Hydrogen Transport

Location:

```text
hytea_components/transport/
```

Models include:

```text
truck_transport.py
pipeline_transport.py
```

Truck transport documentation:

```text
hytea_components/transport/documentation/truck_transport_doc.py
```

Use:

```python
help(HydrogenTruckTransport)
```

for the truck transport model documentation.

---

## Economics

Location:

```text
hytea_components/economics/
```

Main modules:

```text
discounting.py
lc.py
```

These modules contain the economic and levelised-cost calculations used by HyTEA.

---

# 6. Supporting Utilities

Supporting functions are located in:

```text
utils/
```

These include utilities for:

* Scenario configuration
* Hydrogen demand profiles
* LCOH plotting
* GHG plotting
* Renewable electricity plotting
* Storage plotting
* Scenario result export
* Wind resource data
* Solar resource data

The documentation for these functions is located in:

```text
utils/documentation/
```

For example:

```text
utils/documentation/create_scenarios_config_doc.py
utils/documentation/demand_profile_doc.py
utils/documentation/plots_lcoh_doc.py
utils/documentation/plots_ghg_doc.py
utils/documentation/plot_resepw_doc.py
utils/documentation/plots_storage_doc.py
utils/documentation/save_scenarios_to_csv_doc.py
utils/documentation/solar_ninja_doc.py
utils/documentation/wind_ninja_doc.py
```

The recommended way to access the documentation in Colab is:

```python
help(function_name)
```

---

# 7. Optimisation

HyTEA includes optimisation tools under:

```text
hytea_optimizers/
```

The current optimisation module is:

```text
hytea_optimizers/op1.py
```

Documentation:

```text
hytea_optimizers/documentation/op1_doc.py
```

Use:

```python
help(op1_min_electrolyser_capacity)
```

to view the documentation and usage of the optimisation function.

---

# 8. HyTEA SDK

The SDK components are located under:

```text
hytea_sdk/
```

Main module:

```text
hytea_sdk/component.py
```

The SDK provides the component-level structure used within HyTEA.

---

# Recommended Workflow

The recommended workflow for a new user is:

```text
Scenario Analysis Template
            ↓
Master Configuration
            ↓
Create / modify scenario configuration
            ↓
Configure HyTEACore
            ↓
Evaluate scenario
            ↓
Access results
            ↓
Analyse LCOH and GHG
            ↓
Compare scenarios
            ↓
Generate plots
            ↓
Export results
```

For detailed information about a particular class or function, use:

```python
help(ClassName)
```

or:

```python
help(function_name)
```

You can also use:

```python
print(ClassName.__doc__)
```

or:

```python
print(function_name.__doc__)
```

---

# Package Structure

The main installed HyTEA structure is:

```text
hytea/
│
├── hytea_components/
│   ├── rese/
│   ├── grid/
│   ├── storage/
│   ├── economics/
│   ├── transport/
│   └── electrolyser/
│
├── hytea_core/
│   ├── core.py
│   └── documentation/
│
├── hytea_optimizers/
│   ├── op1.py
│   └── documentation/
│
├── hytea_sdk/
│   └── component.py
│
├── utils/
│   ├── create_scenarios_config.py
│   ├── demand_profile.py
│   ├── plots_lcoh.py
│   ├── plots_ghg.py
│   ├── plots_resepw.py
│   ├── plots_storage.py
│   ├── save_scenarios_to_csv.py
│   ├── solar_ninja.py
│   ├── wind_ninja.py
│   └── documentation/
│
└── documentations/
    ├── master_config.py
    └── configurations/
        └── master_configuration.py
```

`__pycache__` directories and `.pyc` files are generated Python cache files and are not part of the user-facing documentation or workflow.

---

