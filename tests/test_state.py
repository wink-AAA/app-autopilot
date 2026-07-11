"""Unit tests for the state management module."""

import json
import tempfile
from pathlib import Path

import pytest

from app_autopilot.core.state import StateStore


@pytest.fixture
def tmp_state_path(tmp_path: Path) -> Path:
    """Provide a temporary path for state files."""
    return tmp_path / "test_state.json"


@pytest.fixture
def store(tmp_state_path: Path) -> StateStore:
    """Provide a fresh StateStore instance."""
    return StateStore(tmp_state_path)


class TestStateStoreCRUD:
    """Tests for basic CRUD operations."""

    def test_put_and_get(self, store: StateStore) -> None:
        store.put("jobs", "j-001", {"title": "Engineer", "status": "pending"})
        record = store.get("jobs", "j-001")
        assert record is not None
        assert record["title"] == "Engineer"
        assert record["status"] == "pending"
        assert "_updated_at" in record

    def test_get_nonexistent(self, store: StateStore) -> None:
        assert store.get("jobs", "nonexistent") is None

    def test_update(self, store: StateStore) -> None:
        store.put("jobs", "j-001", {"title": "Engineer", "status": "pending"})
        success = store.update("jobs", "j-001", {"status": "applied"})
        assert success is True
        record = store.get("jobs", "j-001")
        assert record["status"] == "applied"

    def test_update_nonexistent(self, store: StateStore) -> None:
        success = store.update("jobs", "nonexistent", {"status": "applied"})
        assert success is False

    def test_delete(self, store: StateStore) -> None:
        store.put("jobs", "j-001", {"title": "Engineer"})
        assert store.delete("jobs", "j-001") is True
        assert store.get("jobs", "j-001") is None

    def test_delete_nonexistent(self, store: StateStore) -> None:
        assert store.delete("jobs", "nonexistent") is False

    def test_exists(self, store: StateStore) -> None:
        assert store.exists("jobs", "j-001") is False
        store.put("jobs", "j-001", {"title": "Engineer"})
        assert store.exists("jobs", "j-001") is True


class TestStateStoreCollections:
    """Tests for collection-level operations."""

    def test_list_collections(self, store: StateStore) -> None:
        store.put("jobs", "j-001", {"title": "A"})
        store.put("contacts", "c-001", {"name": "B"})
        collections = store.list_collections()
        assert "jobs" in collections
        assert "contacts" in collections

    def test_count(self, store: StateStore) -> None:
        assert store.count("jobs") == 0
        store.put("jobs", "j-001", {"title": "A"})
        store.put("jobs", "j-002", {"title": "B"})
        assert store.count("jobs") == 2

    def test_clear_collection(self, store: StateStore) -> None:
        store.put("jobs", "j-001", {"title": "A"})
        store.put("jobs", "j-002", {"title": "B"})
        store.clear_collection("jobs")
        assert store.count("jobs") == 0

    def test_get_all(self, store: StateStore) -> None:
        store.put("jobs", "j-001", {"title": "A"})
        store.put("jobs", "j-002", {"title": "B"})
        all_jobs = store.get_all("jobs")
        assert len(all_jobs) == 2
        assert "j-001" in all_jobs
        assert "j-002" in all_jobs


class TestStateStoreExclusions:
    """Tests for exclusion list management."""

    def test_add_and_check_exclusion(self, store: StateStore) -> None:
        store.add_exclusion("contact", "c-001", reason="Spam")
        assert store.is_excluded("contact", "c-001") is True
        assert store.is_excluded("contact", "c-002") is False

    def test_remove_exclusion(self, store: StateStore) -> None:
        store.add_exclusion("job", "j-001", reason="Low salary")
        assert store.is_excluded("job", "j-001") is True
        store.remove_exclusion("job", "j-001")
        assert store.is_excluded("job", "j-001") is False

    def test_get_exclusions_filtered(self, store: StateStore) -> None:
        store.add_exclusion("contact", "c-001")
        store.add_exclusion("job", "j-001")
        store.add_exclusion("contact", "c-002")
        contact_exclusions = store.get_exclusions(entity_type="contact")
        assert len(contact_exclusions) == 2
        job_exclusions = store.get_exclusions(entity_type="job")
        assert len(job_exclusions) == 1


class TestStateStorePersistence:
    """Tests for save/load persistence."""

    def test_save_and_reload(self, tmp_state_path: Path) -> None:
        store1 = StateStore(tmp_state_path)
        store1.put("jobs", "j-001", {"title": "Engineer"})
        store1.save()

        # Verify file exists
        assert tmp_state_path.exists()

        # Load in a new instance
        store2 = StateStore(tmp_state_path)
        record = store2.get("jobs", "j-001")
        assert record is not None
        assert record["title"] == "Engineer"

    def test_dedup_key_exists(self, store: StateStore) -> None:
        store.put("applications", "a-001", {"job_id": "j-001", "platform": "example"})
        assert store.dedup_key_exists("applications", ["job_id", "platform"], {"job_id": "j-001", "platform": "example"}) is True
        assert store.dedup_key_exists("applications", ["job_id", "platform"], {"job_id": "j-002", "platform": "example"}) is False
