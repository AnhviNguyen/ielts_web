from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.placement_service import PlacementService


def test_placement_overall_rounds_to_half_band():
    assert PlacementService._overall([6.0, 6.5, 7.0, 7.0]) == 6.5
    assert PlacementService._overall([6.5, 6.5, 7.0, 7.0]) == 7.0


def test_manual_band_validation_requires_half_steps():
    assert PlacementService._valid_band(6.5, strict=True) == 6.5
    with pytest.raises(HTTPException):
        PlacementService._valid_band(6.25, strict=True)


def test_diagnostic_band_validation_rounds_model_output():
    assert PlacementService._valid_band(6.24) == 6.0
    assert PlacementService._valid_band(6.26) == 6.5


def test_requires_placement_only_after_cutoff(monkeypatch):
    cfg = SimpleNamespace(PLACEMENT_REQUIRED_AFTER="2026-06-09T00:00:00+00:00")
    monkeypatch.setattr("app.services.placement_service.settings", cfg)

    old_user = SimpleNamespace(created_at=datetime(2026, 6, 8, 23, 59, tzinfo=timezone.utc))
    new_user = SimpleNamespace(created_at=datetime(2026, 6, 9, 0, 0, tzinfo=timezone.utc))

    assert PlacementService._requires_placement(old_user) is False
    assert PlacementService._requires_placement(new_user) is True
