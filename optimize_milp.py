import numpy as np
from scipy.optimize import LinearConstraint, milp, Bounds

from optimize import IScheduleOptimization
from powerplant import IPumpStoragePlant


class MILPScheduleOptimization(IScheduleOptimization):
    """
    This don't work anymore, use optimize_dynamic instead. TODO need to be fixed
    Optimisation of the schedule of the pump storage plant using a Mixed Integer Linear Programming.
    """

    def __init__(self, ppt: IPumpStoragePlant):
        self.ppt = ppt

    def calculate_optimal_schedule(self,
                                   electricity_price: list[float],
                                   initial_energy_level: float,
                                   previous_last_action: int,
                                   final_energy_level: float,
                                   mw_to_mwh_factors: list[float]):

        time_step_count = len(electricity_price)
        var_count_per_time_step = 5
        total_variable_count = time_step_count * var_count_per_time_step

        # Coefficents, represent value to minimize
        c = np.array([[-price, price, 0, 0, 0] for price in electricity_price])
        c = np.reshape(c, (total_variable_count, 1)).flatten()

        # 0 means continus, 1 means integer
        integrality = np.array([[0, 0, 1, 1, 0] for i in range(time_step_count)]).flatten()

        # Lower and upper bound are always the same
        lower_bound = np.zeros(total_variable_count)
        upper_bound = np.array([[self.ppt.max_turb_power, self.ppt.max_pump_power, 1, 1, self.ppt.max_level] for i in
                                range(time_step_count)])
        upper_bound = np.reshape(upper_bound, (total_variable_count, 1)).flatten()

        # Constraints initial energy level
        constraints = (
            self.get_constraint_initial_energy_level(initial_energy_level, total_variable_count),
            self.get_constraint_final_energy_level(final_energy_level, total_variable_count),
            self.get_constraint_energy_level(time_step_count, var_count_per_time_step),
            self.get_constraint_energy_level_end(time_step_count, var_count_per_time_step, mw_to_mwh_factors),
            self.get_constraint_turb_on_off(time_step_count, var_count_per_time_step, mw_to_mwh_factors),
            self.get_constraint_pump_on_off(time_step_count, var_count_per_time_step, mw_to_mwh_factors),
            self.get_constraint_pump_turb_same_time(time_step_count, var_count_per_time_step),
            self.get_constraint_turb_pump_pause(time_step_count, var_count_per_time_step),
            self.get_constraint_pump_turb_pause(time_step_count, var_count_per_time_step),
        )

        # Solve
        res = milp(c, constraints=constraints, integrality=integrality, bounds=Bounds(lb=lower_bound, ub=upper_bound))

        total_cashflow = res.fun
        decisions = np.reshape(res.x, (time_step_count, var_count_per_time_step))

        return {
            'total_cashflow': total_cashflow,
            'sell_mwh': decisions[:, 0],
            'buy_mwh': decisions[:, 1],
            'hourly_energy_level': decisions[:, 4]
        }

    def get_constraint_initial_energy_level(self, initial_energy_level, total_variable_count):
        var_coefficients = np.zeros(total_variable_count)
        var_coefficients[4] = 1
        return LinearConstraint(var_coefficients, initial_energy_level, initial_energy_level)

    def get_constraint_final_energy_level(self, end_energy_level, total_variable_count):
        var_coefficients = np.zeros(total_variable_count)
        var_coefficients[-1] = 1

        # TODO find a solution to this problem
        return LinearConstraint(var_coefficients, end_energy_level, end_energy_level + 10 * 0.25)

    def get_constraint_energy_level(self, time_step_count, var_count_per_time_step):
        var_count = time_step_count * var_count_per_time_step
        coefficient_model = [
            -1,  # turb before
            self.ppt.get_pump_efficiency(),  # pump before
            0,  # turb on before
            0,  # pump on before
            1,  # level before
            0,  # turb now
            0,  # pump now
            0,  # turb on now
            0,  # pump on now
            -1  # level now
        ]
        var_coefficients = np.zeros((time_step_count - 1, var_count))
        for i in range(0, time_step_count - 1):
            var_coefficients[i, i * var_count_per_time_step:(i + 2) * var_count_per_time_step] = coefficient_model

        return LinearConstraint(var_coefficients, np.zeros(time_step_count - 1), np.zeros(time_step_count - 1))

    def get_constraint_energy_level_end(self, time_step_count, var_count_per_time_step, mw_to_mwh_factors):
        """Prevents the pump storage plant to exceed the maximum energy level, or to go below 0 energy level,
                during the last time step."""
        var_count = time_step_count * var_count_per_time_step
        coefficient_model = [
            0,  # turb
            0,  # pump
            -self.ppt.get_max_turb_power() * mw_to_mwh_factors[-1],  # turb on
            self.ppt.get_max_pump_power() * mw_to_mwh_factors[-1],  # pump on
            1  # level
        ]

        var_coefficients = np.zeros((1, var_count))
        var_coefficients[0, (time_step_count - 1) * var_count_per_time_step:var_count] = coefficient_model

        energy_level_constraint = LinearConstraint(var_coefficients, 0, self.ppt.get_max_level())
        return energy_level_constraint

    def get_constraint_turb_on_off(self, time_step_count, var_count_per_time_step, mw_to_mwh_factors):
        var_count = time_step_count * var_count_per_time_step

        var_coefficients = np.zeros((time_step_count, var_count))
        for i in range(0, time_step_count):
            coefficient_model = [
                -1,  # turb
                0,  # pump
                self.ppt.get_max_turb_power() * mw_to_mwh_factors[i],  # turb on
                0,  # pump on
                0  # level
            ]
            var_coefficients[i, i * var_count_per_time_step:(i + 1) * var_count_per_time_step] = coefficient_model

        return LinearConstraint(var_coefficients, np.zeros(time_step_count), np.zeros(time_step_count))

    def get_constraint_pump_on_off(self, time_step_count, var_count_per_time_step, mw_to_mwh_factors):
        var_count = time_step_count * var_count_per_time_step

        var_coefficients = np.zeros((time_step_count, var_count))
        for i in range(0, time_step_count):
            coefficient_model = [
                0,  # turb
                -1,  # pump
                0,  # turb on
                self.ppt.get_max_pump_power() * mw_to_mwh_factors[i],  # pump on
                0  # level
            ]
            var_coefficients[i, i * var_count_per_time_step:(i + 1) * var_count_per_time_step] = coefficient_model

        return LinearConstraint(var_coefficients, np.zeros(time_step_count), np.zeros(time_step_count))

    def get_constraint_pump_turb_same_time(self, time_step_count, var_count_per_time_step):
        """
        Forbid to have the pump on and the turbine on at the same time.
        No hydrolic short circuit allowed.
        """
        var_count = time_step_count * var_count_per_time_step
        coefficient_model = [
            0,  # turb
            0,  # pump
            1,  # turb on
            1,  # pump on
            0,  # level
        ]

        var_coefficients = np.zeros((time_step_count, var_count))
        for i in range(0, time_step_count):
            var_coefficients[i, i * var_count_per_time_step:(i + 1) * var_count_per_time_step] = coefficient_model

        return LinearConstraint(var_coefficients, np.zeros(time_step_count), np.ones(time_step_count))

    def get_constraint_turb_pump_pause(self, time_step_count, var_count_per_time_step):
        """Force a pause between pump on and turb off"""
        var_count = time_step_count * var_count_per_time_step
        coefficient_model = [
            0,  # turb before
            0,  # pump before
            1,  # turb on before
            0,  # pump on before
            0,  # level before

            0,  # turb now
            0,  # pump now
            0,  # turb on now
            1,  # pump on now
            0,  # level now
        ]

        var_coefficients = np.zeros((time_step_count - 1, var_count))
        for i in range(0, time_step_count - 1):
            var_coefficients[i, i * var_count_per_time_step:(i + 2) * var_count_per_time_step] = coefficient_model

        return LinearConstraint(var_coefficients, np.zeros(time_step_count - 1), np.ones(time_step_count - 1))

    def get_constraint_pump_turb_pause(self, time_step_count, var_count_per_time_step):
        """Force a pause between turb on and pump off"""
        var_count = time_step_count * var_count_per_time_step
        coefficient_model = [
            0,  # turb before
            0,  # pump before
            0,  # turb on before
            1,  # pump on before
            0,  # level before

            0,  # turb now
            0,  # pump now
            1,  # turb on now
            0,  # pump on now
            0,  # level now
        ]

        var_coefficients = np.zeros((time_step_count - 1, var_count))
        for i in range(0, time_step_count - 1):
            var_coefficients[i, i * var_count_per_time_step:(i + 2) * var_count_per_time_step] = coefficient_model

        return LinearConstraint(var_coefficients, np.zeros(time_step_count - 1), np.ones(time_step_count - 1))
