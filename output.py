import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from powerplant import IPumpStoragePlant, PumpStoragePlantTest


def print_optimisation_results(day, market_1, market_2, market_3, market_1_and_2, market_1_2_and_3, price_1):
    plt.figure(1)
    plt.bar(np.linspace(1, 96, 96), market_1[day]["power_exchange"] * -1, label='in/out')
    plt.plot(market_1[day]["energy_level"], 'C1', label='Level')
    plt.plot(price_1[day], 'C2', label='Price DA 12')
    plt.ylabel('Price Eur €')
    plt.xlabel('Quarter hour')
    plt.legend()
    plt.show(block=False)

    fig = plt.figure(2)
    ax = fig.add_subplot(111)
    plt.plot(price_1[day], 'C2', label='Price DA 12')
    plt.legend()
    ax2 = ax.twinx()
    plt.bar(np.linspace(1, 96, 96), market_1[day]["power_exchange"] * -1, label='in/out')
    plt.plot(market_1[day]["energy_level"], 'C1', label='Level')
    plt.legend()
    ax.set_xlabel("Time (15min)")
    ax.set_ylabel(r"Preis Eur/MWh")
    ax2.set_ylabel(r"Volumen MWh")
    plt.show(block=False)

    plt.figure(3)
    plt.bar(np.linspace(1, 96, 96), market_1[day]["cashflow"] * -1, label='Cashflow')
    plt.xlabel('Quarter hour')
    plt.legend()
    plt.show(block=False)

    plt.figure(4)
    plt.plot(np.cumsum(np.sum(pd.DataFrame(market_1[0:40]).cashflow.tolist(), axis=1)), 'C1',
             label='markstufe 1 seperat')
    plt.plot(np.cumsum(np.sum(pd.DataFrame(market_2[0:40]).cashflow.tolist(), axis=1)), 'C2',
             label='markstufe 2 seperat')
    plt.plot(np.cumsum(np.sum(pd.DataFrame(market_3[0:40]).cashflow.tolist(), axis=1)), 'C3',
             label='markstufe 3 seperat')
    plt.plot(np.cumsum(np.sum(pd.DataFrame(market_1[0:40]).cashflow.tolist(), axis=1)
                       + pd.DataFrame(market_1_and_2[0:40])['rolling-gain']
                       + pd.DataFrame(market_1_2_and_3[0:40])['rolling-gain']), 'C4', label='rolling')
    plt.xlabel('Trading day')
    plt.legend()
    plt.show(block=True)


def plot_day_electricity_price(day_index: int, price_1, price_2, price_3):
    plt.figure(0)
    plt.plot(price_1[day_index])
    plt.plot(price_2[day_index])
    plt.plot(price_3[day_index])
    plt.ylabel('Price Eur/MWh')
    plt.xlabel('Quarter hour')
    plt.title("Electricity prices for day %s" % (str(day_index)))
    plt.show(block=False)

def plot_market(market):
    da_daily_cashflow_sum = np.cumsum([np.sum(market.transaction_history_da[d]) for d in market.transaction_history_da])
    id_1_daily_cashflow_sum = np.cumsum([np.sum(market.transaction_history_id_1[d]) for d in market.transaction_history_id_1])
    id_2_daily_cashflow_sum = np.cumsum([np.sum(market.transaction_history_id_2[d]) for d in market.transaction_history_id_2])

    plt.plot(da_daily_cashflow_sum)
    plt.plot(id_1_daily_cashflow_sum)
    plt.plot(id_2_daily_cashflow_sum)
    plt.legend(["From DA", "From DA to ID 1", "From ID 1 to ID 2"])
    plt.xlabel("Time (1 day resolution)")
    plt.ylabel("Cashflows (EUR)")
    plt.title("Cashflow by market levels")
    plt.show()


def plot_powerplant(power_plant):
    fig, ax1 = plt.subplots()
    ax1.plot(power_plant.executed_schedule)
    ax1.plot(np.cumsum(power_plant.executed_schedule * -1))
    ax1.set_xlabel("Time (15 minutes resolution)")
    ax1.set_ylabel("Energy (MWh)")
    ax1.legend(["Executed schedule (added or removed MWh)", "Energy level (MWh)"])
    plt.title("Power plant schedule")

    #Plot prices of power plant on right axis
    ax2 = plt.twinx()
    ax2.plot(power_plant.prices, 'C2')
    ax2.set_ylabel("Price (EUR/MWh)")

    plt.show()

