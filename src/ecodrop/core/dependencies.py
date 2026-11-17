"""FastAPI dependency providers; tests override these via ``app.dependency_overrides``."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ecodrop.repositories.claim_repository import ClaimRepository
from ecodrop.repositories.donation_repository import DonationRepository
from ecodrop.services.claim_service import ClaimService
from ecodrop.services.donation_service import DonationService


@lru_cache
def get_donation_repository() -> DonationRepository:
    return DonationRepository()


@lru_cache
def get_claim_repository() -> ClaimRepository:
    return ClaimRepository()


def get_donation_service(
    repository: Annotated[DonationRepository, Depends(get_donation_repository)],
) -> DonationService:
    return DonationService(repository)


def get_claim_service(
    claims: Annotated[ClaimRepository, Depends(get_claim_repository)],
    donations: Annotated[DonationRepository, Depends(get_donation_repository)],
) -> ClaimService:
    return ClaimService(claims, donations)


DonationServiceDep = Annotated[DonationService, Depends(get_donation_service)]
ClaimServiceDep = Annotated[ClaimService, Depends(get_claim_service)]
