# API endpoints: QA handoff

| Method | Path | What it does | Success |
|---|---|---|---|
| `POST` | `/donations` | Donor registers a surplus food batch | `201` |
| `GET` | `/donations` | List donations, optional `?status=available\|claimed\|expired` | `200` |
| `GET` | `/donations/{id}` | One donation | `200` |
| `PATCH` | `/donations/{id}` | Change any fields of an unclaimed donation | `200` |
| `DELETE` | `/donations/{id}` | Withdraw an unclaimed donation | `204` |
| `POST` | `/claims` | Food bank claims an available donation | `201` |
| `GET` | `/claims` | List claims, oldest first | `200` |
| `GET` | `/claims/{id}` | One claim | `200` |
| `DELETE` | `/claims/{id}` | Cancel a claim; the donation becomes available again | `204` |

> **Changed since the first version:** `GET /claims` now lists **claims**, not available donations. To see what can be claimed, use `GET /donations?status=available`.

> **Storage is in-memory for now.** Data is lost when the server restarts. A PostgreSQL repository will replace it without changing the API.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
ecodrop                            # or: python -m ecodrop --port 8000
```

| What | URL |
|---|---|
| Base URL | `http://127.0.0.1:8000` |
| Interactive docs (Swagger UI) | `http://127.0.0.1:8000/docs` |
| OpenAPI schema | `http://127.0.0.1:8000/openapi.json` |

The Postman collection [`docs/postman/EcoDrop.postman_collection.json`](postman/EcoDrop.postman_collection.json) runs the whole flow below in order (Collection Runner) against a freshly started server. It uses the `baseUrl` variable (default `http://127.0.0.1:8000`) and stores the created ids in `donationId`, `secondDonationId` and `claimId`.

> **Windows + curl:** Polish characters in an inline `-d '...'` body may not be sent as UTF-8, and the server then answers `400 "There was an error parsing the body"`. Use Postman, or put the body in a UTF-8 file and send it with `--data-binary @body.json`.

---

## Donation status

`status` in every donation response is one of:

| Status | Meaning |
|---|---|
| `available` | Not claimed and `expires_at` is in the future: can be claimed |
| `claimed` | A food bank has claimed it |
| `expired` | Not claimed and `expires_at` has passed |

`expired` is calculated when the donation is read; nobody sets it.

## Donations

### `POST /donations`

| Field | Type | Rules |
|---|---|---|
| `donor_name` | string | required, 1–200 characters (whitespace is trimmed) |
| `food_name` | string | required, 1–200 characters |
| `quantity` | number | required, greater than 0 |
| `unit` | string | required, one of `kg`, `l`, `pcs` |
| `expires_at` | string | required, ISO 8601 **with timezone** (`Z` or `+01:00`), must be in the future |
| `pickup_address` | string | required, 1–300 characters |

Unknown fields are rejected (`422`).

```bash
curl -X POST http://127.0.0.1:8000/donations \
  -H "Content-Type: application/json" \
  -d '{
    "donor_name": "Green Market",
    "food_name": "Wholegrain bread",
    "quantity": 12.5,
    "unit": "kg",
    "expires_at": "2026-12-01T18:00:00Z",
    "pickup_address": "ul. Lucerny 15, Warszawa"
  }'
```

Response `201 Created`:

```json
{
  "id": 1,
  "donor_name": "Green Market",
  "food_name": "Wholegrain bread",
  "quantity": 12.5,
  "unit": "kg",
  "expires_at": "2026-12-01T18:00:00Z",
  "pickup_address": "ul. Lucerny 15, Warszawa",
  "status": "available",
  "created_at": "2026-11-15T14:31:52.960704Z"
}
```

> `expires_at` in the samples must be in the future on the day you test. Move it forward if needed.

More sample donations:

```json
{"donor_name": "Bistro Lucerna", "food_name": "Vegetable soup", "quantity": 8, "unit": "l", "expires_at": "2026-11-28T20:00:00+01:00", "pickup_address": "ul. Żegańska 2, Warszawa"}
{"donor_name": "Green Market", "food_name": "Yoghurt 150 g", "quantity": 40, "unit": "pcs", "expires_at": "2026-11-30T12:00:00Z", "pickup_address": "ul. Lucerny 15, Warszawa"}
```

### `GET /donations`

Sorted by `expires_at`, soonest first. Optional filter `status=available|claimed|expired`.

```bash
curl "http://127.0.0.1:8000/donations?status=available"
```

### `GET /donations/{id}`

Returns one donation, or `404 donation_not_found`.

