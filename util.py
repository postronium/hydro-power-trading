# mean every i th element in the list
import numpy as np


def mean_every_i_element_in_list(list, i):
    return np.array([np.mean(list[j:j + i]) for j in range(0, len(list), i)])


# mean every i th element in the list in the list
def mean_every_i_element_in_list_in_list(list, i):
    return np.array([mean_every_i_element_in_list(list[j], i) for j in range(0, len(list))])
