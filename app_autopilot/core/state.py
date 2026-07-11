"""Lightweight JSON-based state management.

Provides CRUD operations for tracking records (applications, contacts,
interactions) with automatic deduplication and exclusion-list support.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class StateStore:
    """Persistent state store backed by a JSON file.

    The store organises data into named *collections* (e.g. ``"applications"``,
    ``"contacts"``, ``"exclusions"``).  Each record is a dict keyed by a
    caller-supplied unique ID.

    Example::

        store = StateStore("/tmp/state.json")
        store.put("applications", "job-001", {"title": "Engineer", "status": "pending"})
        record = store.get("applications", "job-001")
        store.update("applications", "job-001", {"status": "replied"})
        store.delete("applications", "job-001")
    """

    def __init__(self, storage_path: str | Path = "data/state.json") -> None:
        self.storage_path = Path(storage_path)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    # -- persistence --------------------------------------------------------

    def _load(self) -> None:
        """Load state from disk, creating the file/directories if needed."""
        if self.storage_path.exists():
            with open(self.storage_path, "r", encoding="utf-8") as fh:
                self._data = json.load(fh)
        else:
            self._data = {}

    def save(self) -> None:
        """Persist current state to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.storage_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)
        # Atomic rename
        os.replace(tmp_path, self.storage_path)

    # -- CRUD ---------------------------------------------------------------

    def put(
        self,
        collection: str,
        record_id: str,
        record: Dict[str, Any],
    ) -> None:
        """Insert or update a record.

        Args:
            collection: Name of the collection (created on first use).
            record_id: Unique identifier within the collection.
            record: Arbitrary data dict.  ``_updated_at`` is set automatically.
        """
        if collection not in self._data:
            self._data[collection] = {}
        record["_updated_at"] = time.time()
        self._data[collection][record_id] = record

    def get(self, collection: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single record, or ``None`` if not found."""
        return self._data.get(collection, {}).get(record_id)

    def get_all(self, collection: str) -> Dict[str, Dict[str, Any]]:
        """Return all records in a collection."""
        return dict(self._data.get(collection, {}))

    def update(
        self,
        collection: str,
        record_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Partially update a record.

        Returns:
            ``True`` if the record existed and was updated, ``False`` otherwise.
        """
        existing = self.get(collection, record_id)
        if existing is None:
            return False
        existing.update(updates)
        existing["_updated_at"] = time.time()
        return True

    def delete(self, collection: str, record_id: str) -> bool:
        """Delete a record.

        Returns:
            ``True`` if the record existed and was removed.
        """
        col = self._data.get(collection, {})
        if record_id in col:
            del col[record_id]
            return True
        return False

    def exists(self, collection: str, record_id: str) -> bool:
        """Check whether a record exists."""
        return record_id in self._data.get(collection, {})

    # -- collection helpers -------------------------------------------------

    def list_collections(self) -> List[str]:
        """Return the names of all collections."""
        return list(self._data.keys())

    def count(self, collection: str) -> int:
        """Return the number of records in a collection."""
        return len(self._data.get(collection, {}))

    def clear_collection(self, collection: str) -> None:
        """Remove all records from a collection."""
        self._data.pop(collection, None)

    # -- exclusion list -----------------------------------------------------

    def add_exclusion(self, entity_type: str, entity_id: str, reason: str = "") -> None:
        """Add an entity to the exclusion list so it is skipped in future runs.

        Args:
            entity_type: Category, e.g. ``"contact"``, ``"job"``.
            entity_id: Unique identifier.
            reason: Optional human-readable reason.
        """
        exclusion_key = f"{entity_type}:{entity_id}"
        self.put("exclusions", exclusion_key, {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "reason": reason,
        })

    def is_excluded(self, entity_type: str, entity_id: str) -> bool:
        """Check whether an entity is on the exclusion list."""
        exclusion_key = f"{entity_type}:{entity_id}"
        return self.exists("exclusions", exclusion_key)

    def get_exclusions(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return exclusion records, optionally filtered by entity type."""
        all_exclusions = self.get_all("exclusions")
        results = list(all_exclusions.values())
        if entity_type is not None:
            results = [r for r in results if r.get("entity_type") == entity_type]
        return results

    def remove_exclusion(self, entity_type: str, entity_id: str) -> bool:
        """Remove an entity from the exclusion list."""
        exclusion_key = f"{entity_type}:{entity_id}"
        return self.delete("exclusions", exclusion_key)

    # -- dedup helpers ------------------------------------------------------

    def dedup_key_exists(self, collection: str, key_fields: List[str], data: Dict[str, Any]) -> bool:
        """Check if a record with matching key fields already exists.

        Useful for preventing duplicate applications or messages.
        """
        for record in self.get_all(collection).values():
            if all(record.get(f) == data.get(f) for f in key_fields):
                return True
        return False
