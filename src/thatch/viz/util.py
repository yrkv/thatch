
import numpy as np



def smooth_window(arr, k:int):
    kernel = np.ones(k) / k
    arr = np.array([np.convolve(r, kernel, mode='valid') for r in arr])
    return arr

def smooth_ema(arr, k:float):
    assert False, "todo"

def normal_CI(arr, z=1.96):
    n, _ = arr.shape

    mean = arr.mean(axis=0)
    se = arr.std(axis=0, ddof=1) / np.sqrt(n)

    ci_low = mean - z * se
    ci_high = mean + z * se

    return ci_low, ci_high



