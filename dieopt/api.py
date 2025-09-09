from __future__ import annotations
from typing import Iterable, List, Tuple, Literal, Optional, Dict, Union
import numpy as np
import matplotlib.pyplot as plt  # Add at the top if not already imported

from .models import Wafer, Die, PlacementResult, ThreeRunSummary, DieOptError
from .algo import optimise_three_fixed_offsets

# We import draw_wafer lazily to avoid forcing matplotlib on users who don't draw.
def _maybe_draw_wafer(diameter: float, edge_exclusion_mm: float, ax):
    from .draw_wafer import draw_wafer  # ← relative import inside the package
    draw_wafer(diameter=diameter, edge_exclusion_mm=edge_exclusion_mm, ax=ax)


Mode = Literal["center", "half_offset", "full_offset", "best", "all"]

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
    mode : {"center", "half_offset", "full_offset", "best", "all"}
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
        For modes "best"/"center"/"half_offset"/"full_offset": List[(x, y)] in wafer-centred mm.
        For mode "all": "center", "half_offset", "full_offset"
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
            from matplotlib.patches import Rectangle
            arr = np.asarray(pts, dtype=float)
            # Draw each die as a rectangle
            for (x, y) in arr:
                # Rectangle is centered at (x, y)
                rect = Rectangle(
                    (x - d.width / 2, y - d.height / 2),  # bottom left corner
                    d.width,
                    d.height,
                    edgecolor='blue',
                    facecolor='none',
                    linewidth=0.5
                )
                ax.add_patch(rect)
        return pts

    # When returning results for mode "all":
    if mode == "all":
        return {
            "center": _to_coords(summary.center),
            "half_offset": _to_coords(summary.half_offset),
            "full_offset": _to_coords(summary.full_offset),
        }
    # For single modes:
    if mode == "center":
        return _to_coords(summary.center)
    elif mode == "half_offset":
        return _to_coords(summary.half_offset)
    elif mode == "full_offset":
        return _to_coords(summary.full_offset)
    elif mode == "best":
        return _to_coords(summary.best)
    else:
        raise DieOptError(f"Unknown mode: {mode!r}")

def show_solution(
    *,
    wafer_diameter: float,
    edge_exclusion: float,
    width: float,
    height: float,
    scribe: float,
    solution: Literal["center", "half_offset", "full_offset", "comparison", "optimal"] = "center",
    ax=None,
):
    mode = solution if solution != "comparison" else "all"

    if solution == "comparison":
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
        modes = ["center", "half_offset", "full_offset"]
        results = {}
        for ax_, m in zip(axes, modes):
            pts = dieopt(
                wafer_diameter=wafer_diameter,
                edge_exclusion=edge_exclusion,
                width=width,
                height=height,
                scribe=scribe,
                mode=m,
                draw=True,
                ax=ax_,
            )
            ax_.set_title(f"{m}  DPW={len(pts)}")
            ax_.set_aspect("equal", adjustable="box")
            results[m] = pts
        plt.show()
        return results
    else:
        if ax is None:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
        pts = dieopt(
            wafer_diameter=wafer_diameter,
            edge_exclusion=edge_exclusion,
            width=width,
            height=height,
            scribe=scribe,
            mode=mode if solution != "optimal" else "best",
            draw=True,
            ax=ax,
        )
        import matplotlib.pyplot as plt
        plt.show()
        return pts

def get_solution(
    *,
    wafer_diameter: float,
    edge_exclusion: float,
    width: float,
    height: float,
    scribe: float,
    solution: Literal["center", "half_offset", "full_offset", "optimal"] = "center",
) -> list[tuple[float, float]]:
    mode = solution if solution != "optimal" else "best"
    return dieopt(
        wafer_diameter=wafer_diameter,
        edge_exclusion=edge_exclusion,
        width=width,
        height=height,
        scribe=scribe,
        mode=mode,
        draw=False,
    )
