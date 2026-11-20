"""Import timestamped meter intervals from CSV or Excel files."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO, StringIO
from math import isfinite
from pathlib import Path
from typing import Any


MAX_METER_FILE_BYTES = 10 * 1024 * 1024
MAX_METER_ROWS = 100_000
REQUIRED_COLUMNS = {"timestamp", "price_per_kwh", "base_load_kw"}


@dataclass(frozen=True, slots=True)
class MeterInterval:
    timestamp: datetime
    price_per_kwh: float
    base_load_kw: float
    production_units: float | None = None


@dataclass(frozen=True, slots=True)
class MeterData:
    intervals: tuple[MeterInterval, ...]
    slot_hours: float

    @property
    def prices_per_kwh(self) -> tuple[float, ...]:
        return tuple(item.price_per_kwh for item in self.intervals)

    @property
    def base_load_kw(self) -> tuple[float, ...]:
        return tuple(item.base_load_kw for item in self.intervals)

    @property
    def production_units(self) -> tuple[float, ...] | None:
        if not self.intervals or any(item.production_units is None for item in self.intervals):
            return None
        return tuple(float(item.production_units) for item in self.intervals)


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        raw = value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError(f"Invalid ISO-8601 timestamp: {value!r}") from exc
    else:
        raise ValueError(f"Invalid timestamp value: {value!r}")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Every timestamp must include an explicit UTC offset or timezone")
    return parsed


def _as_float(value: Any, column: str, row_number: int) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Row {row_number}: {column} must be numeric") from exc
    if not isfinite(number):
        raise ValueError(f"Row {row_number}: {column} must be finite")
    return number


def _validate_rows(rows: list[dict[str, Any]]) -> MeterData:
    if not rows:
        raise ValueError("Meter file contains no data rows")
    if len(rows) > MAX_METER_ROWS:
        raise ValueError(f"Meter file exceeds the {MAX_METER_ROWS:,}-row limit")
    columns = {str(key).strip().lower() for key in rows[0] if key is not None}
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    intervals: list[MeterInterval] = []
    production_flags: list[bool] = []
    for row_number, raw in enumerate(rows, start=2):
        row = {
            str(key).strip().lower(): value
            for key, value in raw.items()
            if key is not None
        }
        timestamp = _parse_timestamp(row.get("timestamp"))
        price = _as_float(row.get("price_per_kwh"), "price_per_kwh", row_number)
        load = _as_float(row.get("base_load_kw"), "base_load_kw", row_number)
        if load < 0:
            raise ValueError(f"Row {row_number}: base_load_kw cannot be negative")
        raw_production = row.get("production_units")
        has_production = raw_production not in (None, "")
        production = (
            _as_float(raw_production, "production_units", row_number)
            if has_production else None
        )
        if production is not None and production < 0:
            raise ValueError(f"Row {row_number}: production_units cannot be negative")
        production_flags.append(has_production)
        intervals.append(MeterInterval(timestamp, price, load, production))

    if any(production_flags) and not all(production_flags):
        raise ValueError("production_units must be populated for every row or for none")
    timestamps = [item.timestamp for item in intervals]
    deltas = [
        (timestamps[index] - timestamps[index - 1]).total_seconds()
        for index in range(1, len(timestamps))
    ]
    if not deltas:
        raise ValueError("At least two rows are required to infer interval length")
    if any(delta <= 0 for delta in deltas):
        raise ValueError("Timestamps must be strictly increasing without duplicates")
    if any(abs(delta - deltas[0]) > 1.0 for delta in deltas):
        raise ValueError("Timestamps must be evenly spaced; missing or irregular rows found")
    return MeterData(tuple(intervals), deltas[0] / 3600.0)


def read_meter_data(filename: str, content: bytes) -> MeterData:
    """Read CSV/XLSX columns: timestamp, price_per_kwh, base_load_kw, optional production_units."""
    if len(content) > MAX_METER_FILE_BYTES:
        raise ValueError("Meter file exceeds the 10 MB size limit")
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("CSV file must be UTF-8 encoded") from exc
        reader = csv.DictReader(StringIO(decoded))
        if reader.fieldnames is None:
            raise ValueError("CSV header row is missing")
        return _validate_rows(list(reader))

    if suffix in {".xlsx", ".xlsm"}:
        try:
            from openpyxl import load_workbook
        except ImportError as exc:
            raise ImportError(
                "Excel import requires openpyxl. Install the app extra first."
            ) from exc
        try:
            workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
            sheet = workbook.active
            values = sheet.iter_rows(values_only=True)
            headers = next(values, None)
            if not headers:
                raise ValueError("Excel header row is missing")
            names = [str(value).strip().lower() if value is not None else "" for value in headers]
            rows = [
                dict(zip(names, row))
                for row in values
                if any(value is not None for value in row)
            ]
            workbook.close()
        except (ValueError, OSError):
            raise
        except Exception as exc:
            raise ValueError("Could not read the Excel workbook") from exc
        return _validate_rows(rows)

    raise ValueError("Supported meter file formats are CSV and XLSX")
