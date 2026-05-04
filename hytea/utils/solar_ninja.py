import os
import requests
import pandas as pd


def generate_solar_cf_from_location(
    lat,
    lon,
    output_file="data/solar.csv",
    token=None,
    date_from="2020-01-01",
    date_to="2020-12-31",
    system_loss=0.1,
    tracking=0,
    tilt=35,
    azim=180,
    capacity=1.0,
    verbose=False,
    plot_cf=False,
    save_plot=False,
    plot_file="data/solar_cf_plot.png",
):
    """
    Fetch hourly solar PV capacity factor data from Renewables Ninja
    and save it as a CSV file with columns: hour, cf.
    """

    if token is None:
        raise ValueError("Renewables Ninja API token required")

    url = "https://www.renewables.ninja/api/data/pv"

    headers = {
        "Authorization": f"Token {token}"
    }

    params = {
        "lat": lat,
        "lon": lon,
        "date_from": date_from,
        "date_to": date_to,
        "system_loss": system_loss,
        "tracking": tracking,
        "tilt": tilt,
        "azim": azim,
        "capacity": capacity,
        "format": "json",
    }

    if verbose:
        print("Fetching solar resource data...")

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

    # remove leap year if present
    if len(cf) == 8784:
        cf = cf[:8760]

    solar_df = pd.DataFrame({
        "hour": range(1, len(cf) + 1),
        "cf": cf
    })

    # SAFE DIRECTORY HANDLING (IMPORTANT FIX)
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    solar_df.to_csv(output_file, index=False)

    if verbose:
        print(f"Solar file saved to {output_file}")

    # plotting
    if plot_cf or save_plot:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 4))
        plt.plot(solar_df["hour"], solar_df["cf"], linewidth=0.8)
        plt.xlabel("Hour of Year")
        plt.ylabel("Capacity Factor")
        plt.title("Hourly Solar PV Capacity Factor")
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