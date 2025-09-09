# dieopt

**dieopt** is a Python package for optimal die placement on circular wafers, supporting semiconductor layout and process engineering. It provides fast, flexible algorithms to maximize die-per-wafer (DPW) yield, visualize placements, and compare strategies.

---

## Features

- **Three fixed-offset strategies:** Center, half-offset, and full-offset placement modes.
- **Optimal DPW calculation:** Quickly compute the best die arrangement for given wafer and die dimensions.
- **Visualization:** Easily plot wafer layouts and compare placement strategies.
- **Simple API:** Functional interface for both quick calculations and detailed analysis.

---

## Installation

```bash
pip install dieopt
```

---

## Quickstart

```python
from dieopt import get_solution, show_solution

# Visualize all three placement strategies
show_solution(
    wafer_diameter=50.8,
    edge_exclusion=2.0,
    width=2.0,
    height=2.0,
    scribe=7.0,
    solution="comparison"
)

# Get coordinates for the optimal placement
coords = get_solution(
    wafer_diameter=50.8,
    edge_exclusion=2.0,
    width=2.0,
    height=2.0,
    scribe=7.0,
    solution="optimal"
)
print(coords)
```

---

## API Reference

### `get_solution(...)`

Compute die placements for a wafer.

**Parameters:**
- `wafer_diameter` (float): Wafer diameter in mm.
- `edge_exclusion` (float): Edge exclusion in mm.
- `width` (float): Die width in mm.
- `height` (float): Die height in mm.
- `scribe` (float): Scribe street width in mm.
- `solution` (str): `"center"`, `"half_offset"`, `"full_offset"`, or `"optimal"`.

**Returns:**  
`List[Tuple[float, float]]` — Die center coordinates.

---

### `show_solution(...)`

Visualize die placements on a wafer.

**Parameters:**
- Same as `get_solution`
- `solution` (str): `"center"`, `"half_offset"`, `"full_offset"`, `"comparison"`, or `"optimal"`

**Returns:**  
Shows a matplotlib plot of the wafer and die placements.

---

## Placement Modes

- **center:** Dies placed with grid centered on wafer.
- **half_offset:** Grid offset by half a die.
- **full_offset:** Grid offset by a full die.
- **optimal:** Automatically selects the best DPW.
- **comparison:** Visualizes all three strategies side-by-side.

---

## Example Output

<!-- Add an example image here if available -->
<!-- ![Wafer Layout Example](docs/example-wafer.png) -->

---

## License

MIT License

---

## Contributing

Pull requests and suggestions are welcome! Please open an issue for bugs or feature requests.

---

## Authors

- Bjorn Funch Schrøder

---

## Acknowledgements

Adapted from my Masters Thesis: "Site controlled epitaxy of quantum dots for nano- and 
quantum photonic applications in telecom wavelength range"

---

**dieopt** — Optimal die placement, made simple.