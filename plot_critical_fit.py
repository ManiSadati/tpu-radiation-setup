import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

font_size = 14

df = pd.read_csv("./analysis_data/critical_fit.csv", index_col="Benchmark")


def plot_clustered_stacked(dfall, labels=None, H="/", **kwargs):
    """Given a list of dataframes, with identical columns and index, create a clustered stacked bar plot.
labels is a list of the names of the dataframe, used for the legend
title is a string for the title of the plot
H is the hatch used for identification of the different dataframe"""

    n_df = len(dfall)
    n_col = len(dfall[0].columns)
    n_ind = len(dfall[0].index)
    axe = plt.subplot(111)

    for df in dfall : # for each data frame
        axe = df.plot(kind="bar",
                      linewidth=0,
                      stacked=True,
                      log=True,
                      ax=axe,
                      legend=False,
                      grid=False,
                      **kwargs)  # make bar plots
        xlbls = ['\nTPU1\nTPU2'] * n_ind
        axe.set_xticklabels(xlbls, rotation = 90)

    h,l = axe.get_legend_handles_labels() # get the handles we want to modify

    for i in range(0, n_df * n_col, n_col): # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i+n_col]):
            for rect in pa.patches: # for each index
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_width(1 / float(n_df + 1))
                #rect.set_hatch(H * int(i / n_col))
                #rect.set_alpha(0.99)
            rounded_labels = [ round(elem, 2) for elem in pa.datavalues ]
            axe.bar_label(pa, labels=rounded_labels, rotation=90, padding=2)

    sec = axe.secondary_xaxis(location=0)
    sec.set_xticks((np.arange(0, 2 * n_ind, 2) + 1 / float(n_df + 1)) / 2., labels=df.index, rotation=45, ha='right', fontsize=font_size-4)
    sec.tick_params(axis='x', which='major', pad=35)
    sec.tick_params('x', length=0)

    # Add invisible data to add another legend
    n=[]
    for i in range(n_df):
        n.append(axe.bar(0, 0, color="lightgrey", hatch=H * i, alpha=0.99))

    l1 = axe.legend(h[:n_col], l[:n_col], loc="upper left")
    #if labels is not None:
    #    l2 = plt.legend(n, labels, loc="upper center")

    axe.add_artist(l1)
    return axe


df1 = df[df["TPU"] == 1]
stacked_df1 = df1.pivot_table(index='Benchmark', columns='Type', values='FIT_Rate')

df2 = df[df["TPU"] == 2]
stacked_df2 = df2.pivot_table(index='Benchmark', columns='Type', values='FIT_Rate')

ax = plot_clustered_stacked([stacked_df1, stacked_df2],["TPU1", "TPU2"])

plt.xlabel("Benchmark", fontsize=font_size, labelpad=100)
plt.ylim(0,1000)
plt.yticks(fontsize=font_size)
plt.ylabel("FIT Rate", fontsize=font_size)

plt.savefig("graphs/critical_fit.pdf", bbox_inches='tight')

