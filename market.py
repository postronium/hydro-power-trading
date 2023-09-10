import numpy as np

from optimize import IScheduleOptimization
from powerplant import IPumpStoragePlant


class Market:

    def __init__(self):
        self.rolling_da_id_1 = 0
        self.rolling_id_1_id_2 = 0
        self.rollging_id_2_da = 0

        self.transaction_history_da = {}
        self.transaction_history_id_1 = {}
        self.transaction_history_id_2 = {}

        pass

    def calculate_cashflow(self, prices, sell):
        """
        Parameters
        ----------
        prices : np.array
            The prices for each time step.
        sell : np.array
            The quantities of electricic energy to sell for each time step in MWh.
            When electricity is bought, the quantity is negative.

        Returns
        -------
        The cashflow for each periode.
        """
        return prices * sell

    def do_transactions_da(self, prices, sell, day):
        """
        Parameters
        ----------
        prices : np.array
            Price of electric energy in EUR/MWh for each timestep.
        sell : np.array
            The quantities of electricic energy to sell for each time step in MWh.
            Sell is positif when electricity is sold and negative when electricity is bought.
        day : int
            The day index.
        """
        cashflow = self.calculate_cashflow(prices, sell)
        self.rollging_id_2_da += np.sum(cashflow)
        self.transaction_history_da[str(day)] = cashflow
        return cashflow
    
    def do_transactions_id(self, prices, sell, day, id_type):
        """
        Parameters
        ----------
        prices : np.array
            Price of electric energy in EUR/MWh for each timestep.
        sell : np.array
            The quantities of electricic energy to sell for each time step in MWh.
            Sell is positif when electricity is sold and negative when electricity is bought.
        day : int
            The day index.
        id_type : int
            1 or 2
        """
        cashflow = self.calculate_cashflow(prices, sell)
        if id_type == 1:
            self.rolling_da_id_1 += np.sum(cashflow)
            self.transaction_history_id_1[str(day)] = cashflow
        elif id_type == 2:
            self.rolling_id_1_id_2 += np.sum(cashflow)
            self.transaction_history_id_2[str(day)] = cashflow
        return cashflow


