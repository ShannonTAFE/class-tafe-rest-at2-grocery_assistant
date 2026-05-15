from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{csv_path.stem}_{timestamp}{csv_path.suffix}"
    backup_path = backup_dir / backup_name

    shutil.copy2(csv_path, backup_path)

    return backup_path


def read_csv_for_write(csv_path: Path, columns: list[str]) -> pd.DataFrame:
    """
    Read a CSV for writing.

    If the file does not exist, return an empty DataFrame with the expected columns.
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        return pd.DataFrame(columns=columns)

    df = pd.read_csv(csv_path)

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    return df[columns]


def save_csv(df: pd.DataFrame, csv_path: Path) -> None:
    """Save a DataFrame to CSV safely."""
    csv_path = Path(csv_path)
    ensure_parent_dir(csv_path)
    df.to_csv(csv_path, index=False)


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
    if value is None:
        raise ValueError(f"{field_name} is required.")

    if isinstance(value, str) and not value.strip():
        raise ValueError(f"{field_name} is required.")


def validate_non_negative_number(value: object, field_name: str) -> None:
    """Validate that a value can be treated as a non-negative number."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number.")

    if number < 0:
        raise ValueError(f"{field_name} must not be negative.")


def validate_date_or_blank(value: str, field_name: str = "date") -> None:
    """
    Validate YYYY-MM-DD date format.

    Blank dates are allowed because some inventory items may not have expiry dates.
    """
    if value is None or str(value).strip() == "":
        return

    try:
        datetime.strptime(str(value), "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.")