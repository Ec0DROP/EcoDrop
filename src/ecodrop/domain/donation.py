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
    # Never stored: derived from expires_at when a donation is read (see effective_status).
    EXPIRED = "expired"


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

    def effective_status(self, now: datetime) -> DonationStatus:
        """A claimed batch stays claimed; an unclaimed one becomes expired after expires_at."""
        if self.status is DonationStatus.AVAILABLE and self.expires_at <= now:
            return DonationStatus.EXPIRED
        return self.status

    def is_claimable(self, now: datetime) -> bool:
        return self.effective_status(now) is DonationStatus.AVAILABLE
