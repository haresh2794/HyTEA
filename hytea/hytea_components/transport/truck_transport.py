import numpy as np
import yaml
import math

class HydrogenTruckTransport:
    """
    Hydrogen terrestrial transport via compressed tube trailer
    Hourly resolution
    H2 demand in kg/h per stream
    Energy in kWh
    """

    def __init__(self):
        # ---------------- Core input parameters ----------------
        self.truck_type = None
        self.transport_method = None
        self.P0_bar = None  # Electrolyser pressure
        self.P1_bar = None  # Storage pressure
        self.P2_bar = None  # Trailer/transport pressure
        self.Q1_kgph = None  # Max flow P1-P0
        self.Q2_kgph = None  # Max flow P2-P1
        self.distance_km = None
        self.number_of_trucks = None

        #------------core outputs-------------
        self.total_capex = None
        self.total_opex_per_year = None
        self.total_ghg_per_year = None
        self.booster_spec_elec_consumption = None
        self.trailer_fill_time_h = None
        self.trailer_load_kg = None

        #--------overall secondary outputs---------
        self.capex_per_truck = None
        self.tractor_capex_as_opex = None
        self.salary_per_truck = None
        self.recertification_per_truck = None
        self.fuel_per_truck = None
        self.other_o_n_m_per_truck = None

        self.total_tractor_capex_as_opex = None
        self.total_salary = None
        self.total_recertification = None
        self.total_fuel = None
        self.total_other_o_n_m = None

        self.truck_fleet_capex = None
        self.truck_fleet_opex = None
        self.truck_fleet_ghg = None
        self.truck_speed_kmh = None

        self.total_annual_h2_kg = None
        self.tonnes_per_truck_kg = None
        self.turns_per_truck = None
        self.annual_distance_per_truck_km = None
        self.truck_speed_kmh = None

        self.tractor_capex= None
        self.spec_fuel_kWh_per_km= None
        self.fuel_price_per_kWh= None
        self.fuel_ghg_gCO2_per_kWh= None
        self.drivers_per_truck= None
        self.other_employees_per_truck= None
        self.employee_salary= None
        self.trailer_om_per_km= None
        self.recertification_fraction= None
        self.trailer_capex= None
        self.opex_per_truck= None
        self.booster_capex_total= None
        self.booster_opex_total= None
        self.turns_per_truck= None
        self.tonnes_per_truck_kg= None


        self.tractor_cost_defaults = {
            'Diesel': {
                'tractor_capex': 150000,
                'spec_fuel_kWh_per_km': 3.29, #kWh/km/truck
                'fuel_price_per_kWh': 0.20, #€/kWh/truck
                'fuel_price_per_km': 0.20*3.29, #€/km/truck
                'fuel_ghg_g_per_kWh': 263, #gCO2/kWh/truck
                'drivers_per_truck': 4,
                'other_employees_per_truck': 1.1,
                'employee_salary': 40000

            },
            'FCEV_now': {
                'tractor_capex': 500000,
                'spec_fuel_kWh_per_km': 2.97,
                'fuel_price_per_kWh': 0.60,
                'fuel_price_per_km': 0.60*2.97, #€/km/truck
                'fuel_ghg_g_per_kWh': 0,
                'drivers_per_truck': 4,
                'other_employees_per_truck': 1.1,
                'employee_salary': 40000
            },
            'FCEV_2030': {
                'tractor_capex': 150000,
                'spec_fuel_kWh_per_km': 2.31,
                'fuel_price_per_kWh': 0.30,
                'fuel_price_per_km': 0.30*2.31, #€/km/truck
                'fuel_ghg_g_per_kWh': 0,
                'drivers_per_truck': 4,
                'other_employees_per_truck': 1.1,
                'employee_salary': 40000
            }
        }

        # Trailer defaults
        self.trailer_defaults = {
            'Compressed': {
                'o_n_m_per_km': 0.4,    # €/km/trailer
                'trailer_fill_time_h': 1, #hours
                'pressure_load_capex': {    # max load & cost by pressure
                    200: (580, 558000),
                    250: (690, 677721),
                    350: (840, 840977),
                    450: (970, 982465),
                    500: (1010, 1026000)
                },
                'recertification_fraction': 0.3 #of trailer capex/yr
            },
            'Liquid': {
                'base_capex': 720000,
                'trailer_fill_time_h': 3, #hours
                'o_n_m_per_km': 0.4,
                'recertification_fraction': 0.3 #of trailer capex/yr
            }
        }

        # Boost compressor parameters (calculated from P0, P2, Q2)
        self.sec_boost_kWh_per_kg = None
        self.boost_spec_capex = None
        self.boost_opex_eur_per_year = None
        self._lookup_boost_sec_table = {
                            0:  (0.00433, 4.13),
                            15: (0.00367, 1.72),
                            30: (0.00333, 1.13),
                            60: (0.00300, 0.68)
                        }


    # ---------------- Default Methods ----------------
    def _default_truck_type(self): return 'Diesel'
    def _default_transport_method(self): return 'Compressed'
    def _default_P0_bar(self): return 15
    def _default_P1_bar(self): return 300
    def _default_P2_bar(self): return 350
    def _default_Q1_kgph(self): return 72.29
    def _default_Q2_kgph(self): return 54.17
    def _default_distance_km(self): return 100
    def _default_truck_speed(self): return 60

 



    # ---------------- Derived Calculations ----------------

    # ---------------- Minimum Fleet Calculation ----------------
    def _calc_min_trailers(self):
        """
        Calculates minimum number of trailers required for steady-state supply chain.
        Updates self.number_of_trucks.

        """

        if self.trailer_load_kg is None or self.trailer_load_kg <= 0:
            raise ValueError("trailer_load_kg must be set and >0 before calculating fleet")

        if self.Q2_kgph is None or self.trailer_load_kg is None:
            raise ValueError("Q2_kgph (supply) and trailer_load_kg must be set before calculating fleet")

        # Calculate total transit time (hours)
        time_to_user = self.distance_km / self.truck_speed_kmh
        time_to_return = self.distance_km / self.truck_speed_kmh
        total_transit_time = time_to_user + self.trailer_fill_time_h + time_to_return + 1  # +1h idling at origin
        transit_steps = max(1, round(total_transit_time))

        # Trailers in transit
        trailers_in_transit = (self.Q2_kgph * transit_steps) / self.trailer_load_kg  

        # Trailers being filled per hour (partial counts as 1)
        trailers_being_filled = math.ceil(self.Q2_kgph / self.trailer_load_kg)

        # Total minimum fleet
        self.number_of_trucks = math.ceil(trailers_in_transit + trailers_being_filled)

        return self.number_of_trucks


    def _calc_annual_truck_metrics(self):
          """
          Calculates annual transport metrics per truck based on steady-state flow.
          
          Returns:
              total_annual_h2_kg
              tonnes_per_truck_kg
              turns_per_truck
              annual_distance_per_truck_km
          """
          if self.number_of_trucks is None or self.number_of_trucks <= 0:
              raise ValueError("number_of_trucks must be set and >0 before computing annual metrics")

          if self.trailer_load_kg is None or self.trailer_load_kg <= 0:
              raise ValueError("trailer_load_kg must be >0 before calculating turns per truck")

          #  Total annual hydrogen transported (kg/year)
          self.total_annual_h2_kg = self.Q2_kgph * 8760

          # Safety check
          if self.number_of_trucks <= 0:
              return 0.0, 0.0, 0.0, 0.0

          # Hydrogen transported per truck per year (kg/year)
          self.tonnes_per_truck_kg = self.total_annual_h2_kg / self.number_of_trucks

          # Number of turns per truck per year
          self.turns_per_truck = self.tonnes_per_truck_kg / self.trailer_load_kg

          # Total annual round-trip distance per truck (km/year)
          self.annual_distance_per_truck_km = (
              2 * self.distance_km * self.turns_per_truck
          )


    #------------Booster -------------

    def _calc_compressor_spec_capex(self, pout_bar):
        """
        Compressor CAPEX for compression from P0_bar to pout_bar
        """
        table = {
            0:  (95.16, 126.05, -0.34),
            15: (68.95, 79.24, -0.34),
            30: (64.66, 77.77, -0.34),
            60: (61.07, 68.25, -0.34),
        }

        pin = self.P0_bar
        Q = self.Q2_kgph

       

        if pin not in table:
            raise ValueError("P0_bar must be one of: 0, 15, 30, 60 barg")

        A200, A500, B = table[pin]

        A = A200 + (pout_bar - 200) / (500 - 200) * (A500 - A200)

        return 1000 * A * Q**B



    def _calc_sec_boost(self, P_target):
        """
        Specific compression energy (kWh/kg) from P0_bar to P_target.
        """
        if self.P0_bar not in self._lookup_boost_sec_table:
            raise ValueError("P0_bar must be one of: 0, 15, 30, 60 barg")

        slope, intercept = self._lookup_boost_sec_table[self.P0_bar]

        if P_target <= self.P0_bar:
            return 0.0

        return slope * (P_target - self.P0_bar) + intercept





    # ---------------- Configure ----------------
    def configure(self, config=None, config_file=None):
        if config is not None:
            cfg = config
        elif config_file is not None:
            with open(config_file,'r') as f:
                cfg = yaml.safe_load(f)
        else:
            cfg = {}

        # Core inputs
        self.P0_bar = cfg.get('P0_bar', self._default_P0_bar())
        self.P1_bar = cfg.get('P1_bar', self._default_P1_bar())
        self.P2_bar = cfg.get('P2_bar', self._default_P2_bar())
        self.Q1_kgph = cfg.get('Q1_kgph', self._default_Q1_kgph())
        self.Q2_kgph = cfg.get('Q2_kgph', self._default_Q2_kgph())
        self.distance_km = cfg.get('distance_km', self._default_distance_km())
        self.truck_speed_kmh = cfg.get('truck_speed_kmh', self._default_truck_speed())



        # Tractor
        # ---------------- Truck Type ----------------
        self.truck_type = cfg.get('truck_type', self._default_truck_type())

        if self.truck_type not in self.tractor_cost_defaults:
            raise ValueError(f"Invalid truck_type: {self.truck_type}")

        tractor_defaults = self.tractor_cost_defaults[self.truck_type]




        # ---------------- Tractor ----------------
        self.tractor_capex = cfg.get('tractor_capex', tractor_defaults['tractor_capex'])
        self.spec_fuel_kWh_per_km = cfg.get('spec_fuel_kWh_per_km', tractor_defaults['spec_fuel_kWh_per_km'])
        self.fuel_price_per_kWh = cfg.get('fuel_price_per_kWh', tractor_defaults['fuel_price_per_kWh'])
        self.fuel_ghg_gCO2_per_kWh = cfg.get('fuel_ghg_gCO2_per_kWh', tractor_defaults['fuel_ghg_g_per_kWh'])
        self.drivers_per_truck = cfg.get('drivers_per_truck', tractor_defaults['drivers_per_truck'])
        self.other_employees_per_truck = cfg.get('other_employees_per_truck', tractor_defaults['other_employees_per_truck'])
        self.employee_salary = cfg.get('employee_salary', tractor_defaults['employee_salary'])




        # Trailer
        # ---------------- Transport Method ----------------
        self.transport_method = cfg.get('transport_method', self._default_transport_method())

        if self.transport_method not in self.trailer_defaults:
            raise ValueError(f"Invalid transport_method: {self.transport_method}")

        trailer_defaults = self.trailer_defaults[self.transport_method]

        # Common trailer parameters
        self.trailer_om_per_km = cfg.get('trailer_om_per_km', trailer_defaults['o_n_m_per_km'])
        self.recertification_fraction = cfg.get('recertification_fraction', trailer_defaults['recertification_fraction'])

        # ---------------- Compressed Trailer ----------------
        if self.transport_method == 'Compressed':

            self.trailer_fill_time_h = cfg.get(
                'trailer_fill_time_h',
                trailer_defaults['trailer_fill_time_h']
            )

            trailer_table = trailer_defaults['pressure_load_capex']

            pressures = np.array(list(trailer_table.keys()))
            nearest_p = pressures[np.abs(pressures - self.P2_bar).argmin()]

            self.trailer_load_kg, self.trailer_capex = trailer_table[nearest_p]


            # Booster CAPEX only if P2 > P1
            if self.P2_bar > self.P1_bar:

                capex_P2 = self._calc_compressor_spec_capex(self.P2_bar)
                capex_P1 = self._calc_compressor_spec_capex(self.P1_bar)

                self.boost_spec_capex = capex_P2 - capex_P1

            else:
                self.boost_spec_capex = 0

            # ---- Booster Specific Energy ----

            self.sec_boost_kWh_per_kg = self._calc_sec_boost(self.P2_bar) - self._calc_sec_boost(self.P1_bar)

        # ---------------- Liquid Trailer ----------------
        elif self.transport_method == 'Liquid':

            self.trailer_fill_time_h = cfg.get('trailer_fill_time_h', trailer_defaults['trailer_fill_time_h'])

            self.trailer_capex = trailer_defaults['base_capex']
            self.trailer_load_kg = 4600

            # No booster for liquid
            self.boost_spec_capex = 0
            self.sec_boost_kWh_per_kg = 0

      
    # Calculate minimum fleet after all inputs are configured
        self._calc_min_trailers()
    
    

    # ---------------- Evaluate ----------------
    
    
    def evaluate(self):
            """
            Calculates truck/fleet metrics based on configured parameters.
            Outputs are stored as attributes and returned in a dictionary.
            """

            # Ensure annual truck metrics are calculated first
            self._calc_annual_truck_metrics()

            # --- Distance per truck per year ---
            annual_distance_per_truck_km = self.annual_distance_per_truck_km

            # --- Capex per truck (trailer only) ---
            capex_per_truck = self.trailer_capex

            # --- Tractor capex as opex per truck ---
            tractor_capex_as_opex = self.tractor_capex*0.8 / 5 #0.8 for substracting the resale price

            # --- Fuel per truck ---
            fuel_per_truck = self.spec_fuel_kWh_per_km * self.fuel_price_per_kWh * annual_distance_per_truck_km

            # --- Salary per truck ---
            salary_per_truck = (self.drivers_per_truck + self.other_employees_per_truck) * self.employee_salary

            # --- Recertification per truck ---
            recertification_per_truck = self.trailer_capex * self.recertification_fraction

            # --- Other O&M per truck ---
            other_o_n_m_per_truck = self.trailer_om_per_km * annual_distance_per_truck_km

            # --- Opex per truck ---
            opex_per_truck = tractor_capex_as_opex + fuel_per_truck + salary_per_truck + recertification_per_truck + other_o_n_m_per_truck

            # --- Number of trucks needed ---
            number_of_trucks = self.number_of_trucks

            # --- Fleet-level metrics ---
            truck_fleet_capex = capex_per_truck * number_of_trucks
            truck_fleet_opex = opex_per_truck * number_of_trucks

            # Fuel CO2 emissions per fleet (tCO2/yr)
            fuel_ghg_tCO2_per_truck = self.fuel_ghg_gCO2_per_kWh * self.spec_fuel_kWh_per_km * annual_distance_per_truck_km / 1e6

            # --- Booster for compressed H2 ---
            booster_capex_total = 0
            booster_opex_total = 0
            if self.transport_method == 'Compressed' and self.boost_spec_capex > 0:
                booster_capex_total = self.boost_spec_capex * self.Q2_kgph
                booster_opex_total = booster_capex_total * 0.2
                truck_fleet_capex += booster_capex_total
                truck_fleet_opex += booster_opex_total

            # --- Fleet totals per category ---
            total_fuel = fuel_per_truck * number_of_trucks
            total_salary = salary_per_truck * number_of_trucks
            total_recertification = recertification_per_truck * number_of_trucks
            total_other_o_n_m = other_o_n_m_per_truck * number_of_trucks
            total_tractor_capex_as_opex = tractor_capex_as_opex * number_of_trucks
            total_ghg_per_year = fuel_ghg_tCO2_per_truck * number_of_trucks

            # --- Store as attributes ---
            self.annual_distance_per_truck_km = annual_distance_per_truck_km
            self.capex_per_truck = capex_per_truck
            self.tractor_capex_as_opex = tractor_capex_as_opex
            self.fuel_per_truck = fuel_per_truck
            self.salary_per_truck = salary_per_truck
            self.recertification_per_truck = recertification_per_truck
            self.other_o_n_m_per_truck = other_o_n_m_per_truck
            self.opex_per_truck = opex_per_truck
            self.number_of_trucks = number_of_trucks
            self.truck_fleet_capex = truck_fleet_capex
            self.truck_fleet_opex = truck_fleet_opex
            self.total_ghg_per_year = total_ghg_per_year
            self.booster_capex_total = booster_capex_total
            self.booster_opex_total = booster_opex_total

            self.total_fuel = total_fuel
            self.total_salary = total_salary
            self.total_recertification = total_recertification
            self.total_other_o_n_m = total_other_o_n_m
            self.total_tractor_capex_as_opex = total_tractor_capex_as_opex

            self.booster_spec_elec_consumption = self.sec_boost_kWh_per_kg



            # --- Return dictionary ---
            return {
                "annual_distance_per_truck_km": annual_distance_per_truck_km,
                "capex_per_truck": capex_per_truck,
                "tractor_capex_as_opex": tractor_capex_as_opex,
                "fuel_per_truck": fuel_per_truck,
                "salary_per_truck": salary_per_truck,
                "recertification_per_truck": recertification_per_truck,
                "other_o_n_m_per_truck": other_o_n_m_per_truck,
                "opex_per_truck": opex_per_truck,
                "number_of_trucks": number_of_trucks,
                "truck_fleet_capex": truck_fleet_capex,
                "truck_fleet_opex": truck_fleet_opex,
                "total_ghg_per_year": total_ghg_per_year,
                "booster_capex_total": booster_capex_total,
                "booster_opex_total": booster_opex_total,
                "booster_spec_elec_consumption": self.sec_boost_kWh_per_kg,
                "total_fuel": total_fuel,
                "total_salary": total_salary,
                "total_recertification": total_recertification,
                "total_other_o_n_m": total_other_o_n_m,
                "total_tractor_capex_as_opex": total_tractor_capex_as_opex
            }
