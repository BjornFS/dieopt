from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Tuple, Dict

from draw_wafer import draw_wafer

import numpy as np

@dataclass(frozen=True)
class Wafer:
    diameter: float
    edge_exclusion: float = 0.0

@dataclass(frozen=True)
class Die:
    width: float
    height: float
    scribe: float = 0.0

@dataclass
class PlacementResult:
    dpw: int
    angle_deg: float
    offset: Tuple[float, float]
    positions: np.ndarray            # (N,2) die centres in wafer-centred coords (mm)

# ---------- geometry helpers ----------

def _usable_radius(w: Wafer) -> float:
    return 0.5 * w.diameter - w.edge_exclusion

def _corners_local(w_die: float, h_die: float) -> np.ndarray:
    hw, hh = 0.5 * w_die, 0.5 * h_die
    return np.array([[-hw, -hh], [ hw, -hh], [ hw,  hh], [-hw,  hh]], dtype=float)

def _rotate(points: np.ndarray, theta: float) -> np.ndarray:
    # Used with theta=0 in this no-rotation flow; kept for compatibility.
    c, s = math.cos(theta), math.sin(theta)
    R = np.array([[c, -s], [s, c]])
    return points @ R.T

def _within_circle(points: np.ndarray, R: float, tol: float = 1e-9) -> np.ndarray:
    return np.einsum('ij,ij->i', points, points) <= (R * R) * (1 + tol)


# ---------- core counting (angle fixed at 0) ----------

def _grid_bounds(R: float, pitch_x: float, pitch_y: float) -> Tuple[np.ndarray, np.ndarray]:
    max_half = R + max(pitch_x, pitch_y)
    ix = int(math.ceil(max_half / pitch_x))
    iy = int(math.ceil(max_half / pitch_y))
    return np.arange(-ix, ix + 1), np.arange(-iy, iy + 1)

def _count_with_offset_no_rotation(wafer: Wafer, die: Die, x_off: float, y_off: float) -> PlacementResult:
    R = _usable_radius(wafer)

    px = die.width + die.scribe
    py = die.height + die.scribe

    ix, iy = _grid_bounds(R, px, py)
    grid_x = ix * px + x_off
    grid_y = iy * py + y_off

    X, Y = np.meshgrid(grid_x, grid_y, indexing='xy')
    centres = np.column_stack([X.ravel(), Y.ravel()])  # no rotation

    half_diag = 0.5 * math.hypot(die.width, die.height)
    mask_centre = _within_circle(centres, R - half_diag)
    centres = centres[mask_centre]
    if centres.size == 0:
        return PlacementResult(0, 0.0, (x_off, y_off), np.empty((0,2)))

    corners0 = _corners_local(die.width, die.height)   # unrotated corners
    corners_all = centres[:,None,:] + corners0[None,:,:]  # (N,4,2)

    mask_circle = np.all(_within_circle(corners_all.reshape(-1,2), R).reshape(-1,4), axis=1)

    good = centres[mask_circle]
    return PlacementResult(
        dpw=good.shape[0],
        angle_deg=0.0,
        offset=(x_off, y_off),
        positions=good
    )

# ---------- three fixed iterations ----------

@dataclass
class ThreeRunSummary:
    best: PlacementResult
    per_iter: Dict[str, PlacementResult]  # keys: "iter1", "iter2", "iter3"
    note_iter2: str                       # which axis won in iter2 ("x" or "y")

def optimise_three_fixed_offsets(wafer: Wafer, die: Die) -> ThreeRunSummary:
    """
    No rotation. Run 3 iterations and pick best DPW:
      iter1: centred grid (0, 0)
      iter2: shift by half pitch along x OR y (whichever gives higher DPW)
      iter3: shift by half pitch along both x and y
    """
    px = die.width + die.scribe
    py = die.height + die.scribe

    # iter 1: centre
    r1 = _count_with_offset_no_rotation(wafer, die, 0.0, 0.0)

    # iter 2: half in x OR half in y -> choose better
    r2x = _count_with_offset_no_rotation(wafer, die, 0.5 * px, 0.0)
    r2y = _count_with_offset_no_rotation(wafer, die, 0.0, 0.5 * py)
    if r2x.dpw >= r2y.dpw:
        r2, note2 = r2x, "x"
    else:
        r2, note2 = r2y, "y"

    # iter 3: half in both
    r3 = _count_with_offset_no_rotation(wafer, die, 0.5 * px, 0.5 * py)

    # choose best
    best = max([r1, r2, r3], key=lambda r: r.dpw)

    return ThreeRunSummary(best=best, per_iter={"iter1": r1, "iter2": r2, "iter3": r3}, note_iter2=note2)

def wafermap_coordinates(result: PlacementResult) -> List[Tuple[float, float]]:
    return [tuple(p) for p in result.positions]

# ---------- minimal example ----------
if __name__ == "__main__":
    w = Wafer(diameter=50.8, edge_exclusion=2.0)
    d = Die(width=1.0, height=1.0, scribe=7.0)

    summary = optimise_three_fixed_offsets(w, d)

    # Print DPWs
    print(f"Iter1 (centre): DPW={summary.per_iter['iter1'].dpw}, offset={summary.per_iter['iter1'].offset}")
    print(f"Iter2 (half-{summary.note_iter2}): DPW={summary.per_iter['iter2'].dpw}, offset={summary.per_iter['iter2'].offset}")
    print(f"Iter3 (half-x & half-y): DPW={summary.per_iter['iter3'].dpw}, offset={summary.per_iter['iter3'].offset}")
    best = summary.best
    print(f"BEST -> DPW={best.dpw}, offset={best.offset}")

    # ---- plotting all 3 in one window ----
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
titles = ["Iter1: centre", f"Iter2: half-{summary.note_iter2}", "Iter3: half-x & half-y"]

# precompute best key
per_keys = ["iter1", "iter2", "iter3"]
best_key = max(per_keys, key=lambda k: summary.per_iter[k].dpw)

# draw
for ax, key, title in zip(axes, per_keys, titles):
    draw_wafer(diameter=w.diameter, edge_exclusion_mm=w.edge_exclusion, ax=ax)
    res = summary.per_iter[key]
    if res.dpw > 0:
        pts = np.asarray(wafermap_coordinates(res))
        ax.scatter(pts[:, 0], pts[:, 1], s=10)
        ax.set_title(f"{title}\nDPW={res.dpw}")

# enforce identical limits (uses first axis as reference)
xlim, ylim = axes[0].get_xlim(), axes[0].get_ylim()
for ax in axes[1:]:
    ax.set_xlim(xlim); ax.set_ylim(ylim)

plt.show()