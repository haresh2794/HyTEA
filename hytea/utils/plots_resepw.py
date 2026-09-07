import os
import pandas as pd
import matplotlib.pyplot as plt


def rese_plots(
    rese_df=None,
    rese_results=None,
    source_columns=None,
    plot_type="hourly",
    start_hour=1,
    end_hour=None,
    plot_title=None,
    save_plot=False,
    plot_file=None,
    show_plot=True
):
    """
    Plot renewable electricity generation as a stacked area chart.

    Parameters
    ----------
    rese_df : pandas.DataFrame, optional
        Hourly renewable electricity generation dataframe.
        Required when plot_type="hourly".

    rese_results : dict, optional
        Renewable source results returned by run_rese_sources().
        Required when plot_type="cumulative".

        Expected structure:

        {
            "wind_1": {
                "hourly_output_mw": ...,
                "cumulative_energy_gwh_total": ...,
                "cumulative_energy_gwh_hourly": ...
            },
            "solar_1": {
                "hourly_output_mw": ...,
                "cumulative_energy_gwh_total": ...,
                "cumulative_energy_gwh_hourly": ...
            }
        }

    source_columns : list, optional
        Sources to include in the plot.

        For plot_type="hourly", these should be columns
        in rese_df.

        For plot_type="cumulative", these should be keys
        in rese_results.

        If None, all available renewable sources are plotted.

    plot_type : {"hourly", "cumulative"}, default="hourly"
        Type of plot:

        "hourly"
            Hourly renewable electricity generation (MW).

        "cumulative"
            Cumulative renewable energy generation (GWh).

    start_hour : int, default=1
        First hour to plot.

    end_hour : int, optional
        Last hour to plot.
        If None, all available hours are plotted.

    plot_title : str, optional
        Plot title.
        If None, a default title is generated based on plot_type.

    save_plot : bool, default=False
        If True, save the figure.

    plot_file : str, optional
        Output file path.
        If None, a default filename is generated.

    show_plot : bool, default=True
        If True, display the figure.

    Returns
    -------
    matplotlib.figure.Figure
        Generated figure.
    """

    # =========================================================
    # Validate plot type
    # =========================================================

    if plot_type not in ["hourly", "cumulative"]:
        raise ValueError(
            "plot_type must be either 'hourly' or 'cumulative'."
        )

    # =========================================================
    # HOURLY PLOT
    # =========================================================

    if plot_type == "hourly":

        # -----------------------------------------------------
        # Check input
        # -----------------------------------------------------

        if not isinstance(rese_df, pd.DataFrame):
            raise TypeError(
                "rese_df must be a pandas DataFrame "
                "when plot_type='hourly'."
            )

        # -----------------------------------------------------
        # Select source columns
        # -----------------------------------------------------

        if source_columns is None:
            source_columns = rese_df.select_dtypes(
                include="number"
            ).columns.tolist()

        if not source_columns:
            raise ValueError(
                "No numeric renewable source columns were found."
            )

        source_columns = list(source_columns)

        # -----------------------------------------------------
        # Check columns exist
        # -----------------------------------------------------

        missing_columns = [
            column
            for column in source_columns
            if column not in rese_df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Columns not found in rese_df: {missing_columns}"
            )

        # -----------------------------------------------------
        # Hour range
        # -----------------------------------------------------

        if end_hour is None:
            end_hour = len(rese_df)

        if start_hour < 1:
            raise ValueError(
                "start_hour must be greater than or equal to 1."
            )

        if end_hour > len(rese_df):
            raise ValueError(
                f"end_hour cannot exceed {len(rese_df)}."
            )

        if start_hour > end_hour:
            raise ValueError(
                "start_hour must be less than or equal to end_hour."
            )

        # -----------------------------------------------------
        # Select data
        # -----------------------------------------------------

        plot_df = rese_df.loc[
            start_hour - 1:end_hour - 1,
            source_columns
        ].copy()

        plot_df = plot_df.apply(
            pd.to_numeric,
            errors="coerce"
        ).fillna(0)

        # -----------------------------------------------------
        # Check source values
        # -----------------------------------------------------

        for column in source_columns:

            if plot_df[column].sum() == 0:

                print(
                    f"Warning: {column} contains no generation "
                    "in the selected period."
                )

        # -----------------------------------------------------
        # Hours
        # -----------------------------------------------------

        hours = range(
            start_hour,
            end_hour + 1
        )

        # -----------------------------------------------------
        # Labels
        # -----------------------------------------------------

        if plot_title is None:

            plot_title = (
                "Hourly Renewable Electricity Generation"
            )

        ylabel = (
            "Renewable Electricity Generation (MW)"
        )

        # -----------------------------------------------------
        # Plot file
        # -----------------------------------------------------

        if plot_file is None:

            plot_file = (
                "plots/rese_power_hourly.png"
            )

    # =========================================================
    # CUMULATIVE PLOT
    # =========================================================

    else:

        # -----------------------------------------------------
        # Check input
        # -----------------------------------------------------

        if not isinstance(rese_results, dict):
            raise TypeError(
                "rese_results must be a dictionary "
                "when plot_type='cumulative'."
            )

        if not rese_results:
            raise ValueError(
                "rese_results is empty."
            )

        # -----------------------------------------------------
        # Select renewable sources
        # -----------------------------------------------------

        if source_columns is None:

            source_columns = list(
                rese_results.keys()
            )

        else:

            source_columns = list(
                source_columns
            )

        if not source_columns:

            raise ValueError(
                "No renewable sources were found."
            )

        # -----------------------------------------------------
        # Check source names
        # -----------------------------------------------------

        missing_sources = [
            source
            for source in source_columns
            if source not in rese_results
        ]

        if missing_sources:

            raise ValueError(
                "Sources not found in rese_results: "
                f"{missing_sources}"
            )

        # -----------------------------------------------------
        # Check cumulative data
        # -----------------------------------------------------

        for source in source_columns:

            if (
                "cumulative_energy_gwh_hourly"
                not in rese_results[source]
            ):

                raise ValueError(
                    f"{source} does not contain "
                    "'cumulative_energy_gwh_hourly'."
                )

        # -----------------------------------------------------
        # Determine number of hours
        # -----------------------------------------------------

        n_hours = min(
            len(
                rese_results[source][
                    "cumulative_energy_gwh_hourly"
                ]
            )
            for source in source_columns
        )

        # -----------------------------------------------------
        # Hour range
        # -----------------------------------------------------

        if end_hour is None:

            end_hour = n_hours

        if start_hour < 1:

            raise ValueError(
                "start_hour must be greater than or equal to 1."
            )

        if end_hour > n_hours:

            raise ValueError(
                f"end_hour cannot exceed {n_hours}."
            )

        if start_hour > end_hour:

            raise ValueError(
                "start_hour must be less than or equal to end_hour."
            )

        # -----------------------------------------------------
        # Build cumulative dataframe
        # -----------------------------------------------------

        cumulative_data = {}

        for source in source_columns:

            cumulative_data[source] = (
                rese_results[source][
                    "cumulative_energy_gwh_hourly"
                ][
                    start_hour - 1:end_hour
                ]
            )

        plot_df = pd.DataFrame(
            cumulative_data
        )

        plot_df = plot_df.apply(
            pd.to_numeric,
            errors="coerce"
        ).fillna(0)

        # -----------------------------------------------------
        # Hours
        # -----------------------------------------------------

        hours = range(
            start_hour,
            end_hour + 1
        )

        # -----------------------------------------------------
        # Labels
        # -----------------------------------------------------

        if plot_title is None:

            plot_title = (
                "Cumulative Renewable Energy Generation"
            )

        ylabel = (
            "Cumulative Renewable Energy Generation (GWh)"
        )

        # -----------------------------------------------------
        # Plot file
        # -----------------------------------------------------

        if plot_file is None:

            plot_file = (
                "plots/rese_power_cumulative.png"
            )

    # =========================================================
    # CREATE FIGURE
    # =========================================================

    fig, ax = plt.subplots(
        figsize=(14, 6)
    )

    ax.grid(
        True,
        linestyle="--",
        alpha=0.5
    )

    # =========================================================
    # COLOURS
    # =========================================================

    cmap = plt.get_cmap("tab10")

    colors = [
        cmap(i)
        for i in range(len(source_columns))
    ]

    # =========================================================
    # STACKED AREA PLOT
    # =========================================================

    cumulative_stack = (
        plot_df[source_columns]
        .cumsum(axis=1)
    )

    previous_y = [
        0
    ] * len(hours)

    for i, column in enumerate(source_columns):

        current_y = (
            cumulative_stack[column].values
        )

        ax.fill_between(
            hours,
            previous_y,
            current_y,
            label=column,
            color=colors[i],
            alpha=1.0,
            edgecolor="none"
        )

        previous_y = current_y

    # =========================================================
    # LABELS
    # =========================================================

    ax.set_xlabel(
        "Hour of Year"
    )

    ax.set_ylabel(
        ylabel
    )

    ax.set_title(
        plot_title
    )

    ax.set_xlim(
        start_hour,
        end_hour
    )

    # =========================================================
    # LEGEND
    # =========================================================

    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        title="Renewable Sources"
    )

    # =========================================================
    # CLEAN BORDERS
    # =========================================================

    ax.spines[
        "top"
    ].set_visible(False)

    ax.spines[
        "right"
    ].set_visible(False)

    fig.tight_layout()

    # =========================================================
    # SAVE
    # =========================================================

    if save_plot:

        plot_dir = os.path.dirname(
            plot_file
        )

        if plot_dir:

            os.makedirs(
                plot_dir,
                exist_ok=True
            )

        fig.savefig(
            plot_file,
            dpi=300,
            bbox_inches="tight"
        )

        print(
            f"Plot saved to: {plot_file}"
        )

    # =========================================================
    # SHOW
    # =========================================================

    if show_plot:

        plt.show()
