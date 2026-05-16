from __future__ import annotations

import math
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


def clean_text(
    value: object,
    field_name: str = "value",
    required: bool = False,
) -> str:
    """
    Convert a value into a stripped string.

    If required=True, blank values raise ValueError.
    """
    if value is None:
        if required:
            raise ValueError(f"{field_name} is required.")
        return ""

    cleaned = str(value).strip()

    if required and cleaned == "":
        raise ValueError(f"{field_name} is required.")

    return cleaned


def clean_lower_text(
    value: object,
    field_name: str = "value",
    required: bool = False,
) -> str:
    """
    Clean text and return lowercase.
    """
    return clean_text(value, field_name, required).lower()


def validate_choice_or_blank(
    value: object,
    valid_values: set[str],
    field_name: str,
    default: str = "",
) -> str:
    """
    Validate a lowercase choice if supplied.

    Blank values are allowed and return the supplied default.
    """
    cleaned = clean_lower_text(value, field_name)

    if cleaned == "":
        return default

    if cleaned not in valid_values:
        allowed = ", ".join(sorted(valid_values))
        raise ValueError(f"{field_name} must be blank or one of: {allowed}")

    return cleaned


def validate_required_choice(
    value: object,
    valid_values: set[str],
    field_name: str,
) -> str:
    """
    Validate a required lowercase choice.
    """
    cleaned = clean_lower_text(value, field_name, required=True)

    if cleaned not in valid_values:
        allowed = ", ".join(sorted(valid_values))
        raise ValueError(f"{field_name} must be one of: {allowed}")

    return cleaned


def validate_non_negative_number(value: object, field_name: str) -> float:
    """
    Validate that a value is a finite non-negative number.

    Returns the cleaned float so callers do not need to convert it again.
    """
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number, not a boolean.")

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number.")

    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be a finite number.")

    if number < 0:
        raise ValueError(f"{field_name} must not be negative.")

    return number


def validate_non_negative_fields(values: dict[str, object]) -> dict[str, float]:
    """
    Validate multiple numeric fields and return them as floats.
    """
    cleaned_values = {}

    for field_name, value in values.items():
        cleaned_values[field_name] = validate_non_negative_number(value, field_name)

    return cleaned_values


def validate_date_or_blank(value: object, field_name: str = "date") -> None:
    """
    Validate YYYY-MM-DD date format.

    Blank dates are allowed because some inventory items may not have expiry dates.
    """
    if value is None or str(value).strip() == "":
        return

    try:
        datetime.strptime(str(value).strip(), "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.")


def validate_required_date(value: object, field_name: str = "date") -> str:
    """
    Validate a required YYYY-MM-DD date and return the cleaned date string.
    """
    cleaned = clean_text(value, field_name, required=True)
    validate_date_or_blank(cleaned, field_name)
    return cleaned


def validate_time_or_blank(value: object, field_name: str = "time") -> None:
    """
    Validate HH:MM time format.

    Blank times are allowed because some entries may be approximate.
    """
    if value is None or str(value).strip() == "":
        return

    try:
        datetime.strptime(str(value).strip(), "%H:%M")
    except ValueError:
        raise ValueError(f"{field_name} must use HH:MM format.")


def validate_int_range(
    value: object,
    field_name: str,
    minimum: int,
    maximum: int,
) -> int:
    """
    Validate an integer within a closed range.
    """
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer, not a boolean.")

    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer.")

    if number < minimum or number > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}.")

    return number


def ensure_parent_dir(path: Path) -> None:
    """Ensure the parent folder for a path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def backup_csv(csv_path: Path, backup_dir: Path | None = None) -> Path | None:
    """
    Create a timestamped backup of a CSV before modifying it.

    Returns the backup path if a backup was created.
    Returns None if the source CSV does not exist yet.
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        return None

    if backup_dir is None:
        backup_dir = csv_path.parent / "backups"

    backup_dir.mkdir(parents=True, exist_ok=True)

    # Microseconds reduce collision risk during rapid write tests.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_name = f"{csv_path.stem}_{timestamp}{csv_path.suffix}"
    backup_path = backup_dir / backup_name

    shutil.copy2(csv_path, backup_path)

    return backup_path


def read_csv_for_write(csv_path: Path, columns: list[str]) -> pd.DataFrame:
    """
    Read a CSV for writing.

    If the file does not exist, return an empty DataFrame with the expected columns.
    Missing expected columns are added as blanks. Extra columns are ignored to keep
    service writes aligned with the declared schema.
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        return pd.DataFrame(columns=columns)

    df = pd.read_csv(csv_path)

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    return df[columns]


def save_csv_atomic(df: pd.DataFrame, csv_path: Path) -> None:
    """
    Save a DataFrame to CSV using a temporary file first.

    This reduces the chance of leaving a half-written CSV if an error occurs
    during the write.
    """
    csv_path = Path(csv_path)
    ensure_parent_dir(csv_path)

    temp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")

    try:
        df.to_csv(temp_path, index=False)
        temp_path.replace(csv_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def save_csv(df: pd.DataFrame, csv_path: Path) -> None:
    """Save a DataFrame to CSV safely."""
    save_csv_atomic(df, csv_path)


def generate_next_id(
    existing_ids: list[str],
    prefix: str,
    width: int = 3,
    separator: str = "_",
) -> str:
    """
    Generate the next ID from existing IDs.

    Example:
        existing IDs: inv_001, inv_002
        prefix: inv
        returns: inv_003
    """
    max_number = 0

    expected_start = f"{prefix}{separator}"

    for existing_id in existing_ids:
        if not isinstance(existing_id, str):
            continue

        if not existing_id.startswith(expected_start):
            continue

        number_part = existing_id.replace(expected_start, "", 1)

        if number_part.isdigit():
            max_number = max(max_number, int(number_part))

    next_number = max_number + 1
    return f"{prefix}{separator}{next_number:0{width}d}"


def require_non_empty(value: object, field_name: str) -> None:
    """Raise ValueError if a required value is missing."""
    clean_text(value, field_name, required=True)
