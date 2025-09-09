from __future__ import annotations
import math
from typing import Tuple
import numpy as np

from .models import Wafer, Die, PlacementResult, ThreeRunSummary

# ---------- geometry helpers ----------

def _usable_radius(w: Wafer) -> float:
    return 0.5 * w.diameter - w.edge_exclusion

def _corners_local(w_die: float, h_die: float) -> np.ndarray:
    hw, hh = 0.5 * w_die, 0.5 * h_die
    return np.array([[-hw, -hh], [ hw, -hh], [ hw,  hh], [-hw,  hh]], dtype=float)

def _within_circle(points: np.ndarray, R: float, tol: float = 1e-9) -> np.ndarray:
    return np.einsum('ij,ij->i', points, points) <= (R * R) * (1 + tol)

def _grid_bounds(R: float, pitch_x: float, pitch_y: float) -> Tuple[np.ndarray, np.ndarray]:
    max_half = R + max(pitch_x, pitch_y)
    ix = int(math.ceil(max_half / pitch_x))
    iy = int(math.ceil(max_half / pitch_y))
    return np.arange(-ix, ix + 1), np.arange(-iy, iy + 1)

def _count_with_offset_no_rotation(wafer: Wafer, die: Die, x_off: float, y_off: float) -> PlacementResult:
    """Place unrotated dies on a rectangular grid with given offset; count only those fully inside usable circle."""
    R = _usable_radius(wafer)
    px = die.width + die.scribe
    py = die.height + die.scribe

    ix, iy = _grid_bounds(R, px, py)
    grid_x = ix * px + x_off
    grid_y = iy * py + y_off

    X, Y = np.meshgrid(grid_x, grid_y, indexing='xy')
    centres = np.column_stack([X.ravel(), Y.ravel()])

    # quick reject by centre-to-edge clearance using half-diagonal
    half_diag = 0.5 * math.hypot(die.width, die.height)
    mask_centre = _within_circle(centres, R - half_diag)
    centres = centres[mask_centre]
    if centres.size == 0:
        return PlacementResult(0, 0.0, (x_off, y_off), np.empty((0, 2)))

    corners0 = _corners_local(die.width, die.height)
    corners_all = centres[:, None, :] + corners0[None, :, :]
    mask_circle = np.all(_within_circle(corners_all.reshape(-1, 2), R).reshape(-1, 4), axis=1)

    good = centres[mask_circle]
    return PlacementResult(dpw=good.shape[0], angle_deg=0.0, offset=(x_off, y_off), positions=good)

def optimise_three_fixed_offsets(wafer: Wafer, die: Die) -> ThreeRunSummary:
    """Evaluate three fixed offsets (0, half-x, half-y, half-both) and return the best DPW."""
    px = die.width + die.scribe
    py = die.height + die.scribe

    r1 = _count_with_offset_no_rotation(wafer, die, 0.0, 0.0)

    r2x = _count_with_offset_no_rotation(wafer, die, 0.5 * px, 0.0)
    r2y = _count_with_offset_no_rotation(wafer, die, 0.0, 0.5 * py)
    if r2x.dpw >= r2y.dpw:
        r2, note2 = r2x, "x"
    else:
        r2, note2 = r2y, "y"

    r3 = _count_with_offset_no_rotation(wafer, die, 0.5 * px, 0.5 * py)

    best = max([r1, r2, r3], key=lambda r: r.dpw)
    return ThreeRunSummary(
        best=best,
        per_iter={
            "center": r1,
            "half_offset": r2,
            "full_offset": r3,
        },
        note_iter2=note2
    )
