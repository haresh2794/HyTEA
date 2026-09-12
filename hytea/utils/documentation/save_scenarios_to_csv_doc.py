SAVE_SCENARIO_RESULTS_TO_CSV_DOC = """
Save results from multiple evaluated HyTEA scenarios to a CSV file.

This function extracts selected configuration parameters and model
results from a list of ``HyTEACore`` scenario objects and combines them
into a single pandas DataFrame. The resulting DataFrame is saved as a
CSV file and also returned by the function.

Each scenario must already be configured with ``configure()``. The
function calls ``evaluate()`` for each scenario to obtain the latest
model results before extracting the required values.

The exported results include:

    - Scenario name
    - Renewable electricity (RESE) capacity and electricity price
    - Hydrogen LCOH basis
    - Grid integration and grid GHG factor
    - Hydrogen storage sizing option and capacity
    - Annual hydrogen produced and delivered
    - Total LCOH
    - CAPEX and OPEX contributions to LCOH
    - GHG intensity
    - Total, grid, and transport GHG emissions
    - LCOH component breakdown
    - LCOH CAPEX breakdown
    - LCOH OPEX breakdown

Parameters
----------
scenarios : list
    List of configured ``HyTEACore`` objects.

    Each scenario should have been configured using ``configure()``.
    The function evaluates each scenario before extracting its results.

    Example
    -------
    scenario_1 = HyTEACore()
    scenario_1.configure(config_1)

    scenario_2 = HyTEACore()
    scenario_2.configure(config_2)

    scenarios = [scenario_1, scenario_2]

output_file : str, optional
    Path and filename of the output CSV file.

    If a directory is included in the path and it does not already
    exist, the directory is created automatically.

    Default is ``"scenario_results.csv"``.

Returns
-------
pd.DataFrame
    DataFrame containing one row for each scenario and columns
    corresponding to the extracted configuration and model results.

Notes
-----
The function obtains the scenario configuration directly from the
``config`` attribute of each ``HyTEACore`` object.

The scenario results are obtained by calling:

    ``scenario.evaluate()``

Therefore, each scenario is evaluated again when this function is
called, even if it has already been evaluated previously.

For renewable electricity sources, the function exports only:

    - Installed capacity in MW
    - Electricity price in EUR/MWh

For storage, the reported full storage capacity depends on the storage
sizing method. When ``storage_sizing_option`` is ``"Tonnes"``, the
user-specified storage capacity is retained and the calculated full
storage capacity is not reported. For other sizing options, the full
storage capacity calculated by the model is reported in tonnes.

The function dynamically adds columns for the LCOH component,
CAPEX, and OPEX breakdowns based on the keys available in the
corresponding model results.

The CSV file is written without the pandas DataFrame index.

Examples
--------
Create two configured scenarios and save their results:

    scenario_1 = HyTEACore()
    scenario_1.configure(config_1)

    scenario_2 = HyTEACore()
    scenario_2.configure(config_2)

    scenarios = [scenario_1, scenario_2]

    df = save_scenario_results_to_csv(
        scenarios,
        output_file="results/scenario_results.csv"
    )

The returned DataFrame can then be inspected or used for further
analysis:

    print(df)

    print(df["LCOH (€/kg H2)"])

    print(df["Total GHG (tCO2/year)"])

    print(df["GHG intensity (tCO2/tH2)"])
"""