from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List
import numpy as np

class DieOptError(ValueError):
    """Raised for invalid inputs or inconsistent configuration."""

@dataclass(frozen=True)
class Wafer:
    """Wafer definition.

    Attributes
    ----------
    diameter : float
        Wafer diameter in mm.
    edge_exclusion : float, optional
        Unusable edge margin in mm.
    """
    diameter: float
    edge_exclusion: float = 0.0

    def __post_init__(self) -> None:
        if not (self.diameter and self.diameter > 0):
            raise DieOptError("wafer.diameter must be > 0 (mm).")
        if self.edge_exclusion < 0:
            raise DieOptError("wafer.edge_exclusion must be ≥ 0 (mm).")
        if self.edge_exclusion * 2 >= self.diameter:
            raise DieOptError(
                "edge_exclusion is too large; usable radius would be ≤ 0."
            )

@dataclass(frozen=True)
class Die:
    """Die definition including scribe line.

    Attributes
    ----------
    width : float
        Die width in mm.
    height : float
        Die height in mm.
    scribe : float, optional
        Scribe street width in mm (gap between dies).
    """
    width: float
    height: float
    scribe: float = 0.0

    def __post_init__(self) -> None:
        if not (self.width and self.width > 0):
            raise DieOptError("die.width must be > 0 (mm).")
        if not (self.height and self.height > 0):
            raise DieOptError("die.height must be > 0 (mm).")
        if self.scribe < 0:
            raise DieOptError("die.scribe must be ≥ 0 (mm).")

@dataclass
class PlacementResult:
    """Placement outcome for a particular offset and angle."""
    dpw: int
    angle_deg: float
    offset: Tuple[float, float]
    positions: np.ndarray  # (N,2), wafer-centred coords (mm)

@dataclass
class ThreeRunSummary:
    best: PlacementResult
    per_iter: dict  # keys: "center", "half_offset", "full_offset"
    note_iter2: str

    @property
    def center(self):
        return self.per_iter["center"]

    @property
    def half_offset(self):
        return self.per_iter["half_offset"]

    @property
    def full_offset(self):
        return self.per_iter["full_offset"]
