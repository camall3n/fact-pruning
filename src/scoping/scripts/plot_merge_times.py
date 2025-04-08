#!%cd ~/dev/downward/src/

import pandas as pd
import seaborn as sns

data = pd.read_csv("scoping/scripts/merge-times.csv")
data = data.melt(
    id_vars="n_action_pairs", var_name="duration_type", value_name="duration"
)

ax = sns.lineplot(data, x="n_action_pairs", y="duration", hue="duration_type")
ax.set_yscale("log")
ax.set_xticks(range(1, 21, 1))
None

# %%

data = pd.read_csv("scoping/scripts/merge-times-updated.csv")
# data = data.melt(
#     id_vars="n", var_name="duration_type", value_name="duration"
# )

ax = sns.lineplot(data, x="n_actions", y="time", hue="algo")
ax.set_yscale("log")
ax.set_xticks(range(1, 17, 1))
None
