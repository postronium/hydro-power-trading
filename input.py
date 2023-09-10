import pandas as pd
import scipy as sp

from powerplant import PumpStoragePlant


def get_price_data():
    # Import
    price_data = sp.io.loadmat('price.mat')

    # Get data
    price_data = price_data['Price'][0][0]
    market_lvl_1 = price_data[0]
    market_lvl_2 = price_data[1]
    market_lvl_3 = price_data[2]
    return (market_lvl_1, market_lvl_2, market_lvl_3)


def read_power_plant_informations():
    storage_data = pd.ExcelFile("power-plant-informations.xlsx")

    dfs = {sheet_name: storage_data.parse(sheet_name)
           for sheet_name in storage_data.sheet_names}
    # Storage
    storage_level_max = dfs["Tabelle1"].values[7, 2]
    storage_level_anfang = 0.5 * storage_level_max

    # Turbine and Pump
    storage_turb_max_el = dfs["Tabelle1"].values[1, 2]
    storage_turb_min_el = dfs["Tabelle1"].values[2, 2]
    storage_pump_max_el = dfs["Tabelle1"].values[3, 2]
    storage_pump_min_el = dfs["Tabelle1"].values[4, 2]
    storage_pump_eta = dfs["Tabelle1"].values[6, 2]

    pump_efficiency = 0.75

    return PumpStoragePlant(storage_turb_max_el, storage_pump_max_el, storage_level_max, pump_efficiency)
