WIND_CF_DOC = """
        Generate hourly wind capacity factor data for a specified location
        using the Renewables.ninja Wind API.

        The function sends a request to Renewables.ninja using the specified
        latitude, longitude, time period, hub height, and turbine model. The
        returned hourly electricity generation is converted to a capacity
        factor and saved as a CSV file with the columns ``hour`` and ``cf``.

        Renewables.ninja API access
        ---------------------------
        A Renewables.ninja API token is required for authenticated requests.

        To obtain an API token:

        1. Create a free account at:
        https://www.renewables.ninja/

        2. Log in to your Renewables.ninja account.

        3. Open your profile page and locate the API token.

        4. Copy the token and provide it to this function using the ``token``
        argument.

        Example
        -------

        from hytea.utils import generate_wind_cf_from_location

        generate_wind_cf_from_location(
            lat=53.27,
            lon=-9.05,
            token="YOUR_RENEWABLES_NINJA_TOKEN",
            plot_cf=True,
            save_plot=True,
            plot_file=f"plots/wind_cf.png"
         )

        Parameters
        ----------
        lat : float
            Latitude of the wind farm location in decimal degrees.

        lon : float
            Longitude of the wind farm location in decimal degrees.

        output_file : str, optional
            Path to the CSV file where the hourly wind capacity factor data
            will be saved. Default is ``"data/wind.csv"``.

        token : str, optional
            Renewables.ninja API token. A token is required to access the
            authenticated API.

        date_from : str, optional
            Start date for the simulation in ``YYYY-MM-DD`` format.
            Default is ``"2020-01-01"``.

        date_to : str, optional
            End date for the simulation in ``YYYY-MM-DD`` format.
            Default is ``"2020-12-31"``.

        height : float, optional
            Wind turbine hub height in metres. The value should be supported
            by the selected Renewables.ninja wind model.
            Default is ``100``.

        turbine : str, optional
            Renewables.ninja turbine model used to calculate wind power output.
            Default is ``"Vestas V90 2000"``.

        verbose : bool, optional
            If ``True``, print progress and output-file information.
            Default is ``False``.

        plot_cf : bool, optional
            If ``True``, display a plot of the hourly wind capacity factor.
            Default is ``False``.

        save_plot : bool, optional
            If ``True``, save the capacity factor plot to ``plot_file``.
            Default is ``False``.

        plot_file : str, optional
            Path where the capacity factor plot will be saved when
            ``save_plot=True``. Default is
            ``"plots/wind_cf_plot.png"``.

        Returns
        -------
        str
            Path to the generated CSV file.

        Raises
        ------
        ValueError
            If a Renewables.ninja API token is not provided.

        RuntimeError
            If the Renewables.ninja API request fails or the expected
            ``data`` or ``electricity`` fields are missing from the response.

        Notes
        -----
        Renewables.ninja returns hourly electricity output for a wind turbine
        with the specified installed capacity. Since the requested capacity
        is set to 1 MW, the resulting ``electricity`` values correspond to
        hourly capacity factors.

        The function also handles leap years by removing the final 24 hours
        when 8784 hourly values are returned, producing a standard
        8760-hour annual profile.

        The resulting CSV has the following structure::

            hour,cf
            1,0.234
            2,0.187
            3,0.152
            ...

     
    """