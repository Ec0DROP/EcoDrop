"""Business rules for registering, browsing, editing and withdrawing donations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

from ecodrop.core.exceptions import (
    DonationAlreadyClaimedError,
    DonationExpiredError,
    DonationNotFoundError,
    EcoDropError,
)
from ecodrop.domain.donation import Donation, DonationStatus
from ecodrop.repositories.donation_repository import DonationRepository
from ecodrop.schemas.donation import DonationCreate, DonationUpdate


def utc_now() -> datetime:
    return datetime.now(UTC)


def conflict_or_missing(repository: DonationRepository, donation_id: int) -> EcoDropError:
    """Explain why a compare-and-set on a donation failed: it was deleted or claimed meanwhile."""
    if repository.get(donation_id) is None:
        return DonationNotFoundError(donation_id)
    return DonationAlreadyClaimedError(donation_id)


class DonationService:
    def __init__(
        self, repository: DonationRepository, clock: Callable[[], datetime] = utc_now
    ) -> None:
        self._repository = repository
        self._clock = clock

    def create_donation(self, data: DonationCreate) -> Donation:
        now = self._clock()
        self._ensure_future(data.expires_at, now)
        return self._repository.add(Donation(**data.model_dump(), created_at=now))

    def list_donations(self, status: DonationStatus | None = None) -> list[Donation]:
        """All donations (optionally with one effective status), soonest-expiring first."""
        now = self._clock()
        donations = [self._with_effective_status(d, now) for d in self._repository.list_all()]
        if status is not None:
            donations = [d for d in donations if d.status is status]
        return sorted(donations, key=lambda d: (d.expires_at, d.id))

    def get_donation(self, donation_id: int) -> Donation:
        return self._with_effective_status(self._get_stored(donation_id), self._clock())

    def update_donation(self, donation_id: int, data: DonationUpdate) -> Donation:
        """Edit a donation that has not been claimed yet."""
        now = self._clock()
        current = self._get_stored(donation_id)
        if current.status is DonationStatus.CLAIMED:
            raise DonationAlreadyClaimedError(donation_id)
        changes = data.model_dump(exclude_unset=True)
        if "expires_at" in changes:
            self._ensure_future(changes["expires_at"], now)
        updated = replace(current, **changes)
        if not self._repository.update(updated, expected_status=DonationStatus.AVAILABLE):
            raise conflict_or_missing(self._repository, donation_id)
        return self._with_effective_status(updated, now)

    def delete_donation(self, donation_id: int) -> None:
        """Withdraw a donation; a claimed one must have its claim cancelled first."""
        current = self._get_stored(donation_id)
        if current.status is DonationStatus.CLAIMED:
            raise DonationAlreadyClaimedError(donation_id)
        if not self._repository.delete(donation_id, expected_status=DonationStatus.AVAILABLE):
            raise conflict_or_missing(self._repository, donation_id)

    def _get_stored(self, donation_id: int) -> Donation:
        donation = self._repository.get(donation_id)
        if donation is None:
            raise DonationNotFoundError(donation_id)
        return donation

    @staticmethod
    def _ensure_future(expires_at: datetime, now: datetime) -> None:
        if expires_at <= now:
            raise DonationExpiredError("expires_at must be in the future")

    @staticmethod
    def _with_effective_status(donation: Donation, now: datetime) -> Donation:
        return replace(donation, status=donation.effective_status(now))
