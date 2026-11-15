# API endpoints: QA handoff

Two endpoints are available for testing: `POST /donations` and `GET /claims`.

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

A Postman collection with all the cases below is in [`docs/postman/EcoDrop.postman_collection.json`](postman/EcoDrop.postman_collection.json). It uses the `baseUrl` variable (default `http://127.0.0.1:8000`).

---

## `POST /donations`

Registers a surplus food batch.

**Request body (JSON)**

| Field | Type | Rules |
|---|---|---|
| `donor_name` | string | required, 1–200 characters (whitespace is trimmed) |
| `food_name` | string | required, 1–200 characters |
| `quantity` | number | required, greater than 0 |
| `unit` | string | required, one of `kg`, `l`, `pcs` |
| `expires_at` | string | required, ISO 8601 **with timezone** (e.g. `Z` or `+01:00`), must be in the future |
| `pickup_address` | string | required, 1–300 characters |

Unknown fields are rejected.

**Sample request**

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

**Response `201 Created`**

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

## `GET /claims`

Lists donations a food bank can still claim: status `available` and `expires_at` in the future, sorted by `expires_at` (soonest first). No parameters.

```bash
curl http://127.0.0.1:8000/claims
```

**Response `200 OK`**: a JSON array of donations in the same shape as the `POST /donations` response; `[]` when there are none.

---

## Test cases

| # | Request | Expected |
|---|---|---|
| 1 | `GET /claims` on a fresh server | `200`, `[]` |
| 2 | `POST /donations` with the sample body | `201`, body has `id`, `status: "available"`, `created_at` |
| 3 | `POST /donations` twice | `id` increases by 1 |
| 4 | `GET /claims` after case 2 | `200`, array contains the new donation |
| 5 | Several donations with different `expires_at`, then `GET /claims` | sorted by `expires_at`, soonest first |
| 6 | `expires_at` in the past, e.g. `"2026-01-01T10:00:00Z"` | `400`, `{"error": "donation_expired", "detail": "expires_at must be in the future"}` |
| 7 | `quantity: 0` or negative | `422` |
| 8 | `unit: "boxes"` | `422` |
| 9 | Missing required field (e.g. no `pickup_address`) | `422` |
| 10 | `donor_name: "   "` (only spaces) | `422` |
| 11 | `expires_at` without timezone, e.g. `"2026-12-01T18:00:00"` | `422` |
| 12 | Extra field, e.g. `"unexpected": "x"` | `422` |
| 13 | Body that is not JSON | `422` |
| 14 | Restart the server, then `GET /claims` | `[]` (in-memory storage, expected for now) |

Error formats:

- **Business errors** (`400`): `{"error": "<code>", "detail": "<message>"}`
- **Validation errors** (`422`): FastAPI's default `{"detail": [ ... ]}` listing each invalid field.
