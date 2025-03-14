import pandas as pd
import matplotlib.pyplot as plt

font_size = 14

df = pd.read_csv("./analysis_data/triumf_vs_chipir.csv", index_col="Benchmark")
df = df.sort_values('Benchmark')

ax = df.plot(kind="bar", width=0.7, log=True)

plt.xlabel("Benchmark", fontsize=font_size)
plt.xticks(rotation=45, ha='right', fontsize=font_size-2)
plt.ylim(0,1000)
plt.yticks(fontsize=font_size)
plt.ylabel("FIT Rate", fontsize=font_size)

plt.legend(fontsize=font_size)

for container in ax.containers:
    rounded_labels = [ round(elem, 2) for elem in container.datavalues ]
    ax.bar_label(container, labels=rounded_labels, rotation=90, padding=2)

plt.savefig("graphs/triumf_vs_chipir.pdf", bbox_inches='tight')

