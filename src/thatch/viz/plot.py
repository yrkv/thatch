import numpy as np
import matplotlib.pyplot as plt

from . import util


def plot_single(
    root, key:str,
    window:int=None,
    plot_mean:bool=True,
    plot_all:bool=True,
    plot_IQR:bool=True,
    plot_median:bool=False,
    plot_CI:bool=False,
    logarithmic:bool=False,
    #logarithmic:bool|str='auto', #todo
):
    """
    Detailed plot of a single key/variable within a root.
    """
    data = []
    for rows in root.get_runs():
        data.append([e.get(key) for e in rows])
    arr = np.vstack(data)
    if window is not None and window > 1:
        arr = util.smooth_window(arr, window)
    n, T = arr.shape
    x = np.arange(T)

    plt.figure(figsize=(8, 6), dpi=100)

    plot_fn = plt.semilogy if logarithmic else plt.plot

    if plot_all:
        for run in arr:
            plot_fn(x, run, color='#ebebeb', alpha=1.0, linewidth=0.5, zorder=-100)

    if plot_mean:
        mean = arr.mean(axis=0)
        plot_fn(x, mean, color='blue', alpha=1.0, linewidth=0.5, label='Mean')

    if plot_CI:
        # Normal-approx 95% CI (maybe could be something better)
        ci_low, ci_high = util.normal_CI(arr, z=1.96)
        plt.fill_between(x, ci_low, ci_high, color='blue', alpha=0.15, label='95% CI')

    if plot_median:
        median = np.percentile(arr, 50, axis=0)
        plot_fn(x, median, color='darkgoldenrod', alpha=1.0,
                 linewidth=0.5, label='Median')


    if plot_IQR:
        q25 = np.percentile(arr, 25, axis=0)
        q75 = np.percentile(arr, 75, axis=0)
        plt.fill_between(x, q25, q75, color='orange', linewidth=0,
                         alpha=0.3, label='IQR 25%–75%')



    # todo: automatic ylim to exclude *some* outliers
    #plt.ylim(0, 0.55)
    plt.xlim(0, T)

    plt.grid(True, which='both', axis='both')
    #plt.gca().set_xticks(np.arange(0, T, 100))
    #if logarithmic:
        #pass
        #plt.gca().set_yticks(np.arange(0, plt.ylim()[1], 0.1))
    #else:
        #plt.gca().set_yticks(np.arange(0, plt.ylim()[1], 0.1))

    plt.legend()
    plt.xlabel("Step")
    plt.ylabel(key)
    plt.tight_layout()
    #plt.show()


