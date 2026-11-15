"""Routes for food banks browsing donations they can claim."""

from fastapi import APIRouter

from ecodrop.core.dependencies import DonationServiceDep
from ecodrop.domain.donation import Donation
from ecodrop.schemas.donation import DonationRead

router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("", response_model=list[DonationRead])
def list_claimable_donations(service: DonationServiceDep) -> list[Donation]:
    """List donations that are available and not yet expired, soonest-expiring first."""
    return service.list_claimable()