class PumpStoragePlantIRMarketOptimiserNDays:
    """
    Does the full optimisation of a pump storage plant for all market levels.
    Uses 3 Market level:
        Day ahead with n days ahead
        Intraday 1
        Intraday 2 which are intraday prices known after the intraday 1 prices
    Use the strategy of Intrinsic rolling.
    """

    def __init__(self, ppt: IPumpStoragePlant, market, optimiser: IScheduleOptimization):
        """
        Parameters
        ----------
        ppt : IPumpStoragePlant
            The pump storage plant to optimise
        market : Market
            The market for transactions and power exchange
        optimiser : IScheduleOptimization
            The optimiser to use for the optimisation of the schedule for a given price timeserie
        """
        self.ppt = ppt
        self.optimiser = optimiser
        self.market = market

        # price resolutions
        self.day_ahead_time_step_duration = 1  # 1 hour
        self.intraday_1_time_step_duration = 1 / 4  # 15 minutes
        self.intraday_2_time_step_duration = 1 / 4  # 15 minutes
        self.hour_in_day = 24

        # Amount of days where we can predict the prices
        self.timehorizon = 7

        # Number of day ahead prices in one day
        self.n_step_da_day = int(self.hour_in_day / self.day_ahead_time_step_duration)
        # Number of intraday prices in one day
        self.n_step_id_day = int(self.hour_in_day / self.intraday_2_time_step_duration)

        # end level of optimisation periodes (after self.timehorizon days)
        self.end_level = ppt.state.energy_level

    def set_prices(self, day_ahead, intraday_1, intraday_2):
        self.day_ahead_prices = day_ahead.flatten()
        self.intraday_1_prices = intraday_1.flatten()
        self.intraday_2_prices = intraday_2.flatten()

    def optimise(self):
        """
        Optimise the pump storage plant based on the prices given previously with the set_prices function
        Fills the market object and the power plant state object with data like
            transactions, power exchange and fill level
        Side effect: the power plant state is cleared and changes
        """

        self.ppt.state.clear()

        number_of_days = int(len(self.day_ahead_prices) / self.n_step_da_day)

        last_optimal_schedule = []

        for i in range(0, number_of_days):
            #print("Calculate day %i / %i" % (i, number_of_days))
            # Optimal first transactions of day
            da_prices, step_durations = self.get_da_only_prices(i, self.timehorizon)
            last_optimal_schedule = self.calculate_schedule_da(da_prices, step_durations, i)

            # Optimal Intraday 1 schedule
            id_1_price, id_1_step_duration = self.get_da_and_id_prices(self.intraday_1_prices,
                                                                       self.intraday_1_time_step_duration,
                                                                       i, self.timehorizon)
            # split da ahead periodes to be compatible with intraday 1
            last_optimal_schedule = self.split_first_day_periode(last_optimal_schedule)
            last_optimal_schedule = self.calculate_schedule_id(id_1_price, id_1_step_duration, last_optimal_schedule, i, 1)

            id_2_price, id_2_step_duration = self.get_da_and_id_prices(self.intraday_2_prices,
                                                                       self.intraday_2_time_step_duration,
                                                                       i, self.timehorizon)
            last_optimal_schedule = self.calculate_schedule_id(id_2_price, id_2_step_duration, last_optimal_schedule, i, 2)

            self.ppt.state.execute_schedule(id_2_price[0:self.n_step_id_day], i, last_optimal_schedule[0:self.n_step_id_day])

        print("Done %i days calculated" % (number_of_days))

    def calculate_schedule_da(self, prices, step_duration, day_id: int):
        opt_results_da = self.optimiser.calculate_optimal_schedule(prices, self.ppt.state.energy_level,
                                                                   self.ppt.state.last_action, self.end_level,
                                                                   step_duration)
        best_schedule_da_sell = opt_results_da['sell_mwh'] - opt_results_da['buy_mwh']

        self.market.do_transactions_da(prices[0:self.n_step_da_day], best_schedule_da_sell[0:self.n_step_da_day], day_id)
        return best_schedule_da_sell

    def calculate_schedule_id(self, prices, step_duration, last_optimal_schedule, day_id: int, id_type):
        opt_results_id_1 = self.optimiser.calculate_optimal_schedule(prices, self.ppt.state.energy_level,
                                                                     self.ppt.state.last_action, self.end_level,
                                                                     step_duration)
        best_schedule_id_1_sell = opt_results_id_1['sell_mwh'] - opt_results_id_1['buy_mwh']

        # Value if rolling
        delta_transactions = best_schedule_id_1_sell - last_optimal_schedule
        id_rolling_cashflow = self.market.calculate_cashflow(prices[0:self.n_step_id_day], delta_transactions[0:self.n_step_id_day])
        if (np.sum(id_rolling_cashflow) > 0):
            self.market.do_transactions_id(prices[0:self.n_step_id_day], delta_transactions[0:self.n_step_id_day], day_id, id_type)

            # Update best schedule
            last_optimal_schedule = best_schedule_id_1_sell
        else:
            self.market.do_transactions_id(prices[0:self.n_step_id_day], np.zeros(self.n_step_id_day), day_id, id_type)
        return last_optimal_schedule

    def split_first_day_periode(self, prices):
        factor = int(self.day_ahead_time_step_duration / self.intraday_1_time_step_duration)
        da_periodes_in_day = int(self.hour_in_day / self.day_ahead_time_step_duration)

        new_prices = []
        for i in range(0, da_periodes_in_day):
            for j in range(0, factor):
                new_prices.append(prices[i] / factor)

        return np.concatenate((new_prices, prices[da_periodes_in_day:]))

    def do_market_transactions(self, prices, buy, sell):
        """
        Do the market transactions for the given prices and quantities.

        Parameters
        ----------
        prices : np.array
            The prices for each time step.
        buy : np.array
            The quantities of electricic energy to buy for each time step in MWh.
        sell : np.array
            The quantities of electricic energy to sell for each time step in MWh.

        Returns
        -------
        The cashflow for each periode.
        """
        cashflow = prices * (sell - buy)
        return cashflow

    def get_da_and_id_prices(self, id_prices, id_step_duration, day_idx, timeserie_length):
        """
        Prepare the timeseries for the timeserie_length following days starting from the given day.
        The first day of the timeserie contains the intraday 1 prices.

        Parameters
        ----------
        id_prices :
            Prices known couple of hours ahead.
        id_step_duration :
            Timelaps between two intraday prices.
        day_idx : int
            The index of the day from which to get the prices.
        timeserie_length : int
            The amount of days to get prices for.

        Returns
        -------
        dict that contains an array of ID and DA prices and the step duration
        """

        # process day ahead timeserie indices
        n_step_da = int(self.hour_in_day / self.day_ahead_time_step_duration)

        day_ahead_to = int((day_idx + timeserie_length) * n_step_da)
        if (day_ahead_to > len(self.day_ahead_prices) - 1):
            day_ahead_to = len(self.day_ahead_prices)

        day_ahead_from = int((day_idx + 1) * n_step_da)
        if (day_ahead_from > len(self.day_ahead_prices) - 1):
            day_ahead_from = len(self.day_ahead_prices)

        # process intraday timeserie indices
        n_step_id = int(self.hour_in_day / id_step_duration)

        id_from = int(day_idx * n_step_id)
        id_to = int((day_idx + 1) * n_step_id)

        price = np.concatenate((id_prices[id_from:id_to], (self.day_ahead_prices[day_ahead_from:day_ahead_to])))
        step_duration = np.concatenate((np.ones(id_to - id_from) * id_step_duration,
                                        np.ones(day_ahead_to - day_ahead_from) * self.day_ahead_time_step_duration))
        return price, step_duration

    def get_da_only_prices(self, day_idx, timeserie_length):
        """
        Prepare the day ahead timeseries from the given day up to the following timeserie_length days, when available.

        Parameters
        ----------
        day_idx : int
            The index of the day from which to get the prices.
        timeserie_length : int
            The amount of days to get prices for.

        Returns
        -------
        day ahead prices and step duration
        """

        n_step_da = int(self.hour_in_day / self.day_ahead_time_step_duration)

        day_ahead_to = int((day_idx + timeserie_length) * n_step_da)
        if (day_ahead_to > len(self.day_ahead_prices)):
            day_ahead_to = len(self.day_ahead_prices)

        day_ahead_from = int(day_idx * n_step_da)
        if (day_ahead_from > len(self.day_ahead_prices)):
            day_ahead_from = len(self.day_ahead_prices)

        prices = self.day_ahead_prices[day_ahead_from:day_ahead_to]
        step_durations = np.ones(day_ahead_to - day_ahead_from) * self.day_ahead_time_step_duration
        return prices, step_durations


