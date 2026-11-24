"""Routes for food banks claiming donations."""

from http import HTTPStatus

from fastapi import APIRouter

from ecodrop.core.dependencies import ClaimServiceDep
from ecodrop.domain.claim import Claim
from ecodrop.schemas.claim import ClaimCreate, ClaimRead

router = APIRouter(prefix="/claims", tags=["claims"])


@router.post("", response_model=ClaimRead, status_code=HTTPStatus.CREATED)
def create_claim(payload: ClaimCreate, service: ClaimServiceDep) -> Claim:
    """Claim an available donation for pickup."""
    return service.create_claim(payload)


@router.get("", response_model=list[ClaimRead])
def list_claims(service: ClaimServiceDep) -> list[Claim]:
    """List claims, oldest first."""
    return service.list_claims()


@router.get("/{claim_id}", response_model=ClaimRead)
def get_claim(claim_id: int, service: ClaimServiceDep) -> Claim:
    """Get a single claim by id."""
    return service.get_claim(claim_id)


@router.delete("/{claim_id}", status_code=HTTPStatus.NO_CONTENT)
def cancel_claim(claim_id: int, service: ClaimServiceDep) -> None:
    """Cancel a claim; its donation becomes available again."""
    service.cancel_claim(claim_id)
