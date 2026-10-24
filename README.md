# EcoDrop API 🍃

> An API connecting local supermarkets and restaurants with food banks to donate surplus food before it expires.

## 📌 About The Project
EcoDrop is a **Tech for Good** backend service designed to tackle food waste by bridging the gap between food donors (supermarkets, restaurants, caterers) and recipients (local food banks and charities).

### Key Features & Initial Endpoints
* **`POST /donations`** – Register surplus food batches with expiration dates, quantities, and pickup details.
* **`GET /claims`** – Allow verified food banks to view, filter, and claim available food donations.

---

## 🛠️ Tech Stack
* **Language:** Python 3.11+
* **Framework:** [To be updated - e.g., FastAPI / Express / Crow]
* **Database:** [To be updated - e.g., PostgreSQL]
* **Containerization:** Docker

---

## 👥 Team & Roles
* **Scrum Master / PM:** Krystian
* **Backend Developers:** Olek, Maciej
* **DevOps / QA Tester:** Kuba
* **Technical Writer:** Ola

---

## 🚀 Getting Started

### Prerequisites
* Git
* Python 3.11+

### Installation & Local Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/Ec0DROP/EcoDrop.git
   cd EcoDrop
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```
3. Install the project in editable mode with dev tools:
   ```bash
   pip install -e ".[dev]"
   ```

### Common Commands
| Task | Command |
|------|---------|
| Run the app | `python -m ecodrop` (or `ecodrop --help`) |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Tests | `pytest` |

Configuration is read from environment variables (`ECODROP_ENV`: `development`/`test`/`production`, `ECODROP_LOG_LEVEL`) and can be overridden with `--env` / `--log-level`.

### Project Structure
```
src/ecodrop/
├── __main__.py      # entry point
├── api/             # HTTP routes, request/response schemas
├── core/            # configuration, cross-cutting concerns
├── domain/          # business entities and rules (no I/O)
├── repositories/    # persistence and data access
└── services/        # use cases
tests/               # pytest test suite
```