class PumpStoragePlantIRMarketOptimiserOneDay:
    """
    Does the full optimisation of a pump storage plant for all market levels.
    Use the strategy of Intrinsic rolling.
    """

    def __init__(self, ppt: IPumpStoragePlant, optimiser: IScheduleOptimization):
        """
        Parameters
        ----------
        ppt : IPumpStoragePlant
            The pump storage plant to optimise
        optimiser : IScheduleOptimization
            The optimiser to use for the optimisation of the schedule for a given price timeserie
        """
        self.ppt = ppt
        self.optimiser = optimiser

    # For all days in one market level, calculate all optimal decisions
    def calculate_market_activity(self, daily_price_list):
        days = []

        for hourly_price in daily_price_list:
            opt_results = self.optimiser.calculate_optimal_schedule(hourly_price,
                                                                    self.ppt.max_level / 2,
                                                                    0,
                                                                    self.ppt.max_level / 2,
                                                                    np.ones_like(hourly_price) * 0.25)

            print("day %s after milp" % (len(days)))

            # Positive values mean that the plant is selling power
            power_exchange = np.array(opt_results['hourly_selling'] - opt_results['hourly_buying'])
            energy_level = np.array(opt_results['hourly_energy_level'])
            hourly_cashflow = np.array(power_exchange * np.array(hourly_price))

            days.append({'power_exchange': power_exchange, 'energy_level': energy_level, 'cashflow': hourly_cashflow})
            print("day %s after append" % (len(days)))

        return days

    def optimise(self, prices_market_1, prices_market_2, prices_market_3):
        # Initial decisions from initial prices
        market_1 = self.calculate_market_activity(prices_market_1)

        # next decisions from next prices
        market_2 = self.calculate_market_activity(prices_market_2)

        # Rolling from market 1 to market 2
        market_1_and_2 = []
        for day in zip(market_1, market_2, prices_market_2):
            power_exchange_difference = day[1]['power_exchange'] - day[0]['power_exchange']
            cashflow_difference = day[1]['cashflow'] - day[0]['cashflow']
            cashflow_change = power_exchange_difference.dot(np.array(day[2]).T)

            # Do we have a gain from rolling?
            if (cashflow_change > 0):  # yes, we roll
                market_1_and_2.append({
                    'power_exchange': day[0]['power_exchange'] + power_exchange_difference,
                    'energy_level': day[1]['energy_level'],
                    'cashflow': day[0]['cashflow'] + cashflow_difference,
                    'rolling-gain': cashflow_change
                })
            else:  # no, just copy market 1
                market_1_and_2.append({
                    'power_exchange': day[0]['power_exchange'],
                    'energy_level': day[0]['energy_level'],
                    'cashflow': day[0]['cashflow'],
                    'rolling-gain': 0
                })

        # next decisions from next prices
        market_3 = self.calculate_market_activity(prices_market_3)

        # Rolling from market (1 and 2 rolled or not) to market 3
        market_1_2_and_3 = []
        for day in zip(market_1_and_2, market_3, prices_market_3):
            power_exchange_difference = day[1]['power_exchange'] - day[0]['power_exchange']
            cashflow_difference = day[1]['cashflow'] - day[0]['cashflow']

            cashflow_change = power_exchange_difference.dot(np.array(day[2]).T)

            # Do we have a gain from rolling?
            if (cashflow_change > 0):  # yes, we roll
                market_1_2_and_3.append({
                    'power_exchange': day[0]['power_exchange'] + power_exchange_difference,
                    'energy_level': day[1]['energy_level'],
                    'cashflow': day[0]['cashflow'] + cashflow_difference,
                    'rolling-gain': cashflow_change
                })
            else:  # no, cancel rolling
                market_1_2_and_3.append({
                    'power_exchange': day[0]['power_exchange'],
                    'energy_level': day[0]['energy_level'],
                    'cashflow': day[0]['cashflow'],
                    'rolling-gain': 0
                })

        return market_1, market_2, market_3, market_1_and_2, market_1_2_and_3

