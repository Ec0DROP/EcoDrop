"""API tests for /claims: claim a donation, list, get, cancel."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier

import pytest

from ecodrop.core.exceptions import DonationAlreadyClaimedError
from ecodrop.repositories.claim_repository import ClaimRepository
from ecodrop.repositories.donation_repository import DonationRepository
from ecodrop.schemas.claim import ClaimCreate
from ecodrop.schemas.donation import DonationCreate
from ecodrop.services.claim_service import ClaimService
from ecodrop.services.donation_service import DonationService
from tests.conftest import NOW, donation_payload

THREADS = 16


def claim(client, donation_id, food_bank_name="Bank Żywności Wawer"):
    return client.post(
        "/claims", json={"donation_id": donation_id, "food_bank_name": food_bank_name}
    )


def test_create_claim_returns_201_and_marks_donation_claimed(client, create_donation):
    donation = create_donation()

    response = claim(client, donation["id"])

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["donation_id"] == donation["id"]
    assert body["food_bank_name"] == "Bank Żywności Wawer"
    assert datetime.fromisoformat(body["claimed_at"]) == NOW
    assert client.get(f"/donations/{donation['id']}").json()["status"] == "claimed"


def test_claimed_donation_leaves_available_list(client, create_donation):
    donation = create_donation()
    claim(client, donation["id"])
    assert client.get("/donations?status=available").json() == []


def test_claiming_twice_returns_409(client, create_donation):
    donation = create_donation()
    claim(client, donation["id"])

    response = claim(client, donation["id"], "Another bank")
    assert response.status_code == 409
    assert response.json() == {
        "error": "donation_already_claimed",
        "detail": f"Donation {donation['id']} is already claimed",
    }
    assert len(client.get("/claims").json()) == 1


def test_claiming_missing_donation_returns_404(client):
    response = claim(client, 99)
    assert response.status_code == 404
    assert response.json()["error"] == "donation_not_found"


def test_claiming_expired_donation_returns_400(client, clock, create_donation):
    donation = create_donation(expires_at=(NOW + timedelta(hours=1)).isoformat())
    clock.now = NOW + timedelta(hours=2)

    response = claim(client, donation["id"])
    assert response.status_code == 400
    assert response.json() == {
        "error": "donation_expired",
        "detail": f"Donation {donation['id']} has expired",
    }


@pytest.mark.parametrize(
    "body",
    [
        {"donation_id": 1},
        {"food_bank_name": "Bank"},
        {"donation_id": 0, "food_bank_name": "Bank"},
        {"donation_id": "one", "food_bank_name": "Bank"},
        {"donation_id": 1, "food_bank_name": "  "},
        {"donation_id": 1, "food_bank_name": "Bank", "extra": True},
    ],
)
def test_create_claim_rejects_invalid_input_with_422(client, create_donation, body):
    create_donation()
    assert client.post("/claims", json=body).status_code == 422


def test_list_claims_oldest_first(client, clock, create_donation):
    first, second = create_donation(), create_donation()
    claim(client, second["id"], "Bank A")
    clock.now = NOW + timedelta(minutes=5)
    claim(client, first["id"], "Bank B")

    response = client.get("/claims")
    assert response.status_code == 200
    assert [c["food_bank_name"] for c in response.json()] == ["Bank A", "Bank B"]


def test_list_claims_is_empty_initially(client):
    assert client.get("/claims").json() == []


def test_get_claim_returns_it_and_404_when_missing(client, create_donation):
    created = claim(client, create_donation()["id"]).json()

    assert client.get(f"/claims/{created['id']}").json() == created
    response = client.get("/claims/99")
    assert response.status_code == 404
    assert response.json() == {"error": "claim_not_found", "detail": "Claim 99 not found"}


def test_cancel_claim_makes_donation_available_again(client, create_donation):
    donation = create_donation()
    created = claim(client, donation["id"]).json()

    response = client.delete(f"/claims/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/claims/{created['id']}").status_code == 404
    assert client.get(f"/donations/{donation['id']}").json()["status"] == "available"
    assert claim(client, donation["id"], "Another bank").status_code == 201


def test_cancel_missing_claim_returns_404(client):
    assert client.delete("/claims/99").status_code == 404


def test_concurrent_claims_on_one_donation_have_one_winner(clock):
    donations, claims = DonationRepository(), ClaimRepository()
    donation = DonationService(donations, clock).create_donation(
        DonationCreate(**donation_payload())
    )
    service = ClaimService(claims, donations, clock)
    start = Barrier(THREADS)

    def try_claim(n: int) -> bool:
        start.wait()
        try:
            service.create_claim(ClaimCreate(donation_id=donation.id, food_bank_name=f"Bank {n}"))
        except DonationAlreadyClaimedError:
            return False
        return True

    with ThreadPoolExecutor(THREADS) as pool:
        results = list(pool.map(try_claim, range(THREADS)))

    assert results.count(True) == 1
    assert len(claims.list_all()) == 1
