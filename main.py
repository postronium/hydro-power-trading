from input import get_price_data
from output import plot_total_value_vs_intrinsic_value, plot_compare_timehorizont_capacity
from util import mean_every_i_element_in_list_in_list
from experiments import default_case, cashflow_by_timehorizont, cashflow_by_end_level, cashflow_by_end_level_timehorizont, cashflow_by_capacity


if __name__ == "__main__":
    price_1, price_2, price_3 = get_price_data()

    price_1 = mean_every_i_element_in_list_in_list(price_1, 4)

    #default_case(price_1, price_2, price_3)

    total_value, instrinsic_value = cashflow_by_timehorizont(1, 10, price_1, price_2, price_3)
    #total_value, instrinsic_value = cashflow_by_end_level([0, 100, 200, 300, 400, 500, 600], price_1, price_2, price_3)
    #total_value_7, instrinsic_value_7 = cashflow_by_capacity(7, [100, 300, 600, 1800, 3000, 4200, 5400, 6600, 7800, 9000], price_1, price_2, price_3)
    #total_value_14, instrinsic_value_14 = cashflow_by_capacity(14, [100, 300, 600, 1800, 3000, 4200, 5400, 6600, 7800, 9000], price_1, price_2, price_3)

    #plot_compare_timehorizont_capacity(total_value_7, total_value_14)
    plot_total_value_vs_intrinsic_value(total_value, instrinsic_value)