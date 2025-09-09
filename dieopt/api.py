from __future__ import annotations
from typing import Iterable, List, Tuple, Literal, Optional, Dict, Union
import numpy as np

from .models import Wafer, Die, PlacementResult, ThreeRunSummary, DieOptError
from .algo import optimise_three_fixed_offsets

# We import draw_wafer lazily to avoid forcing matplotlib on users who don't draw.
def _maybe_draw_wafer(diameter: float, edge_exclusion_mm: float, ax):
    from draw_wafer import draw_wafer  # your existing function
    draw_wafer(diameter=diameter, edge_exclusion_mm=edge_exclusion_mm, ax=ax)

Mode = Literal["best", "iter1", "iter2", "iter3", "all"]

def _coerce_wafer(wafer: Optional[Wafer], wafer_diameter: Optional[float], edge_exclusion: Optional[float]) -> Wafer:
    if wafer is not None:
        return wafer
    if wafer_diameter is None:
        raise DieOptError("Provide wafer or wafer_diameter.")
    return Wafer(diameter=float(wafer_diameter), edge_exclusion=float(edge_exclusion or 0.0))

def _coerce_die(die: Optional[Die], width: Optional[float], height: Optional[float], scribe: Optional[float]) -> Die:
    if die is not None:
        return die
    if width is None or height is None:
        raise DieOptError("Provide die or width & height.")
    return Die(width=float(width), height=float(height), scribe=float(scribe or 0.0))

def _positions_to_tuples(arr: np.ndarray) -> List[Tuple[float, float]]:
    return [tuple(map(float, p)) for p in np.asarray(arr).reshape(-1, 2)]

def dieopt(
    *,
    # Either pass objects...
    wafer: Optional[Wafer] = None,
    die: Optional[Die] = None,
    # ...or pass scalars:
    wafer_diameter: Optional[float] = None,
    edge_exclusion: Optional[float] = None,
    width: Optional[float] = None,
    height: Optional[float] = None,
    scribe: Optional[float] = None,
    mode: Mode = "best",
    draw: bool = False,
    ax=None,
    return_summary: bool = False,
) -> Union[List[Tuple[float, float]], Dict[str, List[Tuple[float, float]]], Tuple[List[Tuple[float, float]], ThreeRunSummary], Tuple[Dict[str, List[Tuple[float, float]]], ThreeRunSummary]]:
    """
    Compute die placements for a circular wafer using the three fixed-offset strategy.

    Parameters
    ----------
    wafer, die :
        Optional model objects. If omitted, provide scalar dimensions below.
    wafer_diameter, edge_exclusion :
        Wafer diameter and edge exclusion (mm).
    width, height, scribe :
        Die width/height and scribe street (mm).
    mode : {"best","iter1","iter2","iter3","all"}
        Which result(s) to return.
    draw : bool
        If True, calls user's draw_wafer(...) on the provided `ax`.
    ax :
        Matplotlib Axes to draw onto when draw=True.
    return_summary : bool
        If True, also return the ThreeRunSummary alongside the coordinates.

    Returns
    -------
    coords or mapping
        For modes "best"/"iterN": List[(x, y)] in wafer-centred mm.
        For mode "all": {"iter1": [...], "iter2": [...], "iter3": [...]}
    (coords, summary) if return_summary=True
    """
    w = _coerce_wafer(wafer, wafer_diameter, edge_exclusion)
    d = _coerce_die(die, width, height, scribe)

    summary = optimise_three_fixed_offsets(w, d)

    if draw:
        if ax is None:
            raise DieOptError("draw=True requires a Matplotlib Axes via ax=...")
        _maybe_draw_wafer(diameter=w.diameter, edge_exclusion_mm=w.edge_exclusion, ax=ax)

    def _to_coords(res: PlacementResult) -> List[Tuple[float, float]]:
        pts = _positions_to_tuples(res.positions)
        if draw and pts:
            import numpy as np
            arr = np.asarray(pts, dtype=float)
            ax.scatter(arr[:, 0], arr[:, 1], s=10)
        return pts

    if mode == "best":
        out = _to_coords(summary.best)
    elif mode in ("iter1", "iter2", "iter3"):
        out = _to_coords(summary.per_iter[mode])
    elif mode == "all":
        out = {k: _to_coords(v) for k, v in summary.per_iter.items()}
    else:
        raise DieOptError(f"Unknown mode: {mode!r}")

    return (out, summary) if return_summary else out

class DieOpt:
    """Optional stateful wrapper if users prefer an object interface."""
    def __init__(self, wafer: Wafer, die: Die) -> None:
        self.wafer = wafer
        self.die = die

    def run(self, *, mode: Mode = "best", draw: bool = False, ax=None, return_summary: bool = False):
        return dieopt(wafer=self.wafer, die=self.die, mode=mode, draw=draw, ax=ax, return_summary=return_summary)
