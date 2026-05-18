from __future__ import annotations

from pathlib import Path

import pandas as pd

from grocery_assistant_mcp.core.write_helpers import (
    backup_csv,
    save_csv,
)


def save_related_csv_updates(
    operations: list[tuple[str, Path, pd.DataFrame, pd.DataFrame]],
) -> dict[str, str | None]:
    """
    Save multiple related CSV updates with best-effort rollback.

    Each operation is:
    - logical name
    - CSV path
    - original DataFrame
    - updated DataFrame

    This does not replace a real database transaction, but it reduces the risk
    of leaving related CSV files out of sync during multi-file workflows.
    """
    backup_paths: dict[str, str | None] = {}

    try:
        for name, path, _original_df, _updated_df in operations:
            backup_path = backup_csv(path)
            backup_paths[name] = str(backup_path) if backup_path else None

        for _name, path, _original_df, updated_df in operations:
            save_csv(updated_df, path)

    except Exception as exc:
        try:
            for _name, path, original_df, _updated_df in operations:
                save_csv(original_df, path)
        except Exception as rollback_exc:
            raise RuntimeError(
                "Failed to save related CSV updates, and rollback also failed."
            ) from rollback_exc

        raise RuntimeError(
            "Failed to save related CSV updates. Original CSV state was restored."
        ) from exc

    return backup_paths