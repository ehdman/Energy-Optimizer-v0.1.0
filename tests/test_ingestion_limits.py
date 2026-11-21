from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook

from energy_optimizer import read_meter_data
from energy_optimizer import ingestion


def test_csv_row_limit_is_enforced_while_reading(monkeypatch) -> None:
    monkeypatch.setattr(ingestion, "MAX_METER_ROWS", 1)
    content = (
        b"timestamp,price_per_kwh,base_load_kw\n"
        b"2026-01-01T00:00:00+00:00,1,2\n"
        b"2026-01-01T01:00:00+00:00,1,2\n"
    )

    with pytest.raises(ValueError, match="row limit"):
        read_meter_data("meter.csv", content)


def test_xlsx_row_limit_is_enforced_while_reading(monkeypatch) -> None:
    monkeypatch.setattr(ingestion, "MAX_METER_ROWS", 1)
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["timestamp", "price_per_kwh", "base_load_kw"])
    sheet.append(["2026-01-01T00:00:00+00:00", 1, 2])
    sheet.append(["2026-01-01T01:00:00+00:00", 1, 2])
    buffer = BytesIO()
    workbook.save(buffer)

    with pytest.raises(ValueError, match="row limit"):
        read_meter_data("meter.xlsx", buffer.getvalue())