def plot_compare_powerplants(power_plant_1, power_plant_2):
    plt.plot(power_plant_1.executed_schedule)
    plt.plot(power_plant_2.executed_schedule)
    plt.plot(np.cumsum(power_plant_1.executed_schedule * -1))
    plt.plot(np.cumsum(power_plant_2.executed_schedule * -1))
    plt.legend(["Executed schedule (added or removed MWh)", "Executed schedule (added or removed MWh)",
                "Energy level (MWh)", "Energy level (MWh)"])
    plt.xlabel("Time (15 minutes resolution)")
    plt.ylabel("Energy (MWh)")
    plt.title("Power plant schedule")
    plt.show()

def get_real_and_intrinsic_value(ppt_state, market, time_steps_day = 96):
    total_transaction_cashflow_day = []
    total_power_value_day = []

    cashflow_schedule = np.reshape(ppt_state.cashflow_schedule, (-1, time_steps_day))

    for i in range(0, int(len(ppt_state.prices)/time_steps_day)):
        transaction_sum = np.sum(market.transaction_history_da[str(i)] if str(i) in market.transaction_history_da else 0)
        transaction_sum += np.sum(market.transaction_history_id_1[str(i)] if str(i) in market.transaction_history_id_1 else 0)
        transaction_sum += np.sum(market.transaction_history_id_2[str(i)] if str(i) in market.transaction_history_id_2 else 0)
        total_transaction_cashflow_day.append(transaction_sum)
        total_power_value_day.append(np.sum(cashflow_schedule[i]))
    return total_transaction_cashflow_day, total_power_value_day

def plot_real_and_intrinsic_value(ppt_state, market, time_steps_day = 96):
    total_transaction_cashflow_day, total_power_value_day = get_real_and_intrinsic_value(ppt_state, market, time_steps_day)

    plt.plot(total_transaction_cashflow_day)
    plt.plot(total_power_value_day)
    plt.legend(["Total transaction cashflow", "Total traded energy value"])
    plt.xlabel("Time (1 day resolution)")
    plt.ylabel("Cashflow (EUR)")
    plt.title("Real and intrinsic value")
    plt.show()

def plot_real_and_intrinsic_value_cumsum(ppt_state, market, time_steps_day = 96):
    total_transaction_cashflow_day, total_power_value_day = get_real_and_intrinsic_value(ppt_state, market, time_steps_day)

    plt.plot(np.cumsum(total_transaction_cashflow_day))
    plt.plot(np.cumsum(total_power_value_day))
    plt.legend(["Total transactions cashflow sum", "Total traded energy value"])
    plt.xlabel("Time (1 day resolution)")
    plt.ylabel("Cashflow (EUR)")
    plt.title("Real and intrinsic value, cumulated")
    plt.show()

    
def print_stats(ppt_state, market):
    total_intrinsic_value = np.sum(ppt_state.cashflow_schedule)
    print("Total intrinsic value: " + str(total_intrinsic_value))

    total_extrinsic_value = market.rolling_da_id_1 + market.rolling_id_1_id_2 + market.rollging_id_2_da
    print("Total extrinsic value: " + str(total_extrinsic_value))

def plot_total_value_vs_intrinsic_value(total_value, instrinsic_value):
    plt.plot(list(total_value.keys()), list(total_value.values()), label="Total value")
    plt.plot(list(instrinsic_value.keys()), list(instrinsic_value.values()), label="Intrinsic value")
    plt.legend(["Total value", "Intrinsic value"])
    plt.title("Cashflow by parameter value")
    plt.xlabel("Parameter value")
    plt.ylabel("Cashflow")
    plt.show()

def plot_compare_timehorizont_capacity(total_value_7, total_value_14):
    plt.plot(list(total_value_7.keys()), list(total_value_7.values()), label="Total value")
    plt.plot(list(total_value_14.keys()), list(total_value_14.values()), label="Intrinsic value")
    plt.legend(["Total value 7 days", "Total value 14 day"])
    plt.title("Cashflow by capacity")
    plt.xlabel("Capacity in MWh")
    plt.ylabel("Cashflow")
    plt.show()