"""Claim storage. In-memory for now, like ``DonationRepository``."""

from __future__ import annotations

from dataclasses import replace
from itertools import count
from threading import Lock

from ecodrop.domain.claim import Claim


class ClaimRepository:
    def __init__(self) -> None:
        self._claims: dict[int, Claim] = {}
        self._ids = count(start=1)
        self._lock = Lock()

    def add(self, claim: Claim) -> Claim:
        with self._lock:
            stored = replace(claim, id=next(self._ids))
            self._claims[stored.id] = stored
        return stored

    def get(self, claim_id: int) -> Claim | None:
        with self._lock:
            return self._claims.get(claim_id)

    def list_all(self) -> list[Claim]:
        with self._lock:
            return list(self._claims.values())

    def delete(self, claim_id: int) -> Claim | None:
        """Remove and return the claim, or ``None`` if it does not exist."""
        with self._lock:
            return self._claims.pop(claim_id, None)
