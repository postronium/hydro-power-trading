import numpy as np

from optimize import IScheduleOptimization
from powerplant import IPumpStoragePlant

class DynamicProgrammingOptimisation(IScheduleOptimization):
    """
    Deprecated, use DynamicProgrammingOptimisationFast instead.
    """

    def __init__(self, ppt: IPumpStoragePlant):
        super().__init__(ppt)

    def calculate_optimal_schedule(self,
                                   electricity_price: list[float],
                                   initial_energy_level: float,
                                   previous_last_action: int,
                                   final_energy_level: float,
                                   mw_to_mwh_factors: list[float]):

        n_energy_levels = int((self.ppt.get_max_level() / self.energy_lvl_step) + 1)

        # max profit for each state
        profit_matrix = np.ones((len(electricity_price) + 1, n_energy_levels)) * -np.inf
        profit_matrix[len(electricity_price)][int(final_energy_level / self.energy_lvl_step)] = 0

        # optimal decision for each state
        # zero is no action, one is pump, negative one is turb
        decisions = np.zeros((len(electricity_price) + 1, n_energy_levels))

        for i in range(len(electricity_price), 0, -1):
            for lvl in range(n_energy_levels):
                next_i = i - 1
                # no action
                if (profit_matrix[i][lvl] > profit_matrix[next_i][lvl]):
                    profit_matrix[next_i][lvl] = profit_matrix[i][lvl]
                    decisions[next_i][lvl] = 0

                # pump
                level_pump = int(lvl - (self.ppt.get_max_pump_power() * mw_to_mwh_factors[
                    next_i] * self.ppt.get_pump_efficiency() / self.energy_lvl_step))
                if (level_pump >= 0 and decisions[i][lvl] != -1 and (next_i != 0 or previous_last_action != 1)):
                    profit_change_pump = profit_matrix[i][lvl] - (
                            self.ppt.get_max_pump_power() * mw_to_mwh_factors[next_i] * electricity_price[next_i])
                    if (profit_change_pump > profit_matrix[next_i][level_pump]):
                        profit_matrix[next_i][level_pump] = profit_change_pump
                        decisions[next_i][level_pump] = 1

                # turb
                level_turb = int(lvl + self.ppt.get_max_turb_power() * mw_to_mwh_factors[next_i] / self.energy_lvl_step)
                if (level_turb < n_energy_levels and decisions[i][lvl] != 1 and (
                        next_i != 0 or previous_last_action != -1)):
                    profit_change_turb = profit_matrix[i][lvl] + (
                            self.ppt.get_max_turb_power() * mw_to_mwh_factors[next_i] * electricity_price[next_i])
                    if (profit_change_turb > profit_matrix[next_i][level_turb]):
                        profit_matrix[next_i][level_turb] = profit_change_turb
                        decisions[next_i][level_turb] = -1

        sell_mwh = np.zeros(len(electricity_price))
        buy_mwh = np.zeros(len(electricity_price))

        energy_lvl = [0 for i in range(len(electricity_price) + 1)]

        energy_lvl[0] = int(initial_energy_level / self.energy_lvl_step)
        for i in range(0, len(electricity_price), 1):
            action = decisions[i][energy_lvl[i]]
            if (action == 0):
                sell_mwh[i] = 0
                buy_mwh[i] = 0
                energy_lvl[i + 1] = energy_lvl[i]
            elif (action == 1):
                sell_mwh[i] = 0
                buy_mwh[i] = self.ppt.get_max_pump_power() * mw_to_mwh_factors[i]
                energy_lvl[i + 1] = int(energy_lvl[i] + (self.ppt.get_max_pump_power() * mw_to_mwh_factors[
                    i] * self.ppt.get_pump_efficiency() / self.energy_lvl_step))
            elif (action == -1):
                sell_mwh[i] = self.ppt.get_max_turb_power() * mw_to_mwh_factors[i]
                buy_mwh[i] = 0
                energy_lvl[i + 1] = int(
                    energy_lvl[i] - (self.ppt.get_max_turb_power() * mw_to_mwh_factors[i] / self.energy_lvl_step))

        return {
            'total_cashflow': profit_matrix[0][int(initial_energy_level / self.energy_lvl_step)],
            'sell_mwh': sell_mwh,
            'buy_mwh': buy_mwh,
            'hourly_energy_level': [lvl * self.energy_lvl_step for lvl in energy_lvl][1:]
        }