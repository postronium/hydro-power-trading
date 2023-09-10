from input import read_power_plant_informations
from market import Market, PumpStoragePlantIRMarketOptimiserNDays
from optimize_dynamic_fast_fast import DynamicProgrammingOptimisationFastFast
from output import plot_powerplant, plot_market, plot_real_and_intrinsic_value, plot_real_and_intrinsic_value_cumsum, print_stats, plot_total_value_vs_intrinsic_value
from powerplant import IPumpStoragePlant
import time
import numpy as np

def default_case(price_1, price_2, price_3):
    ppt_fast: IPumpStoragePlant = read_power_plant_informations()
    market_fast: Market = Market()
    market_optimiser_fast = PumpStoragePlantIRMarketOptimiserNDays(ppt_fast, market_fast, DynamicProgrammingOptimisationFastFast(ppt_fast))

    market_optimiser_fast.set_prices(price_1, price_2, price_3)
    start = time.time()
    market_optimiser_fast.optimise()
    end = time.time()
    print("Execution time fast: %s seconds" % (str(end - start)))

    print_stats(ppt_fast.state, market_fast)
    plot_powerplant(ppt_fast.state)
    #plot_real_and_intrinsic_value(ppt_fast.state, market_fast)
    plot_real_and_intrinsic_value_cumsum(ppt_fast.state, market_fast)
    plot_market(market_fast)

def cashflow_by_timehorizont(min_timehorizont, max_timehorizont, price_1, price_2, price_3):
    """
    Calculate the cashflow for all timehorizonts.
    """
    extrinsic_value = {}
    instrinsic_value = {}
    for timehorizont in range(min_timehorizont, max_timehorizont + 1):
        print("##################### %s days #####################" % str(timehorizont))
        ppt_fast: IPumpStoragePlant = read_power_plant_informations()
        market_fast: Market = Market()
        market_optimiser_fast = PumpStoragePlantIRMarketOptimiserNDays(ppt_fast, market_fast, DynamicProgrammingOptimisationFastFast(ppt_fast))
        market_optimiser_fast.timehorizon = timehorizont

        market_optimiser_fast.set_prices(price_1, price_2, price_3)
        start = time.time()
        market_optimiser_fast.optimise()
        end = time.time()
        print("Execution time fast: %s seconds" % (str(end - start)))

        instrinsic_value[str(timehorizont)] = np.sum(ppt_fast.state.cashflow_schedule)
        extrinsic_value[str(timehorizont)] = market_fast.rolling_da_id_1 + market_fast.rolling_id_1_id_2 + market_fast.rollging_id_2_da

        print("Total value:     %s" % str(extrinsic_value[str(timehorizont)]))
        print("Intrinsic value: %s" % str(instrinsic_value[str(timehorizont)]))
    return extrinsic_value, instrinsic_value

def cashflow_by_end_level(end_levels, price_1, price_2, price_3, timehorizon = 7):
    """
    Calculate the cashflow for all timehorizonts.
    """
    total_value = {}
    instrinsic_value = {}
    for lvl in end_levels:
        print("##################### %s MWh #####################" % str(lvl))
        ppt_fast: IPumpStoragePlant = read_power_plant_informations()
        market_fast: Market = Market()
        market_optimiser_fast = PumpStoragePlantIRMarketOptimiserNDays(ppt_fast, market_fast, DynamicProgrammingOptimisationFastFast(ppt_fast))
        market_optimiser_fast.end_level = lvl
        market_optimiser_fast.timehorizon = timehorizon

        market_optimiser_fast.set_prices(price_1, price_2, price_3)
        start = time.time()
        market_optimiser_fast.optimise()
        end = time.time()
        print("Execution time fast: %s seconds" % (str(end - start)))

        instrinsic_value[str(lvl)] = np.sum(ppt_fast.state.cashflow_schedule)
        total_value[str(lvl)] = market_fast.rolling_da_id_1 + market_fast.rolling_id_1_id_2 + market_fast.rollging_id_2_da

        #print("Total value:     " % str(total_value[str(lvl)]))
        #print("Intrinsic value: %s" % str(instrinsic_value[str(lvl)]))
    return total_value, instrinsic_value

def cashflow_by_capacity(timehorizont, capacities, price_1, price_2, price_3):
    """
    Calculate the cashflow for all timehorizonts.
    """

    total_value = {}
    instrinsic_value = {}

    for capacity in capacities:

        print("##################### %s MWh Capacity #####################" % str(capacity))
        ppt_fast: IPumpStoragePlant = read_power_plant_informations()
        ppt_fast.max_level = capacity
        market_fast: Market = Market()
        market_optimiser_fast = PumpStoragePlantIRMarketOptimiserNDays(ppt_fast, market_fast, DynamicProgrammingOptimisationFastFast(ppt_fast))
        market_optimiser_fast.timehorizon = timehorizont

        market_optimiser_fast.set_prices(price_1, price_2, price_3)
        start = time.time()
        market_optimiser_fast.optimise()
        end = time.time()
        print("Execution time fast: %s seconds" % (str(end - start)))

        instrinsic_value[str(capacity)] = np.sum(ppt_fast.state.cashflow_schedule)
        total_value[str(capacity)] = market_fast.rolling_da_id_1 + market_fast.rolling_id_1_id_2 + market_fast.rollging_id_2_da

        print("Total value:     %s" % str(total_value[str(capacity)]))
        print("Intrinsic value: %s" % str(instrinsic_value[str(capacity)]))

        #print_stats(ppt_fast.state, market_fast)
        #plot_powerplant(ppt_fast.state)
        #plot_real_and_intrinsic_value(ppt_fast.state, market_fast)
        #plot_real_and_intrinsic_value_cumsum(ppt_fast.state, market_fast)
        #plot_market(market_fast)

    return total_value, instrinsic_value

def cashflow_by_end_level_timehorizont(end_levels, timehorizonts, price_1, price_2, price_3):
    """
    Calculate the cashflow for all timehorizonts.
    """
    total_value = {}
    instrinsic_value = {}
    for h in timehorizonts:
        print("##################### %s days #####################" % str(h))
        total_value_lvl, instrinsic_value_lvl = cashflow_by_end_level(end_levels, price_1, price_2, price_3, h)

        total_value[str(h)] = total_value_lvl
        instrinsic_value[str(h)] = instrinsic_value_lvl

        print("Total value:     %s" % str(total_value[str(h)]))
        print("Intrinsic value: %s" % str(instrinsic_value[str(h)]))
    return total_value, instrinsic_value