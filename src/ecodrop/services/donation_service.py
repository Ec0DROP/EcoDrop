"""Business rules for registering and listing donations."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from ecodrop.core.exceptions import DonationExpiredError
from ecodrop.domain.donation import Donation
from ecodrop.repositories.donation_repository import DonationRepository
from ecodrop.schemas.donation import DonationCreate


def utc_now() -> datetime:
    return datetime.now(UTC)


class DonationService:
    def __init__(
        self, repository: DonationRepository, clock: Callable[[], datetime] = utc_now
    ) -> None:
        self._repository = repository
        self._clock = clock

    def create_donation(self, data: DonationCreate) -> Donation:
        now = self._clock()
        if data.expires_at <= now:
            raise DonationExpiredError("expires_at must be in the future")
        return self._repository.add(Donation(**data.model_dump(), created_at=now))

    def list_claimable(self) -> list[Donation]:
        """Donations food banks can still claim, soonest-expiring first."""
        now = self._clock()
        claimable = (d for d in self._repository.list_all() if d.is_claimable(now))
        return sorted(claimable, key=lambda d: d.expires_at)
