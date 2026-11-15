"""Donation storage.

In-memory for now: data is lost on restart. It will be replaced by a PostgreSQL-backed
repository with the same interface once the database schema lands.
"""

from __future__ import annotations

from dataclasses import replace
from itertools import count
from threading import Lock

from ecodrop.domain.donation import Donation


class DonationRepository:
    def __init__(self) -> None:
        self._donations: dict[int, Donation] = {}
        self._ids = count(start=1)
        self._lock = Lock()

    def add(self, donation: Donation) -> Donation:
        with self._lock:
            stored = replace(donation, id=next(self._ids))
            self._donations[stored.id] = stored
        return stored

    def list_all(self) -> list[Donation]:
        with self._lock:
            return list(self._donations.values())
