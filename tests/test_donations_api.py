"""API tests for POST /donations and GET /claims."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from ecodrop.core.dependencies import get_donation_service
from ecodrop.main import app
from ecodrop.repositories.donation_repository import DonationRepository
from ecodrop.services.donation_service import DonationService

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock():
    return FakeClock(NOW)


@pytest.fixture
def client(clock):
    service = DonationService(DonationRepository(), clock=clock)
    app.dependency_overrides[get_donation_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def donation_payload(**overrides):
    payload = {
        "donor_name": "Green Market",
        "food_name": "Wholegrain bread",
        "quantity": 12.5,
        "unit": "kg",
        "expires_at": (NOW + timedelta(days=2)).isoformat(),
        "pickup_address": "ul. Lucerny 15, Warszawa",
    }
    return payload | overrides


def test_create_donation_returns_201_with_stored_donation(client):
    response = client.post("/donations", json=donation_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "available"
    assert body["food_name"] == "Wholegrain bread"
    assert body["quantity"] == 12.5
    assert datetime.fromisoformat(body["created_at"]) == NOW


def test_create_donation_assigns_incrementing_ids(client):
    first = client.post("/donations", json=donation_payload()).json()
    second = client.post("/donations", json=donation_payload()).json()
    assert (first["id"], second["id"]) == (1, 2)


def test_create_donation_rejects_past_expiry_with_400(client):
    expired = (NOW - timedelta(minutes=1)).isoformat()
    response = client.post("/donations", json=donation_payload(expires_at=expired))

    assert response.status_code == 400
    assert response.json() == {
        "error": "donation_expired",
        "detail": "expires_at must be in the future",
    }


@pytest.mark.parametrize(
    "overrides",
    [
        {"quantity": 0},
        {"quantity": -3},
        {"unit": "boxes"},
        {"donor_name": "   "},
        {"expires_at": "2026-11-20T18:00:00"},  # no timezone
        {"unexpected": "field"},
    ],
)
def test_create_donation_rejects_invalid_input_with_422(client, overrides):
    response = client.post("/donations", json=donation_payload(**overrides))
    assert response.status_code == 422


def test_create_donation_rejects_missing_field_with_422(client):
    payload = donation_payload()
    del payload["pickup_address"]
    assert client.post("/donations", json=payload).status_code == 422


def test_claims_is_empty_without_donations(client):
    response = client.get("/claims")
    assert response.status_code == 200
    assert response.json() == []


def test_claims_lists_unexpired_donations_soonest_first(client, clock):
    later = donation_payload(food_name="Apples", expires_at=(NOW + timedelta(days=5)).isoformat())
    sooner = donation_payload(food_name="Milk", expires_at=(NOW + timedelta(hours=3)).isoformat())
    client.post("/donations", json=later)
    client.post("/donations", json=sooner)

    names = [d["food_name"] for d in client.get("/claims").json()]
    assert names == ["Milk", "Apples"]

    clock.now = NOW + timedelta(hours=4)  # "Milk" has now expired
    names = [d["food_name"] for d in client.get("/claims").json()]
    assert names == ["Apples"]
