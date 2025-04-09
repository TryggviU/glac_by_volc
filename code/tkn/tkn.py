import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm


def intermediate_scatterplot(info_dict):
    fig, ax = plt.subplots()
    hs = []
    for i in range(len(info_dict["labels"])):
        if "facecolors" in info_dict and "edgecolors" in info_dict:
            h = ax.scatter(
                [0], [0],
                facecolor=info_dict["facecolors"][i],
                edgecolor=info_dict["edgecolors"][i],
                marker=info_dict["markers"][i],
                label=info_dict["labels"][i]
            )
            hs.append(h)
        else:
            h = ax.scatter(
                [0], [0],
                color=info_dict["colors"][i],
                marker=info_dict["markers"][i],
                label=info_dict["labels"][i]
            )
            hs.append(h)

    plt.close(fig)
    return hs


def intermediate_scatterplot_cmap(cmap, labels):
    cmap = cm.get_cmap(cmap)

    colors = cmap(np.linspace(0, 1, len(labels)))

    fig, ax = plt.subplots()
    hs = []
    for i in range(len(labels)):
        h = ax.scatter(
            [0], [0],
            color=colors[i],
            marker="o",
            label=labels[i]
        )
        hs.append(h)

    plt.close(fig)
    return hs


def intermediate_lineplot(colors, labels, linestyles=None):
    if not linestyles:
        linestyles = ["-" for c in colors]

    fig, ax = plt.subplots()
    hs = []
    for i in range(len(labels)):
        h, = ax.plot(
            [0, 1], [0, 1],
            color=colors[i],
            linestyle=linestyles[i],
            label=labels[i]
        )
        hs.append(h)

    plt.close(fig)
    return hs


def intermediate_figure(cmap, vmin, vmax, levels):
    # An intermediary figure to get the colormap for the matplotlib figure.
    fig_i, ax_i = pplt.subplots(ncols=1, nrows=1)
    m = ax_i.pcolormesh(
        [[0, 0], [1, 1]], [[0, 1], [0, 1]], [[vmin, vmin], [vmin, vmax]],
        cmap=cmap, vmin=vmin, vmax=vmax, extend='both', levels=levels
    )
    pplt.close(fig_i)

    return m
