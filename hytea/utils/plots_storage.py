import matplotlib.pyplot as plt
import os
from .documentation.plots_storage_doc import STORAGE_PLOTS_DOC

def storage_plots(
    storage_results,
    plots,
    figsize=(15, 5),
    title_fontsize=16,
    axis_fontsize=13,
    tick_fontsize=11,
    linewidth=1.5,
    grid=True,
    save_plot=False,
    plot_file_prefix="plots/storage"
):
    
    storage_plots.__doc__ = STORAGE_PLOTS_DOC
    # ----------------------------------------------------------
    # Validation
    # ----------------------------------------------------------

    if not isinstance(plots, list) or not plots:
        raise ValueError(
            "'plots' must be a non-empty list of dictionaries."
        )

    # ----------------------------------------------------------
    # Create output folder if required
    # ----------------------------------------------------------

    if save_plot:
        os.makedirs(
            plot_file_prefix,
            exist_ok=True
        )

    # ----------------------------------------------------------
    # Generate plots
    # ----------------------------------------------------------

    for plot in plots:

        if "key" not in plot:
            raise KeyError(
                "Each plot definition must contain a 'key'."
            )

        key = plot["key"]

        # ------------------------------------------------------
        # Check result exists
        # ------------------------------------------------------

        if key not in storage_results:
            raise KeyError(
                f"'{key}' not found in storage_results."
            )

        # ------------------------------------------------------
        # Plot settings
        # ------------------------------------------------------

        title = plot.get(
            "title",
            key.replace("_", " ").title()
        )

        xlabel = plot.get(
            "xlabel",
            "Hour"
        )

        ylabel = plot.get(
            "ylabel",
            key.replace("_", " ").title()
        )

        filename = plot.get(
            "filename",
            f"{key}.png"
        )

        # ------------------------------------------------------
        # Create figure
        # ------------------------------------------------------

        plt.figure(
            figsize=figsize
        )

        plt.plot(
            storage_results[key],
            linewidth=linewidth
        )

        # ------------------------------------------------------
        # Labels
        # ------------------------------------------------------

        plt.xlabel(
            xlabel,
            fontsize=axis_fontsize
        )

        plt.ylabel(
            ylabel,
            fontsize=axis_fontsize
        )

        plt.title(
            title,
            fontsize=title_fontsize
        )

        # ------------------------------------------------------
        # Tick fonts
        # ------------------------------------------------------

        plt.xticks(
            fontsize=tick_fontsize
        )

        plt.yticks(
            fontsize=tick_fontsize
        )

        # ------------------------------------------------------
        # Grid
        # ------------------------------------------------------

        if grid:
            plt.grid(True)

        # ------------------------------------------------------
        # Layout
        # ------------------------------------------------------

        plt.tight_layout()

        # ------------------------------------------------------
        # Save
        # ------------------------------------------------------

        if save_plot:

            plot_path = os.path.join(
                plot_file_prefix,
                filename
            )

            plt.savefig(
                plot_path,
                dpi=300,
                bbox_inches="tight"
            )

        # ------------------------------------------------------
        # Show
        # ------------------------------------------------------

        plt.show()