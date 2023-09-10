import numpy as np

from powerplant import IPumpStoragePlant


class IScheduleOptimization:
    """
    Interface for optimisation of pump storage plant schedule, bases on a price timeserie.
    This interface is not to be used for intrinsic rolling, only the optimisation of a single schedule.
    """

    def __init__(self, ppt: IPumpStoragePlant):
        self.ppt = ppt
        self.min_timestep = 0.25
        self.energy_lvl_step = self.get_possible_energy_level(self.min_timestep)

    def calculate_optimal_schedule(self,
                                   electricity_price: list[float],
                                   initial_energy_level: float,
                                   previous_last_action: int,
                                   final_energy_level: float,
                                   mw_to_mwh_factors: list[float]):
        """
        The objective is to maximise the profit of the plant.
        In this function we do it only for one market level.
        All the power is electric input/output power in MW.
        The timestep size can be specified with the mw_to_mwh_factors parameter.

        Parameters
        ----------
        electricity_price : list of float
            The electricity price for each timestep in the market level.
        initial_energy_level : float
            The initial energy level of the plant in MWh of electricity that can be
                produced (after efficiency losses in pumping and turbining).
        previous_last_action : int
            The last action of the previous schedule.
            0 if no action, 1 if pump, -1 if turb.
        final_energy_level : float
            Same than initial_energy_level but for the final energy level
        mw_to_mwh_factors : list of float
            The factor to convert MW to MWh.
            It is one if the timestep is one hour, is 1/4 if the timestep is 15 minutes.
            List of different values, so that the timestep size can be different for each timestep.
        """
        pass

    def get_possible_energy_level(self, min_timestep):
        """
        Finde a goold value for the energy level step.
        The energy level step is the smallest possible change in energy level.
        Returns
        -------
        Smallest level change in MWh.
        """
        smallest_pump_energy = self.ppt.get_max_pump_power() * min_timestep * self.ppt.get_pump_efficiency()
        smallest_turb_energy = self.ppt.get_max_turb_power() * min_timestep

        # LCM of smallest_pump_energy and smallest_turb_energy
        precision = 100000  # This is needed because np.gcd only supports integers
        return np.gcd(int(smallest_pump_energy * precision), int(smallest_turb_energy * precision)) / precision
