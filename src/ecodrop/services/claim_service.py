"""Business rules for food banks claiming donations and cancelling claims."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from ecodrop.core.exceptions import (
    ClaimNotFoundError,
    DonationAlreadyClaimedError,
    DonationExpiredError,
    DonationNotFoundError,
)
from ecodrop.domain.claim import Claim
from ecodrop.domain.donation import DonationStatus
from ecodrop.repositories.claim_repository import ClaimRepository
from ecodrop.repositories.donation_repository import DonationRepository
from ecodrop.schemas.claim import ClaimCreate
from ecodrop.services.donation_service import conflict_or_missing, utc_now


class ClaimService:
    def __init__(
        self,
        claims: ClaimRepository,
        donations: DonationRepository,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._claims = claims
        self._donations = donations
        self._clock = clock

    def create_claim(self, data: ClaimCreate) -> Claim:
        """Reserve an available, unexpired donation for one food bank."""
        now = self._clock()
        donation = self._donations.get(data.donation_id)
        if donation is None:
            raise DonationNotFoundError(data.donation_id)
        status = donation.effective_status(now)
        if status is DonationStatus.CLAIMED:
            raise DonationAlreadyClaimedError(data.donation_id)
        if status is DonationStatus.EXPIRED:
            raise DonationExpiredError(f"Donation {data.donation_id} has expired")

        claimed = replace(donation, status=DonationStatus.CLAIMED)
        if not self._donations.update(claimed, expected_status=DonationStatus.AVAILABLE):
            raise conflict_or_missing(self._donations, data.donation_id)
        # With a database, the status change and the new claim belong in one transaction.
        return self._claims.add(
            Claim(donation_id=data.donation_id, food_bank_name=data.food_bank_name, claimed_at=now)
        )

    def list_claims(self) -> list[Claim]:
        return sorted(self._claims.list_all(), key=lambda c: (c.claimed_at, c.id))

    def get_claim(self, claim_id: int) -> Claim:
        claim = self._claims.get(claim_id)
        if claim is None:
            raise ClaimNotFoundError(claim_id)
        return claim

    def cancel_claim(self, claim_id: int) -> None:
        """Remove the claim and make its donation available again."""
        claim = self._claims.delete(claim_id)
        if claim is None:
            raise ClaimNotFoundError(claim_id)
        donation = self._donations.get(claim.donation_id)
        if donation is not None:
            self._donations.update(
                replace(donation, status=DonationStatus.AVAILABLE),
                expected_status=DonationStatus.CLAIMED,
            )
