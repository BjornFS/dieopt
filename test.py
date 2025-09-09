# example_usage.py
import matplotlib.pyplot as plt
from dieopt import dieopt, Wafer, Die

# scalar-style call
coords_best = dieopt(
    wafer_diameter=50.8,
    edge_exclusion=2.0,
    width=1.0,
    height=1.0,
    scribe=7.0,
    mode="best",
)
print(f"Best DPW: {len(coords_best)}")

# ask for all three and draw
w = Wafer(diameter=50.8, edge_exclusion=2.0)
d = Die(width=1.0, height=1.0, scribe=7.0)
from dieopt import dieopt  # reusing the function API

fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
modes = ["iter1", "iter2", "iter3"]
for ax, m in zip(axes, modes):
    pts, summary = dieopt(wafer=w, die=d, mode=m, draw=True, ax=ax, return_summary=True)
    ax.set_title(f"{m}  DPW={len(pts)}")
    ax.set_aspect("equal", adjustable="box")

# keep limits comparable
xlim, ylim = axes[0].get_xlim(), axes[0].get_ylim()
for ax in axes[1:]:
    ax.set_xlim(xlim); ax.set_ylim(ylim)

plt.show()
