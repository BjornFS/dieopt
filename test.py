from dieopt import get_solution, show_solution

# Show all three solutions for comparison
show_solution(
    wafer_diameter=50.8,
    edge_exclusion=2.0,
    width=2.0,
    height=2.0,
    scribe=7.0,
    solution="comparison"
)

# Get a specific solution and the respective placements
coords = get_solution(
    wafer_diameter=50.8,
    edge_exclusion=2.0,
    width=2.0,
    height=2.0,
    scribe=7.0,
    solution="optimal"  # or "center", "half_offset", "full_offset"
)
print(coords)
