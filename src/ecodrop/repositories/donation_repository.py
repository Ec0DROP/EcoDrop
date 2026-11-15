"""Donation storage.

In-memory for now: data is lost on restart. It will be replaced by a PostgreSQL-backed
repository with the same interface once the database schema lands.
"""

from __future__ import annotations

from dataclasses import replace
from itertools import count
from threading import Lock

from ecodrop.domain.donation import Donation, DonationStatus


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

    def get(self, donation_id: int) -> Donation | None:
        with self._lock:
            return self._donations.get(donation_id)

    def list_all(self) -> list[Donation]:
        with self._lock:
            return list(self._donations.values())

    def update(self, donation: Donation, *, expected_status: DonationStatus) -> bool:
        """Replace a stored donation only if its stored status is still ``expected_status``.

        Compare-and-set, so two concurrent requests cannot both claim or edit the same batch
        (the SQL equivalent is ``UPDATE ... WHERE id = :id AND status = :expected``).
        """
        with self._lock:
            current = self._donations.get(donation.id)
            if current is None or current.status is not expected_status:
                return False
            self._donations[donation.id] = donation
            return True

    def delete(self, donation_id: int, *, expected_status: DonationStatus) -> bool:
        """Delete only if the stored status is still ``expected_status`` (see ``update``)."""
        with self._lock:
            current = self._donations.get(donation_id)
            if current is None or current.status is not expected_status:
                return False
            del self._donations[donation_id]
            return True
