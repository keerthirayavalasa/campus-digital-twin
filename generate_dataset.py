"""Reproducibly create the project's synthetic campus CSV datasets.

Run ``python generate_dataset.py`` from the project root. The sample dates are
fixed so generated files and test results remain reproducible.
"""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


SEED = 20261012
FIRST_DAY = datetime(2026, 10, 12)
SAMPLE_HOURS = (8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
DATA_LABEL = "SYNTHETIC DEMONSTRATION DATA"

CAMPUS = [
    ("academic-a", "Academic Block A", "academic", 600),
    ("academic-b", "Academic Block B", "academic", 450),
    ("library", "Central Library", "library", 500),
    ("labs", "Computer Labs", "laboratory", 320),
    ("canteen", "Canteen", "dining", 260),
    ("parking", "Parking", "parking", 350),
    ("main-gate", "Main Gate", "entrance", 180),
    ("open-area", "Open Areas", "outdoor", 800),
]

PROFILES = {
    "academic-a": (600, (0.12, 0.23, 0.45, 0.66, 0.73, 0.78, 0.70, 0.64, 0.52, 0.35, 0.16)),
    "academic-b": (450, (0.10, 0.20, 0.40, 0.58, 0.69, 0.76, 0.67, 0.60, 0.49, 0.31, 0.14)),
    "main-gate": (180, (0.38, 0.60, 0.31, 0.22, 0.18, 0.20, 0.23, 0.27, 0.30, 0.48, 0.61)),
    "open-area": (800, (0.08, 0.15, 0.25, 0.36, 0.48, 0.56, 0.51, 0.44, 0.35, 0.24, 0.12)),
}


def _bounded_count(capacity: int, ratio: float, rng: random.Random, weekend: bool) -> int:
    weekend_factor = 0.48 if weekend else 1.0
    varied_ratio = ratio * weekend_factor * rng.uniform(0.94, 1.06)
    return max(0, min(capacity, round(capacity * varied_ratio)))


def generate_datasets(output_dir: str | Path = "data") -> None:
    """Write all CSVs using a fixed seed and one week of hourly samples."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    campus_rows = [
        {
            "building_id": building_id,
            "building_name": name,
            "building_type": building_type,
            "latitude": "",
            "longitude": "",
            "capacity": capacity,
            "data_label": DATA_LABEL,
        }
        for building_id, name, building_type, capacity in CAMPUS
    ]
    pd.DataFrame(campus_rows).to_csv(directory / "campus.csv", index=False)

    crowd_rows: list[dict[str, object]] = []
    library_rows: list[dict[str, object]] = []
    lab_rows: list[dict[str, object]] = []
    canteen_rows: list[dict[str, object]] = []
    parking_rows: list[dict[str, object]] = []
    specialized_profiles = {
        "library": (500, (0.10, 0.18, 0.34, 0.55, 0.76, 0.87, 0.82, 0.74, 0.65, 0.48, 0.24)),
        "labs": (320, (0.05, 0.14, 0.58, 0.73, 0.61, 0.52, 0.64, 0.76, 0.60, 0.35, 0.12)),
        "canteen": (260, (0.02, 0.05, 0.12, 0.29, 0.77, 0.91, 0.70, 0.40, 0.22, 0.13, 0.05)),
        "parking": (350, (0.28, 0.58, 0.72, 0.78, 0.80, 0.79, 0.76, 0.71, 0.65, 0.50, 0.30)),
    }

    for day_offset in range(7):
        current_day = FIRST_DAY + timedelta(days=day_offset)
        weekend = current_day.weekday() >= 5
        for sample_index, hour in enumerate(SAMPLE_HOURS):
            stamp = current_day.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S")
            for location_id, (capacity, pattern) in PROFILES.items():
                name = next(item[1] for item in CAMPUS if item[0] == location_id)
                crowd_rows.append(
                    {
                        "timestamp": stamp,
                        "location_id": location_id,
                        "location_name": name,
                        "people_count": _bounded_count(capacity, pattern[sample_index], rng, weekend),
                        "data_label": DATA_LABEL,
                    }
                )
            for location_id, (capacity, pattern) in specialized_profiles.items():
                occupied = _bounded_count(capacity, pattern[sample_index], rng, weekend)
                if location_id == "library":
                    library_rows.append(
                        {
                            "timestamp": stamp,
                            "total_seats": capacity,
                            "occupied_seats": occupied,
                            "available_seats": capacity - occupied,
                            "data_label": DATA_LABEL,
                        }
                    )
                elif location_id == "labs":
                    lab_rows.append(
                        {
                            "timestamp": stamp,
                            "lab_name": "Computer Labs",
                            "capacity": capacity,
                            "occupied_count": occupied,
                            "data_label": DATA_LABEL,
                        }
                    )
                elif location_id == "canteen":
                    canteen_rows.append(
                        {
                            "timestamp": stamp,
                            "capacity": capacity,
                            "occupied_count": occupied,
                            "data_label": DATA_LABEL,
                        }
                    )
                else:
                    parking_rows.append(
                        {
                            "timestamp": stamp,
                            "total_spaces": capacity,
                            "occupied_spaces": occupied,
                            "available_spaces": capacity - occupied,
                            "data_label": DATA_LABEL,
                        }
                    )

    datasets = {
        "crowd.csv": crowd_rows,
        "library.csv": library_rows,
        "labs.csv": lab_rows,
        "canteen.csv": canteen_rows,
        "parking.csv": parking_rows,
    }
    for filename, rows in datasets.items():
        pd.DataFrame(rows).to_csv(directory / filename, index=False)
    print(f"Wrote six reproducible synthetic datasets to {directory.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Output directory (defaults to the project's data folder).",
    )
    arguments = parser.parse_args()
    generate_datasets(arguments.output_dir)
