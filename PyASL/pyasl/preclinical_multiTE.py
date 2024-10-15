from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
import os


def T1fit_function(xdata: np.ndarray, a: float, T1: float, A: float):
    return a + np.abs(A * (1 - 2 * np.exp(-xdata / T1)))


def T1fit(xdata: np.ndarray, ydata: np.ndarray):
    x0 = [0, 1.7, np.max(ydata)]
    for _ in range(3):
        param_bounds = [(-np.inf, 0, -np.inf), (np.inf, np.inf, np.inf)]
        x_bef, _ = curve_fit(
            lambda xdata, a, T1, A: T1fit_function(xdata, a, T1, A),
            xdata,
            ydata,
            p0=x0,
            ftol=1e-4,
            xtol=1e-4,
            gtol=1e-4,
            bounds=param_bounds,
        )
        x0 = x_bef

    return x0


def preclinical_multiTE_pipeline(
    data: np.ndarray,
    sel_index: list,
    glo_index: list,
    TE_list: list,
    mask_array=None,
    save_dir=None,
):
    print("Preclinical ASL: start processing...")
    CBF = np.zeros(data.shape[:2])
    sel = data[:, :, np.array(sel_index)]
    glo = data[:, :, np.array(glo_index)]
    TE_list = np.array(TE_list)

    # apply mask
    if mask_array is not None:
        if not isinstance(mask_array, np.ndarray):
            raise ValueError("mask_array is not an ndarray!")
        if mask_array.shape != data.shape[:2]:
            raise ValueError(
                "Shape of mask_array is different from the shape of image!"
            )
        mask_array = mask_array.astype(int)
        sel = sel * mask_array[:, :, np.newaxis]
        glo = glo * mask_array[:, :, np.newaxis]

    A = glo.copy()
    B = sel.copy()

    plot_interval = (data.shape[0] * data.shape[1]) // 200
    counter = 0

    # fit function
    print("Preclinical ASL: fitting T1 function...")
    plt.figure()
    for x in range(data.shape[0]):
        for y in range(data.shape[1]):
            if A[x, y, 0] != 0:
                x0_a = T1fit(TE_list, A[x, y])
                T1_glo = x0_a[1]
                x0_b = T1fit(TE_list, B[x, y])
                T1_sel = x0_b[1]

                if counter % plot_interval == 0:
                    plt.scatter(TE_list, A[x, y])
                    plt.plot(
                        TE_list,
                        np.abs(T1fit_function(TE_list, *x0_a)),
                        "b",
                        linewidth=0.5,
                    )
                    plt.scatter(TE_list, B[x, y])
                    plt.plot(
                        TE_list,
                        np.abs(T1fit_function(TE_list, *x0_b)),
                        "b",
                        linewidth=0.5,
                    )
                counter += 1

                CBF[x, y] = 4980 * T1_glo / 2250 * (1000 / T1_sel - 1000 / T1_glo)

    print("Curve fitting complete!")
    if save_dir is None:
        return CBF
    else:
        np.save(os.path.join(save_dir, "CBF.npy"), CBF)
        plt.savefig(os.path.join(save_dir, "curvefit.png"))
        with open(os.path.join(save_dir, "config.txt"), "w") as f:
            if mask_array is None:
                f.write(
                    f"preclinical_multiTE_pipeline(data, sel_index={sel_index}, glo_index={glo_index}, TE_list={TE_list}, mask_array=None, save_dir='{save_dir}')"
                )
            else:
                f.write(
                    f"preclinical_multiTE_pipeline(data, sel_index={sel_index}, glo_index={glo_index}, TE_list={TE_list}, mask_array, save_dir='{save_dir}')"
                )
        return CBF
