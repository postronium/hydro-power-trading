import numpy as np

from optimize import IScheduleOptimization
from powerplant import IPumpStoragePlant


class DynamicProgrammingOptimisationFast(IScheduleOptimization):
    def __init__(self, ppt: IPumpStoragePlant):
        super().__init__(ppt)
        self.n_energy_levels = int((self.ppt.get_max_level() / self.energy_lvl_step) + 1)
        self.delta_lvl_pump = +self.ppt.get_max_pump_power() * self.ppt.get_pump_efficiency() / self.energy_lvl_step
        self.delta_lvl_turb = -self.ppt.get_max_turb_power() / self.energy_lvl_step

    def calculate_optimal_schedule(self,
                                   prices: list[float],
                                   initial_energy_lvl: float,
                                   previous_last_action: int,
                                   final_energy_lvl: float,
                                   mw_to_mwh_factors: list[float]):
        """
        Optimisation using dynamic programming.
        For more informations, see documentation of parent class.
        """
        final_energy_lvl = int(final_energy_lvl / self.energy_lvl_step)
        profits, decisions = self.build_matrix(prices, self.n_energy_levels, previous_last_action, final_energy_lvl,
                                               mw_to_mwh_factors)
        sell_mwh = np.zeros(len(prices))
        buy_mwh = np.zeros(len(prices))

        energy_lvl = [0 for i in range(len(prices) + 1)]
        energy_lvl[0] = int(initial_energy_lvl / self.energy_lvl_step)
        for i in range(0, len(prices), 1):
            action = decisions[i][energy_lvl[i]]
            if (action == 0):
                sell_mwh[i] = 0
                buy_mwh[i] = 0
                energy_lvl[i + 1] = energy_lvl[i]
            elif (action == 1):
                sell_mwh[i] = 0
                buy_mwh[i] = self.ppt.get_max_pump_power() * mw_to_mwh_factors[i]
                energy_lvl[i + 1] = int(energy_lvl[i] + mw_to_mwh_factors[i] * self.delta_lvl_pump)
            elif (action == -1):
                sell_mwh[i] = self.ppt.get_max_turb_power() * mw_to_mwh_factors[i]
                buy_mwh[i] = 0
                energy_lvl[i + 1] = int(energy_lvl[i] + mw_to_mwh_factors[i] * self.delta_lvl_turb)

        return {
            'total_cashflow': profits[energy_lvl[0]],
            'sell_mwh': sell_mwh,
            'buy_mwh': buy_mwh,
            'hourly_energy_level': [lvl * self.energy_lvl_step for lvl in energy_lvl][1:]
        }

    def build_matrix(self,
                     electricity_price: list[float],
                     n_energy_levels: int,
                     previous_last_action: int,
                     final_energy_level: int,
                     mw_to_mwh_factors: list[float]):
        """
        Create a decision matrix according to prices.
        """

        profits_previous = np.ones(n_energy_levels) * -np.inf
        profits_previous[final_energy_level] = 0
        profits_next = np.ones(n_energy_levels) * -np.inf
        decisions = np.zeros((len(electricity_price) + 1, n_energy_levels))

        # Iterate backwards, next is more in the passt
        for i in range(len(electricity_price), 0, -1):
            next_i = i - 1
            mw_to_mwh_factor = mw_to_mwh_factors[next_i]

            cash_delta_pump = -self.ppt.get_max_pump_power() * mw_to_mwh_factor * electricity_price[next_i]
            cash_delta_turb = +self.ppt.get_max_turb_power() * mw_to_mwh_factor * electricity_price[next_i]

            # Change in energy level when goint from future to past
            lvl_delta_pump = - int(
                self.ppt.get_max_pump_power() * self.ppt.get_pump_efficiency() * mw_to_mwh_factor / self.energy_lvl_step)
            lvl_delta_turb = + int(self.ppt.get_max_turb_power() * mw_to_mwh_factor / self.energy_lvl_step)

            previous_decisions = decisions[i]
            next_decisions = decisions[next_i]

            for lvl in range(n_energy_levels):
                # pump
                new_level = lvl + lvl_delta_pump
                if (new_level >= 0 and previous_decisions[lvl] != -1 and (next_i != 0 or previous_last_action != 1)):
                    profit_change_pump = profits_previous[lvl] + cash_delta_pump
                    if (profit_change_pump > profits_next[new_level]):
                        profits_next[new_level] = profit_change_pump
                        next_decisions[new_level] = 1

                # turb
                new_level = lvl + lvl_delta_turb
                if (new_level < n_energy_levels and previous_decisions[lvl] != 1 and (
                        next_i != 0 or previous_last_action != -1)):
                    profit_change_turb = profits_previous[lvl] + cash_delta_turb
                    if (profit_change_turb > profits_next[new_level]):
                        profits_next[new_level] = profit_change_turb
                        next_decisions[new_level] = -1

                # no action
                if (profits_previous[lvl] > profits_next[lvl]):
                    profits_next[lvl] = profits_previous[lvl]
                    next_decisions[lvl] = 0
            decisions[next_i] = next_decisions
            profits_previous = np.copy(profits_next)

        return profits_previous, decisions