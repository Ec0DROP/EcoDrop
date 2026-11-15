"""Business errors raised by services and mapped to HTTP responses in ``ecodrop.main``."""

from http import HTTPStatus


class EcoDropError(Exception):
    """Base class for business errors; subclasses set the HTTP status and error code."""

    status_code: HTTPStatus = HTTPStatus.BAD_REQUEST
    code: str = "bad_request"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class DonationExpiredError(EcoDropError):
    code = "donation_expired"


class DonationNotFoundError(EcoDropError):
    status_code = HTTPStatus.NOT_FOUND
    code = "donation_not_found"

    def __init__(self, donation_id: int) -> None:
        super().__init__(f"Donation {donation_id} not found")


class DonationAlreadyClaimedError(EcoDropError):
    status_code = HTTPStatus.CONFLICT
    code = "donation_already_claimed"

    def __init__(self, donation_id: int) -> None:
        super().__init__(f"Donation {donation_id} is already claimed")


class ClaimNotFoundError(EcoDropError):
    status_code = HTTPStatus.NOT_FOUND
    code = "claim_not_found"

    def __init__(self, claim_id: int) -> None:
        super().__init__(f"Claim {claim_id} not found")
