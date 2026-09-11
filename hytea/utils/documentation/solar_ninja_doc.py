SOLAR_CF_DOC = """
Generate hourly solar PV capacity factor data for a specified location
using the Renewables.ninja PV API.

The function retrieves hourly solar PV generation data based on the
specified location, date range, PV system configuration, and installed
capacity. The resulting hourly capacity factor profile is saved as a
CSV file with the columns ``hour`` and ``cf``.

Renewables.ninja API access
---------------------------
A Renewables.ninja API token is required.

To obtain an API token:

1. Create an account at https://www.renewables.ninja/
2. Log in to your account.
3. Go to your account/profile page.
4. Copy your API token.
5. Pass the token to this function using the ``token`` argument.


Example
-------

from hytea.utils import generate_solar_cf_from_location

generate_solar_cf_from_location(
            lat=53.27,
            lon=-9.05,
            token="YOUR_RENEWABLES_NINJA_TOKEN",
            plot_cf=True,
            save_plot=True,
            plot_file=f"plots/solar_cf.png"
         )


Parameters
----------
lat : float
    Latitude of the PV system location in decimal degrees.

lon : float
    Longitude of the PV system location in decimal degrees.

output_file : str, optional
    Path to the CSV file where the hourly solar PV capacity factor data
    will be saved. Default is ``"data/solar.csv"``.

token : str, optional
    Renewables.ninja API token. A valid token is required to access the
    API.

date_from : str, optional
    Start date for the simulation in ``YYYY-MM-DD`` format.
    Default is ``"2020-01-01"``.

date_to : str, optional
    End date for the simulation in ``YYYY-MM-DD`` format.
    Default is ``"2020-12-31"``.

system_loss : float, optional
    Fraction of the PV system output lost due to system losses.
    For example, ``0.1`` represents a 10% system loss.
    Default is ``0.1``.

tracking : int, optional
    PV tracking configuration used by Renewables.ninja.
    ``0`` represents a fixed-tilt system. Other values correspond to
    the tracking options supported by the Renewables.ninja PV model.
    Default is ``0``.

tilt : float, optional
    Tilt angle of the PV panels in degrees.
    Default is ``35``.

azim : float, optional
    Azimuth angle of the PV panels in degrees. The value follows the
    Renewables.ninja convention. Default is ``180``.

capacity : float, optional
    Installed PV capacity in MW. Default is ``1.0``.

verbose : bool, optional
    If ``True``, print progress messages and the locations of generated
    output files. Default is ``False``.

plot_cf : bool, optional
    If ``True``, display a plot of the hourly solar PV capacity factor.
    Default is ``False``.

save_plot : bool, optional
    If ``True``, save the capacity factor plot to ``plot_file``.
    Default is ``False``.

plot_file : str, optional
    Path where the capacity factor plot will be saved when
    ``save_plot=True``. Default is
    ``"plots/solar_cf_plot.png"``.

Returns
-------
str
    Path to the generated CSV file.

Raises
------
ValueError
    If a Renewables.ninja API token is not provided.

RuntimeError
    If the Renewables.ninja API request fails or the expected ``data``
    or ``electricity`` fields are missing from the API response.

Notes
-----
Renewables.ninja returns hourly electricity generation based on the
specified PV system configuration and installed capacity. The function
uses a capacity of ``1.0 MW`` by default, allowing the returned
electricity values to represent the hourly capacity factor directly.

If a leap year produces 8784 hourly values, the final 24 hours are
removed to produce a standard 8760-hour annual profile.

The generated CSV has the following structure::

    hour,cf
    1,0.000
    2,0.000
    3,0.015
    ...

References
----------
Renewables.ninja API documentation:
https://www.renewables.ninja/documentation/api
"""