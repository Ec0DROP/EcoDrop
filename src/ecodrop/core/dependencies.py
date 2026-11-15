"""FastAPI dependency providers; tests override these via ``app.dependency_overrides``."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ecodrop.repositories.donation_repository import DonationRepository
from ecodrop.services.donation_service import DonationService


@lru_cache
def get_donation_repository() -> DonationRepository:
    return DonationRepository()


def get_donation_service(
    repository: Annotated[DonationRepository, Depends(get_donation_repository)],
) -> DonationService:
    return DonationService(repository)


DonationServiceDep = Annotated[DonationService, Depends(get_donation_service)]
