import numpy as np
import matplotlib.pyplot as plt
import os

def get_plot_array(data: np.ndarray, winf: list):
    scale = data.shape
    target = np.zeros((winf[0] * scale[0], winf[1] * scale[1]))
    for ni in range(scale[2]):
        pi = np.floor(ni / winf[1]).astype(int)
        qi = ni - pi * winf[1]
        target[
            pi * scale[0] : (pi + 1) * scale[0], qi * scale[1] : (qi + 1) * scale[1]
        ] = data[:, :, ni]
    return target

def plot_save_fig(data: np.ndarray, fig_title: str, fig_path: str, range=None):
    os.makedirs(os.path.dirname(fig_path) or ".", exist_ok=True)
    plt.figure()
    if not range:
        plt.imshow(data)
    else:
        plt.imshow(data, vmin=range[0], vmax=range[1])
    plt.title(fig_title)
    plt.colorbar()
    plt.savefig(fig_path)
    plt.close()