"""Shared API test fixtures: a fresh in-memory store and a controllable clock per test."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from ecodrop.core.dependencies import get_claim_service, get_donation_service
from ecodrop.main import app
from ecodrop.repositories.claim_repository import ClaimRepository
from ecodrop.repositories.donation_repository import DonationRepository
from ecodrop.services.claim_service import ClaimService
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
    donations, claims = DonationRepository(), ClaimRepository()
    app.dependency_overrides[get_donation_service] = lambda: DonationService(donations, clock)
    app.dependency_overrides[get_claim_service] = lambda: ClaimService(claims, donations, clock)
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


@pytest.fixture
def create_donation(client):
    def create(**overrides) -> dict:
        response = client.post("/donations", json=donation_payload(**overrides))
        assert response.status_code == 201, response.text
        return response.json()

    return create
