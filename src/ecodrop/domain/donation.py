"""Donation entity: a batch of surplus food offered by a donor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Unit(StrEnum):
    KILOGRAM = "kg"
    LITRE = "l"
    PIECE = "pcs"


class DonationStatus(StrEnum):
    AVAILABLE = "available"
    CLAIMED = "claimed"


@dataclass(frozen=True)
class Donation:
    donor_name: str
    food_name: str
    quantity: float
    unit: Unit
    expires_at: datetime
    pickup_address: str
    created_at: datetime
    status: DonationStatus = DonationStatus.AVAILABLE
    id: int | None = None

    def is_claimable(self, now: datetime) -> bool:
        """A food bank can claim a batch only while it is available and not expired."""
        return self.status is DonationStatus.AVAILABLE and self.expires_at > now
