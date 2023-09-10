import numpy as np

from optimize import IScheduleOptimization
from powerplant import IPumpStoragePlant

from numba import jit


class DynamicProgrammingOptimisation(IScheduleOptimization):
    def __init__(self, ppt: IPumpStoragePlant):
        super().__init__(ppt)
        self.n_energy_levels = int((self.ppt.get_max_level() / self.energy_lvl_step) + 1)
        self.delta_lvl_pump = +self.ppt.get_max_pump_power() * self.ppt.get_pump_efficiency() / self.energy_lvl_step
        self.delta_lvl_turb = -self.ppt.get_max_turb_power() / self.energy_lvl_step

        print("########## init DynamicProgrammingOptimisation ##########")
        print("Number of energy levels: " + str(self.n_energy_levels))
        print("number steps pump: " + str(self.delta_lvl_pump))
        print("number steps turb: " + str(self.delta_lvl_turb))

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
        return build_matrix_optimized(electricity_price, 
                     n_energy_levels, 
                     previous_last_action, 
                     final_energy_level, 
                     mw_to_mwh_factors, 
                     self.ppt.get_max_pump_power(), 
                     self.ppt.get_max_turb_power(), 
                     self.ppt.get_pump_efficiency(), 
                     self.energy_lvl_step)
    

# Remove this line if the function crashes
@jit(nopython=True)
def build_matrix_optimized(electricity_price: list[float],
            n_energy_levels: int,
            previous_last_action: int,
            final_energy_level: int,
            mw_to_mwh_factors: list[float], 
            pump_power: float,
            turb_power: float,
            pump_efficiency: float, 
            energy_lvl_step: float):
    """
    Separate function for numba optimization.
    Because of the optimization, the function may not be as readable as other functions.
    Operations are choosen to be as parallel as possible, and outside of inner loops as much as possible.
    """
    
    profits_previous = np.ones(n_energy_levels) * -np.inf
    profits_previous[final_energy_level] = 0
    profits_next = np.ones(n_energy_levels) * -np.inf
    decisions = np.zeros((len(electricity_price) + 1, n_energy_levels))

    # Iterate backwards, next is more in the passt
    for i in range(len(electricity_price), 0, -1):
        next_i = i - 1
        mw_to_mwh_factor = mw_to_mwh_factors[next_i]

        cash_delta_pump = -pump_power * mw_to_mwh_factor * electricity_price[next_i]
        cash_delta_turb = +turb_power * mw_to_mwh_factor * electricity_price[next_i]

        # Change in energy level when goint from future to past
        lvl_delta_pump = - int(
            pump_power * pump_efficiency * mw_to_mwh_factor / energy_lvl_step)
        lvl_delta_turb = + int(turb_power * mw_to_mwh_factor / energy_lvl_step)

        previous_decisions = decisions[i]
        next_decisions = decisions[next_i]

        profit_next_pump = profits_previous + cash_delta_pump
        profit_next_turb = profits_previous + cash_delta_turb

        if (next_i == 0):
            allowed_to_pump = (previous_decisions != -1) & (previous_last_action != 1)
            allowed_to_turb = (previous_decisions != 1) & (previous_last_action != -1)
        else:
            allowed_to_pump = previous_decisions != -1
            allowed_to_turb = previous_decisions != 1

        for lvl in range(n_energy_levels):
            # pump
            new_level = lvl + lvl_delta_pump
            if (new_level >= 0 and allowed_to_pump[lvl]):
                if (profit_next_pump[lvl] > profits_next[new_level]):
                    profits_next[new_level] = profit_next_pump[lvl]
                    next_decisions[new_level] = 1

            # turb
            new_level = lvl + lvl_delta_turb
            if (new_level < n_energy_levels and allowed_to_turb[lvl]):
                if (profit_next_turb[lvl] > profits_next[new_level]):
                    profits_next[new_level] = profit_next_turb[lvl]
                    next_decisions[new_level] = -1

            # no action
            if (profits_previous[lvl] > profits_next[lvl]):
                profits_next[lvl] = profits_previous[lvl]
                next_decisions[lvl] = 0

        decisions[next_i] = next_decisions
        profits_previous = np.copy(profits_next)

    return profits_previous, decisions