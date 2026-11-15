"""Routes for donors registering surplus food."""

from http import HTTPStatus

from fastapi import APIRouter

from ecodrop.core.dependencies import DonationServiceDep
from ecodrop.domain.donation import Donation
from ecodrop.schemas.donation import DonationCreate, DonationRead

router = APIRouter(prefix="/donations", tags=["donations"])


@router.post("", response_model=DonationRead, status_code=HTTPStatus.CREATED)
def create_donation(payload: DonationCreate, service: DonationServiceDep) -> Donation:
    """Register a surplus food batch."""
    return service.create_donation(payload)
