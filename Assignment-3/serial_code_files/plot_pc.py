import pandas as pd
import matplotlib.pyplot as plt

# read csv file
data = pd.read_csv("lab_pc_results.csv")

# bar plot
plt.bar(data["Case"], data["Time(sec)"])

plt.xlabel("Problem Index (Case A-E)")
plt.ylabel("Execution Time (sec)")
plt.title("Lab PC Execution Time vs Problem Index")

# save plot
plt.savefig("pc_plot.png")

plt.show()
