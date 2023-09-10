# Hydro power trading

This program was written in the context of a university project by Adrian Buntschu and Vassily Aliseyko.


## Objective

The primary objective was to market the electricity from a pumped hydro storage power plant on the Day-Ahead and Intraday markets. The trading strategy used is the Intrinsic Rolling strategy. This strategy doesn't only make profit from the sold energy (Intrinsic Value) but also from the flexibility of the power plant (Extrinsic Value).

The second objective was to conduct experiments to observe how parameter changes affect the results. The following experiments were conducted:
* Profit at different time horizons (for Day-Ahead prices)
* Profit at different final states
* Profit at different storage capacities
* Profit at different final states and time horizons (for Day-Ahead prices)

All experiments are in the ```experiments.py``` file, you can add some experiments if you want

## Optimization Methods

We employed two optimization methods. The first one is Mixed Integer Linear Programming, which was already coded in Matlab. The second one is Dynamic Programming. We fully implemented the Dynamic Programming algorithm ourselves because we were not allowed to use a library.

## Technology

We needed to use Python as the programming language. However, it was slow for the Dynamic Programming part. Therefore, we utilized a high-performance Python compiler called numba to compile the critical portion of our algorithm. The execution time is 50 times faster with numba than without.

## TODOS
- [x] Translate everything in English
- [x] Remove deprecated code and rename file
- [x] Explain the files and the project
- [ ] File with python package dependencies
- [ ] Make MILP work again
