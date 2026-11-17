"""Claim entity: a food bank reserving a donation for pickup."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Claim:
    donation_id: int
    food_bank_name: str
    claimed_at: datetime
    id: int | None = None
