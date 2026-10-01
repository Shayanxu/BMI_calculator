"""Core BMI logic and history storage.

Nothing in this module depends on the GUI, so it can be tested on its own.
"""

import json
import math
from dataclasses import dataclass
from datetime import datetime

MIN_WEIGHT, MAX_WEIGHT = 2, 600      # kg
MIN_HEIGHT, MAX_HEIGHT = 50, 275     # cm

HEALTHY_MIN_BMI, HEALTHY_MAX_BMI = 18.5, 24.9

TIME_FORMAT = "%Y-%m-%d %H:%M"
REQUIRED_KEYS = ("weight", "height", "bmi", "status")
NUMERIC_KEYS = ("weight", "height", "bmi")


@dataclass(frozen=True)
class Category:
    """A BMI category: the BMI must be below `upper` to belong to it."""

    name: str
    upper: float
    color: str


CATEGORIES = (
    Category("underweight", 18.5, "#4dabf7"),
    Category("normal", 25.0, "#51cf66"),
    Category("overweight", 30.0, "#fcc419"),
    Category("obese", math.inf, "#ff6b6b"),
)


def parse_number(text):
    """Turn user input into a float. Accepts a comma as decimal separator."""
    return float(text.strip().replace(",", "."))


def validate_measurements(weight, height):
    """Raise ValueError if weight (kg) or height (cm) is outside the allowed range."""
    if not (MIN_WEIGHT <= weight <= MAX_WEIGHT and MIN_HEIGHT <= height <= MAX_HEIGHT):
        raise ValueError(
            "Enter valid values\n"
            f"Weight {MIN_WEIGHT}-{MAX_WEIGHT} kg\n"
            f"Height {MIN_HEIGHT}-{MAX_HEIGHT} cm"
        )


def calculate_bmi(weight, height):
    """Return the BMI for a weight in kg and a height in cm."""
    validate_measurements(weight, height)
    return weight / (height / 100) ** 2


def classify(bmi):
    """Return the Category that a BMI value falls into."""
    for category in CATEGORIES:
        if bmi < category.upper:
            return category
    return CATEGORIES[-1]


def healthy_weight_range(height):
    """Return the (low, high) weight in kg that gives a healthy BMI for this height in cm."""
    meters_squared = (height / 100) ** 2
    return HEALTHY_MIN_BMI * meters_squared, HEALTHY_MAX_BMI * meters_squared


def make_record(weight, height, now=None):
    """Build a history record (a plain dict, ready to be saved as JSON)."""
    bmi = calculate_bmi(weight, height)
    now = now or datetime.now()
    return {
        "time": now.strftime(TIME_FORMAT),
        "weight": weight,
        "height": height,
        "bmi": bmi,
        "status": classify(bmi).name,
    }


def describe_record(record):
    """One-line text for a history record. Old records without a time still work."""
    return (
        f'{record.get("time", "--")} | {record["weight"]:g} kg | '
        f'{record["height"]:g} cm | BMI {record["bmi"]:.1f} | {record["status"]}'
    )


def _is_valid_record(record):
    return (
        isinstance(record, dict)
        and all(key in record for key in REQUIRED_KEYS)
        and all(isinstance(record[key], (int, float)) for key in NUMERIC_KEYS)
    )


def load_history(path):
    """Load the history list. A missing, corrupt, or malformed file gives an empty list."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError):
        return []

    if not isinstance(data, list):
        return []

    return [record for record in data if _is_valid_record(record)]


def save_history(path, history):
    """Write the history list to a JSON file."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)
