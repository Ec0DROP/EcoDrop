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
