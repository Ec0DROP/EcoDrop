"""API tests for /donations: create, list, get, update, delete."""

from datetime import datetime, timedelta

import pytest

from tests.conftest import NOW, donation_payload


def in_hours(hours: float) -> str:
    return (NOW + timedelta(hours=hours)).isoformat()


# --- POST /donations ---------------------------------------------------------------------------


def test_create_donation_returns_201_with_stored_donation(client):
    response = client.post("/donations", json=donation_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "available"
    assert body["food_name"] == "Wholegrain bread"
    assert body["quantity"] == 12.5
    assert datetime.fromisoformat(body["created_at"]) == NOW


def test_create_donation_assigns_incrementing_ids(create_donation):
    assert (create_donation()["id"], create_donation()["id"]) == (1, 2)


def test_create_donation_rejects_past_expiry_with_400(client):
    response = client.post("/donations", json=donation_payload(expires_at=in_hours(-0.1)))

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


# --- GET /donations ----------------------------------------------------------------------------


def test_list_donations_is_empty_initially(client):
    response = client.get("/donations")
    assert response.status_code == 200
    assert response.json() == []


def test_list_donations_sorts_soonest_expiry_first(client, create_donation):
    create_donation(food_name="Apples", expires_at=in_hours(120))
    create_donation(food_name="Milk", expires_at=in_hours(3))

    assert [d["food_name"] for d in client.get("/donations").json()] == ["Milk", "Apples"]


def test_list_donations_marks_and_filters_by_effective_status(client, clock, create_donation):
    milk = create_donation(food_name="Milk", expires_at=in_hours(3))
    create_donation(food_name="Apples", expires_at=in_hours(120))
    soup = create_donation(food_name="Soup", expires_at=in_hours(48))
    client.post("/claims", json={"donation_id": soup["id"], "food_bank_name": "Bank Wawer"})
    clock.now = NOW + timedelta(hours=4)  # Milk has expired

    statuses = {d["food_name"]: d["status"] for d in client.get("/donations").json()}
    assert statuses == {"Milk": "expired", "Apples": "available", "Soup": "claimed"}

    def names(status):
        return [d["food_name"] for d in client.get(f"/donations?status={status}").json()]

    assert names("available") == ["Apples"]
    assert names("claimed") == ["Soup"]
    assert names("expired") == ["Milk"]
    assert client.get(f"/donations/{milk['id']}").json()["status"] == "expired"


def test_list_donations_rejects_unknown_status_with_422(client):
    assert client.get("/donations?status=gone").status_code == 422


# --- GET /donations/{id} -----------------------------------------------------------------------


def test_get_donation_returns_it(client, create_donation):
    created = create_donation()
    response = client.get(f"/donations/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_donation_returns_404(client):
    response = client.get("/donations/99")
    assert response.status_code == 404
    assert response.json() == {"error": "donation_not_found", "detail": "Donation 99 not found"}


def test_get_donation_with_non_numeric_id_returns_422(client):
    assert client.get("/donations/abc").status_code == 422


# --- PATCH /donations/{id} ---------------------------------------------------------------------


def test_update_donation_changes_only_sent_fields(client, create_donation):
    created = create_donation()
    response = client.patch(
        f"/donations/{created['id']}", json={"quantity": 20, "expires_at": in_hours(72)}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 20
    assert datetime.fromisoformat(body["expires_at"]) == NOW + timedelta(hours=72)
    assert body["food_name"] == created["food_name"]
    assert client.get(f"/donations/{created['id']}").json() == body


def test_update_donation_with_empty_body_changes_nothing(client, create_donation):
    created = create_donation()
    response = client.patch(f"/donations/{created['id']}", json={})
    assert response.status_code == 200
    assert response.json() == created


def test_update_donation_rejects_past_expiry_with_400(client, create_donation):
    created = create_donation()
    response = client.patch(f"/donations/{created['id']}", json={"expires_at": in_hours(-1)})
    assert response.status_code == 400
    assert response.json()["error"] == "donation_expired"


@pytest.mark.parametrize(
    "body",
    [{"quantity": 0}, {"unit": "boxes"}, {"food_name": None}, {"food_name": ""}, {"id": 5}],
)
def test_update_donation_rejects_invalid_input_with_422(client, create_donation, body):
    created = create_donation()
    assert client.patch(f"/donations/{created['id']}", json=body).status_code == 422


def test_update_missing_donation_returns_404(client):
    assert client.patch("/donations/99", json={"quantity": 1}).status_code == 404


def test_update_claimed_donation_returns_409(client, create_donation):
    created = create_donation()
    client.post("/claims", json={"donation_id": created["id"], "food_bank_name": "Bank Wawer"})

    response = client.patch(f"/donations/{created['id']}", json={"quantity": 1})
    assert response.status_code == 409
    assert response.json()["error"] == "donation_already_claimed"


# --- DELETE /donations/{id} --------------------------------------------------------------------


def test_delete_donation_returns_204_and_removes_it(client, create_donation):
    created = create_donation()

    response = client.delete(f"/donations/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/donations/{created['id']}").status_code == 404
    assert client.delete(f"/donations/{created['id']}").status_code == 404


def test_delete_claimed_donation_returns_409(client, create_donation):
    created = create_donation()
    client.post("/claims", json={"donation_id": created["id"], "food_bank_name": "Bank Wawer"})

    response = client.delete(f"/donations/{created['id']}")
    assert response.status_code == 409
    assert client.get(f"/donations/{created['id']}").status_code == 200
