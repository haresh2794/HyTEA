DEMAND_PROFILE_DOC = """
Load an hourly hydrogen demand profile for use in HyTEA.

The function can either generate a constant hydrogen demand profile or
load a user-provided hourly demand profile from a CSV file. The resulting
profile contains 8760 hourly values representing one standard year and
is returned as a NumPy array in kg/h.

Demand profile options
----------------------
The demand profile can be generated in two ways:

1. Constant demand

   Set ``use_demand_file=False`` and specify the required hourly demand
   using ``constant_demand``.

   Example::

       demand = load_demand_profile(
           use_demand_file=False,
           constant_demand=50
       )

   This generates an 8760-hour profile with a constant demand of
   50 kg/h.

2. User-provided CSV profile

   Set ``use_demand_file`` to the path of a CSV file containing the
   hourly hydrogen demand.

   The CSV file must contain a column named ``demand`` by default.

   Example::

       demand = load_demand_profile(
           use_demand_file="data/demand.csv",
           demand_column="demand"
       )

   A different column name can be specified using ``demand_column``.

   Example CSV format::

       demand
       50
       50
       55
       60
       ...

   The demand values must be provided in kg/h.

Parameters
----------
use_demand_file : bool or str, optional
    Determines whether to use a user-provided demand profile.

    If ``False``, a constant demand profile is generated using
    ``constant_demand``.

    If a string containing a file path is provided, the function loads
    the demand profile from that CSV file.

    Default is ``False``.

constant_demand : float, optional
    Constant hourly hydrogen demand in kg/h. This value is used only
    when ``use_demand_file=False``.

    Default is ``50``.

demand_column : str, optional
    Name of the column containing hourly hydrogen demand in the input
    CSV file.

    Default is ``"demand"``.

plot_demand : bool, optional
    If ``True``, display a plot of the hourly hydrogen demand profile.

    Default is ``False``.

save_plot : bool, optional
    If ``True``, save the hydrogen demand profile plot to ``plot_file``.

    Default is ``False``.

plot_file : str, optional
    Path where the demand profile plot will be saved when
    ``save_plot=True``.

    Default is ``"plots/demand_profile.png"``.

Returns
-------
np.ndarray
    An array containing 8760 hourly hydrogen demand values in kg/h.

Raises
------
FileNotFoundError
    If the specified demand CSV file does not exist.

ValueError
    If the specified demand column is not present in the CSV file.

ValueError
    If the demand profile does not contain exactly 8760 hours after
    leap-year handling.

Notes
-----
The function expects a standard annual profile containing 8760 hours.

If an 8784-hour leap-year profile is provided, the first 8760 hours
are retained and the final 24 hours are removed.

The demand profile is returned as a NumPy array and can be directly
used as an hourly hydrogen demand input for subsequent HyTEA modelling.

The unit of demand is kg/h.

Examples
--------
Generate a constant hydrogen demand profile::

    demand = load_demand_profile(
        constant_demand=100
    )

Load a demand profile from a CSV file::

    demand = load_demand_profile(
        use_demand_file="data/hydrogen_demand.csv"
    )

Use a custom CSV column name::

    demand = load_demand_profile(
        use_demand_file="data/hydrogen_demand.csv",
        demand_column="H2_demand"
    )

Generate and save a plot::

    demand = load_demand_profile(
        constant_demand=100,
        save_plot=True,
        plot_file="plots/hydrogen_demand.png"
    )
"""