### `PATCH /donations/{id}`

Send only the fields to change, with the same rules as `POST`. Fields cannot be set to `null`, and `id`, `status` and `created_at` cannot be changed. A claimed donation cannot be edited (`409`).

```bash
curl -X PATCH http://127.0.0.1:8000/donations/1 \
  -H "Content-Type: application/json" \
  -d '{"quantity": 20, "expires_at": "2026-12-03T18:00:00Z"}'
```

### `DELETE /donations/{id}`

`204 No Content` with an empty body. A claimed donation cannot be deleted (`409`): cancel its claim first.

## Claims

### `POST /claims`

| Field | Type | Rules |
|---|---|---|
| `donation_id` | integer | required, greater than 0 |
| `food_bank_name` | string | required, 1–200 characters |

```bash
curl -X POST http://127.0.0.1:8000/claims \
  -H "Content-Type: application/json" \
  -d '{"donation_id": 1, "food_bank_name": "Food Bank Wawer"}'
```

Response `201 Created`:

```json
{
  "id": 1,
  "donation_id": 1,
  "food_bank_name": "Food Bank Wawer",
  "claimed_at": "2026-11-15T16:46:37.927892Z"
}
```

The donation's status becomes `claimed`. Only one food bank can claim a donation.

### `GET /claims`, `GET /claims/{id}`

The list is oldest first; the single claim returns `404 claim_not_found` when missing.

### `DELETE /claims/{id}`

`204 No Content`. The claim is removed and its donation is `available` again, so it can be claimed or edited.

---

## Test cases

| # | Request | Expected |
|---|---|---|
| 1 | `GET /donations` and `GET /claims` on a fresh server | `200`, `[]` |
| 2 | `POST /donations` with the sample body | `201`, `id`, `status: "available"`, `created_at` |
| 3 | `POST /donations` twice | `id` increases by 1 |
| 4 | Several donations with different `expires_at`, then `GET /donations` | sorted by `expires_at`, soonest first |
| 5 | `POST /donations` with `expires_at` in the past | `400`, `error: "donation_expired"` |
| 6 | `POST /donations` with `quantity: 0`, `unit: "boxes"`, a missing field, `donor_name: "   "`, `expires_at` without timezone, or an extra field | `422` |
| 7 | `GET /donations/1` | `200`, same body as the `POST` response |
| 8 | `GET /donations/999` | `404`, `error: "donation_not_found"` |
| 9 | `GET /donations/abc` | `422` |
| 10 | `GET /donations?status=gone` | `422` |
| 11 | `PATCH /donations/1` with `{"quantity": 20}` | `200`, only `quantity` changed |
| 12 | `PATCH /donations/1` with `{}` | `200`, nothing changed |
| 13 | `PATCH /donations/1` with `expires_at` in the past | `400`, `error: "donation_expired"` |
| 14 | `PATCH /donations/1` with `{"food_name": null}`, `{"quantity": 0}` or `{"id": 5}` | `422` |
| 15 | `POST /claims` for an available donation | `201`; `GET /donations/{id}` shows `status: "claimed"` |
| 16 | `GET /donations?status=available` after case 15 | the claimed donation is not listed |
| 17 | `POST /claims` for the same donation again | `409`, `error: "donation_already_claimed"` |
| 18 | `PATCH` or `DELETE` the claimed donation | `409`, `error: "donation_already_claimed"` |
| 19 | `POST /claims` with `donation_id: 999` | `404`, `error: "donation_not_found"` |
| 20 | `POST /claims` for a donation whose `expires_at` has passed | `400`, `error: "donation_expired"` |
| 21 | `POST /claims` with a missing field, `donation_id: 0`, `food_bank_name: "  "` or an extra field | `422` |
| 22 | `GET /claims` and `GET /claims/1` | `200` |
| 23 | `GET /claims/999` | `404`, `error: "claim_not_found"` |
| 24 | `DELETE /claims/1` | `204`; the donation is `available` again and can be claimed again |
| 25 | `DELETE /claims/1` again | `404` |
| 26 | `DELETE /donations/{id}` for an unclaimed donation | `204`; then `GET` returns `404` |
| 27 | A donation whose `expires_at` passes while unclaimed | `status: "expired"`; listed by `?status=expired` |
| 28 | Restart the server, then `GET /donations` | `[]` (in-memory storage, expected for now) |

Error formats:

- **Business errors** (`400`, `404`, `409`): `{"error": "<code>", "detail": "<message>"}`
- **Validation errors** (`422`): FastAPI's default `{"detail": [ ... ]}` listing each invalid field.
