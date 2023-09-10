import numpy as np


class IPumpStoragePlant:
    def __init__(self):
        self.state: PumpStoragePlantState = PumpStoragePlantState(self)

    def get_max_turb_power(self):
        pass

    def get_max_pump_power(self):
        pass

    def get_max_level(self):
        pass

    def get_pump_efficiency(self):
        pass


class PumpStoragePlantTest(IPumpStoragePlant):
    def __init__(self) -> None:
        super().__init__()
        self.max_turb_power = 25
        self.max_pump_power = 25
        self.max_level = 100
        self.pump_efficiency = 1

    def get_max_turb_power(self):
        return self.max_turb_power

    def get_max_pump_power(self):
        return self.max_pump_power

    def get_max_level(self):
        return self.max_level

    def get_pump_efficiency(self):
        return self.pump_efficiency


class PumpStoragePlant(IPumpStoragePlant):
    """
    Fixed properties of the pump storage plant
    Represent the physical asset
    """

    def __init__(self, max_turb_power, max_pump_power, max_level, pump_efficiency):
        super().__init__()
        self.max_turb_power = max_turb_power  # in MW of electric power
        self.max_pump_power = max_pump_power  # in MW of electric power
        self.max_level = max_level  # in MWh of energy
        self.pump_efficiency = pump_efficiency

    def get_max_turb_power(self):
        return self.max_turb_power

    def get_max_pump_power(self):
        return self.max_pump_power

    def get_max_level(self):
        return self.max_level

    def get_pump_efficiency(self):
        return self.pump_efficiency


class PumpStoragePlantState:

    def __init__(self, ppt):
        self.ppt = ppt
        self.executed_schedule = []
        self.cashflow_schedule = []
        self.prices = []
        self.energy_level = 0
        self.last_action = 0  # 0 = no action, 1 = pump, -1 turb
        pass

    def clear(self):
        self.executed_schedule = []
        self.prices = []
        self.energy_level = 0
        self.last_action = 0

    def execute_schedule(self, prices, day_index, schedule):
        self.cashflow_schedule = np.concatenate((self.cashflow_schedule, prices * schedule))
        self.prices = np.concatenate((self.prices, prices))

        # Multiply negative values with the power plant efficiency
        schedule[schedule < 0] = schedule[schedule < 0] * self.ppt.pump_efficiency

        self.executed_schedule = np.concatenate((self.executed_schedule, schedule))

        # Set last action
        if (schedule[-1] > 0):
            self.last_action = -1
        elif (schedule[-1] < 0):
            self.last_action = 1
        else:
            self.last_action = 0

        self.energy_level = -np.sum(self.executed_schedule)


class PSWLimmern(IPumpStoragePlant):
    """
    Pump Storage Plant in Switzerland
    Source: https://www.axpo.com/ch/de/ueber-uns/energiewissen.detail.html/energiewissen/pumpspeicherwerk-limmern.html
    """

    def __init__(self):
        super().__init__()
        self.max_turb_power = 1000   # in MW (4*250 MW)
        self.max_pump_power = 1000   # in MW (4*250 MW)
        self.max_level = 38670       # in MWh
        self.pump_efficiency = 0.85  # 40/47

    def get_max_turb_power(self):
        return self.max_turb_power

    def get_max_pump_power(self):
        return self.max_pump_power

    def get_max_level(self):
        return self.max_level

    def get_pump_efficiency(self):
        return self.pump_efficiency
    
class Hongrin(IPumpStoragePlant):
    """
    Concret Pump Storage Plant in Switzerland
    Source: http://www.fmhl.ch/PgStd1.asp?m=200
    """
    
    def __init__(self):
        super().__init__()
        self.max_turb_power = 480    # in MW 
        self.max_pump_power = 480    # in MW
        self.max_level = 125121      # in MWh
        self.pump_efficiency = 0.75  # 42/56

    def get_max_turb_power(self):
        return self.max_turb_power

    def get_max_pump_power(self):
        return self.max_pump_power

    def get_max_level(self):
        return self.max_level

    def get_pump_efficiency(self):
        return self.pump_efficiency
    
class PSWGoldisthal(IPumpStoragePlant):
    """
    Concret Pump Storage Plant in Germany
    Source: https://powerplants.vattenfall.com/de/goldisthal/
    """
        
    def __init__(self):
        super().__init__()
        self.max_turb_power = 1060    # in MW 
        self.max_pump_power = 1060    # in MW
        self.max_level = 10698        # in MWh
        self.pump_efficiency = 0.8    # ?

    def get_max_turb_power(self):
        return self.max_turb_power

    def get_max_pump_power(self):
        return self.max_pump_power

    def get_max_level(self):
        return self.max_level

    def get_pump_efficiency(self):
        return self.pump_efficiency