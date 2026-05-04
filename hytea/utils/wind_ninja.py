import os
import requests
import pandas as pd


def generate_wind_cf_from_location(
    lat,
    lon,
    output_file="data/wind.csv",
    token=None,
    date_from="2020-01-01",
    date_to="2020-12-31",
    height=100,
    turbine="Vestas V90 2000",
    verbose=False,
    plot_cf=False,
    save_plot=False,
    plot_file="data/wind_cf_plot.png",
):
    """
    Fetch hourly wind capacity factor data from Renewables Ninja
    and save it as a CSV file with columns: hour, cf.

    Optional:
    - plot_cf=True   -> create a plot
    - save_plot=True -> save the plot image

    Parameters
    ----------
    lat : float
        Latitude.
    lon : float
        Longitude.
    output_file : str, optional
        Path to save the CSV file.
    token : str, optional
        Renewables Ninja API token.
    date_from : str, optional
        Start date in YYYY-MM-DD format.
    date_to : str, optional
        End date in YYYY-MM-DD format.
    height : float, optional
        Hub height in meters.
    turbine : str, optional
        Turbine model name supported by Renewables Ninja.
    verbose : bool, optional
        Whether to print progress messages.
    plot_cf : bool, optional
        Whether to generate a CF plot.
    save_plot : bool, optional
        Whether to save the CF plot.
    plot_file : str, optional
        Path to save the plot image.

    Returns
    -------
    str
        Path to generated CSV file.
    """

    if token is None:
        raise ValueError("Renewables Ninja API token required")

    url = "https://www.renewables.ninja/api/data/wind"

    headers = {
        "Authorization": f"Token {token}"
    }

    params = {
        "lat": lat,
        "lon": lon,
        "date_from": date_from,
        "date_to": date_to,
        "capacity": 1.0,
        "height": height,
        "turbine": turbine,
        "format": "json",
    }

    if verbose:
        print("Fetching wind resource data...")

    response = requests.get(url, params=params, headers=headers, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Renewables Ninja request failed: {response.status_code} - {response.text}"
        )

    data = response.json()

    if "data" not in data:
        raise RuntimeError("Expected 'data' field not found in API response.")

    df = pd.DataFrame.from_dict(data["data"], orient="index")

    if "electricity" not in df.columns:
        raise RuntimeError("Expected 'electricity' column not found in API response.")

    cf = df["electricity"].astype(float).values

    if len(cf) == 8784:
        cf = cf[:8760]

    wind_df = pd.DataFrame({
        "hour": range(1, len(cf) + 1),
        "cf": cf
    })

    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    wind_df.to_csv(output_file, index=False)

    if verbose:
        print(f"Wind file saved to {output_file}")

    if plot_cf or save_plot:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 4))
        plt.plot(wind_df["hour"], wind_df["cf"], linewidth=0.8)
        plt.xlabel("Hour of Year")
        plt.ylabel("Capacity Factor")
        plt.title("Hourly Wind Farm Capacity Factor")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if save_plot:
            plot_dir = os.path.dirname(plot_file)
            if plot_dir:
                os.makedirs(plot_dir, exist_ok=True)
            plt.savefig(plot_file, dpi=300, bbox_inches="tight")

            if verbose:
                print(f"Plot saved to {plot_file}")

        if plot_cf:
            plt.show()

        plt.close()

    return output_file


""" 
Sample use

csv_path = generate_wind_cf_from_location(
    lat=53.2707,
    lon=-9.0568,
    token="your_token_here",
    plot_cf=True,
    save_plot=True,
    plot_file="data/galway_wind_plot.png",
    verbose=True,
)

"""