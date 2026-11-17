"""Routes for donors registering, editing and withdrawing surplus food."""

from http import HTTPStatus

from fastapi import APIRouter

from ecodrop.core.dependencies import DonationServiceDep
from ecodrop.domain.donation import Donation, DonationStatus
from ecodrop.schemas.donation import DonationCreate, DonationRead, DonationUpdate

router = APIRouter(prefix="/donations", tags=["donations"])


@router.post("", response_model=DonationRead, status_code=HTTPStatus.CREATED)
def create_donation(payload: DonationCreate, service: DonationServiceDep) -> Donation:
    """Register a surplus food batch."""
    return service.create_donation(payload)


@router.get("", response_model=list[DonationRead])
def list_donations(
    service: DonationServiceDep, status: DonationStatus | None = None
) -> list[Donation]:
    """List donations, soonest-expiring first. `status=available` gives what can be claimed."""
    return service.list_donations(status)


@router.get("/{donation_id}", response_model=DonationRead)
def get_donation(donation_id: int, service: DonationServiceDep) -> Donation:
    return service.get_donation(donation_id)


@router.patch("/{donation_id}", response_model=DonationRead)
def update_donation(
    donation_id: int, payload: DonationUpdate, service: DonationServiceDep
) -> Donation:
    """Change any subset of fields of a donation that is not claimed."""
    return service.update_donation(donation_id, payload)


@router.delete("/{donation_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_donation(donation_id: int, service: DonationServiceDep) -> None:
    """Withdraw a donation that is not claimed."""
    service.delete_donation(donation_id)
