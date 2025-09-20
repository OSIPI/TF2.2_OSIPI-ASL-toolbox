import numpy as np
from scipy.optimize import curve_fit

def T1fit_function(xdata: np.ndarray, a: float, T1: float, A: float):
    return a + np.abs(A * (1 - 2 * np.exp(-xdata / T1)))

def T1fit(xdata: np.ndarray, ydata: np.ndarray):
    x0 = [0, 1.7, np.max(ydata)]
    for _ in range(3):
        param_bounds = [(-np.inf, 0, -np.inf), (np.inf, np.inf, np.inf)]
        x_bef, _ = curve_fit(
            lambda xdata, a, T1, A: T1fit_function(xdata, a, T1, A),
            xdata, ydata, p0=x0,
            ftol=1e-4, xtol=1e-4, gtol=1e-4, bounds=param_bounds,
        )
        x0 = x_bef
    return x0