"""
wafer_outline.py

Production-ready utilities to compute and draw semiconductor wafer outlines
with an optional bottom flat and optional edge-exclusion ring.

Public API:
- wafer_with_flat_outline(R, L) -> (x, y)
- offset_flat_outline(R, L, e) -> (x, y) | None
- draw_wafer(diameter, edge_exclusion_mm=0.0, *, flat_width=None, flat_ratio=0.33, ax=None) -> Axes

Notes
-----
- Geometry uses a circle of radius R, optionally truncated by a bottom flat of chord length L.
- Edge-exclusion is modelled as a uniform inward offset by e.
- Angles are sampled densely to produce smooth polylines suitable for plotting/CAD export.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

# Matplotlib is only required if draw_wafer is called ; import guarded below.

__all__ = [
    "wafer_with_flat_outline",
    "offset_flat_outline",
    "draw_wafer",
]


def wafer_with_flat_outline(R: float, L: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the polyline (x, y) of a wafer of radius R with an optional bottom flat of chord length L.

    Parameters
    ----------
    R : float
        Wafer radius (> 0).
    L : float
        Bottom-flat chord length in the same units as R. If 0, the outline is a perfect circle.
        Must satisfy 0 ≤ L ≤ 2R.

    Returns
    -------
    (x, y) : Tuple[np.ndarray, np.ndarray]
        Arrays containing the outline coordinates (counter-clockwise, starting at the right-hand
        flat endpoint for L > 0; arbitrary start for a circle).

    Raises
    ------
    ValueError
        If inputs are out of range.

    Notes
    -----
    - For L > 0, the arc spans the circle from the right flat endpoint to the left flat endpoint,
      then a straight segment closes the flat.
    - Uses dense sampling for a smooth outline suitable for plotting.
    """
    if R <= 0:
        raise ValueError("R must be > 0.")
    if L < 0 or L > 2 * R:
        raise ValueError("L (flat width) must be in [0, 2R].")

    if L == 0:
        theta = np.linspace(0.0, 2.0 * np.pi, 1201)
        return R * np.cos(theta), R * np.sin(theta)

    a = L / 2.0
    # Distance from centre to the chord (flat line y = -d)
    d = float(np.sqrt(max(R * R - a * a, 0.0)))
    y_flat = -d
    x_left, x_right = -a, a

    theta_r = float(np.arctan2(y_flat, x_right))
    theta_l = float(np.arctan2(y_flat, x_left))
    if theta_l <= theta_r:
        theta_l += 2.0 * np.pi

    theta_arc = np.linspace(theta_r, theta_l, 1600)
    x_arc = R * np.cos(theta_arc)
    y_arc = R * np.sin(theta_arc)

    x_flat = np.array([x_left, x_right], dtype=float)
    y_flat_seg = np.array([y_flat, y_flat], dtype=float)

    x = np.concatenate([x_arc, x_flat])
    y = np.concatenate([y_arc, y_flat_seg])
    return x, y


def offset_flat_outline(R: float, L: float, e: float) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """
    Compute a uniform inward offset (erosion) by e of a wafer outline with radius R and flat width L.

    Parameters
    ----------
    R : float
        Wafer radius (> 0).
    L : float
        Bottom-flat chord length (≥ 0, ≤ 2R).
    e : float
        Non-negative inward offset. If e ≥ R, the result degenerates.

    Returns
    -------
    (x, y) : Tuple[np.ndarray, np.ndarray] or None
        Polyline coordinates of the inward offset outline. If the offset eliminates the flat
        intersection with the inner circle, falls back to the inner circle only. If R - e ≤ 0,
        returns None.

    Notes
    -----
    - Circle → circle of radius R' = R - e.
    - Flat line y = -d → y' = -(d - e). Endpoints are intersections of y' with the inner circle.
    """
    if e < 0:
        raise ValueError("e (offset) must be ≥ 0.")
    R2 = R - e
    if R2 <= 0:
        return None

    # Circle case
    if L == 0:
        theta = np.linspace(0.0, 2.0 * np.pi, 1001)
        return R2 * np.cos(theta), R2 * np.sin(theta)

    # General case with flat
    a = L / 2.0
    d = float(np.sqrt(max(R * R - a * a, 0.0)))
    y_flat2 = -(d - e)

    # Intersection of the offset flat with inner circle x^2 + y^2 = R2^2
    s = R2 * R2 - y_flat2 * y_flat2  # (x')^2
    if s <= 0:
        # Offset flat does not intersect the inner circle → inner circle only
        theta = np.linspace(0.0, 2.0 * np.pi, 1001)
        return R2 * np.cos(theta), R2 * np.sin(theta)

    a2 = float(np.sqrt(s))  # half-chord of the inner flat
    x_left2, x_right2 = -a2, a2

    theta_r2 = float(np.arctan2(y_flat2, x_right2))
    theta_l2 = float(np.arctan2(y_flat2, x_left2))
    if theta_l2 <= theta_r2:
        theta_l2 += 2.0 * np.pi

    theta_arc2 = np.linspace(theta_r2, theta_l2, 1200)
    x_arc2 = R2 * np.cos(theta_arc2)
    y_arc2 = R2 * np.sin(theta_arc2)

    x_flat2 = np.array([x_left2, x_right2], dtype=float)
    y_flat_seg2 = np.array([y_flat2, y_flat2], dtype=float)

    x2 = np.concatenate([x_arc2, x_flat2])
    y2 = np.concatenate([y_arc2, y_flat_seg2])
    return x2, y2


def draw_wafer(
    diameter: float,
    edge_exclusion_mm: float = 0.0,
    *,
    flat_width: Optional[float] = None,
    flat_ratio: float = 0.33,
    ax=None,
):
    """
    Draw a wafer with an optional bottom flat and an optional edge-exclusion (inward offset).

    Parameters
    ----------
    diameter : float
        Wafer diameter (> 0).
    edge_exclusion_mm : float, default 0.0
        Radial inward offset for edge exclusion (same units as diameter).
    flat_width : float, optional
        Explicit flat width L. If not provided, uses flat_ratio * diameter.
    flat_ratio : float, default 0.33
        Ratio used to derive flat width when flat_width is None. Typical values vary with wafer size.
    ax : matplotlib.axes.Axes, optional
        Target axes. If None, a new figure and axes are created.

    Returns
    -------
    ax : matplotlib.axes.Axes
        Axes with the drawing.

    Raises
    ------
    ValueError
        For invalid parameters.
    ImportError
        If matplotlib is not available but drawing is requested.

    Examples
    --------
    >>> draw_wafer(200.0, edge_exclusion_mm=3.0)  # doctest: +SKIP
    """
    try:
        import matplotlib.pyplot as plt  # deferred import
    except Exception as exc:  # pragma: no cover
        raise ImportError("matplotlib is required for draw_wafer.") from exc

    if diameter <= 0:
        raise ValueError("diameter must be > 0.")
    if edge_exclusion_mm < 0:
        raise ValueError("edge_exclusion_mm must be ≥ 0.")
    if flat_width is None:
        if flat_ratio <= 0 or flat_ratio > 1:
            raise ValueError("flat_ratio must be in (0, 1].")
        L = float(diameter) * float(flat_ratio)
    else:
        L = float(flat_width)

    R = float(diameter) / 2.0
    e = float(edge_exclusion_mm)

    if L < 0 or L > 2 * R:
        raise ValueError("flat_width must be in [0, 2R] (R = diameter/2).")
    if e >= R:
        raise ValueError("edge_exclusion_mm must be < radius (diameter/2).")

    # Axes setup
    created_fig = False
    if ax is None:
        created_fig = True
        fig, ax = plt.subplots()  # noqa: F841 (fig kept alive by reference)

    # Outer wafer
    x, y = wafer_with_flat_outline(R, L)
    ax.plot(x, y, linewidth=1.5, label="Wafer")

    # Edge exclusion (inner, shrunk copy)
    if e > 0:
        inner = offset_flat_outline(R, L, e)
        if inner is not None:
            x2, y2 = inner
            ax.plot(x2, y2, linewidth=1.0, linestyle="--", label=f"Edge excl. {e:g}")

    # Viewport & labelling
    lim = R * 1.1
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-R * 1.25, R * 1.25)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(f"Wafer Ø = {diameter:g}, edge_excl = {edge_exclusion_mm:g}, flat = {L:g}")
    ax.grid(False)

    return ax