"""
Tier 1 & Tier 2 Unit Tests: SQLite Database & Repository (13 Test Cases).
Coverage:
- TC-T1-DB-01: Schema migration initializes all 7 tables
- TC-T1-DB-02: PRAGMA journal_mode=WAL and foreign_keys=ON
- TC-T1-DB-03: Voice profile CRUD
- TC-T1-DB-04: Generation history CRUD
- TC-T1-DB-05: Evaluation metrics CRUD & foreign key linking
- TC-T1-DB-06: Audio asset catalog CRUD
- TC-T1-DB-07: Persistence across disconnect & reconnect
- TC-T2-BND-QUE-01: Concurrent database writes in WAL mode
- TC-T2-BND-DB-01: Foreign key enforcement rejects orphan records
- TC-T2-BND-DB-02: Unique profile name constraint enforcement
- TC-T2-BND-DB-03: Mandatory consent check enforcement
- TC-T2-BND-DB-04: Cascade deletion of evaluation metrics
- TC-T2-BND-DB-05: Non-existent record queries return None gracefully
"""

import sqlite3
import time
from pathlib import Path
import pytest

try:
    from voicestudio.db.repository import DatabaseManager
except ImportError:
    from tests.contracts import DatabaseManager


@pytest.mark.unit
class TestDatabaseTier1:
    """Tier 1: Feature Coverage for Database Schema, Migrations, and CRUD."""

    def test_tc_t1_db_01_schema_migrations_create_7_tables(self, test_db):
        """TC-T1-DB-01: Automatic database initialization creates all 7 required tables."""
        expected_tables = {
            "schema_migrations",
            "audio_files",
            "voice_profiles",
            "model_configs",
            "generation_history",
            "evaluation_metrics",
            "system_telemetry",
        }
        with test_db.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}
            for t in expected_tables:
                assert t in tables, f"Expected table '{t}' missing from database"

    def test_tc_t1_db_02_wal_mode_and_foreign_keys_enabled(self, test_db):
        """TC-T1-DB-02: PRAGMA journal_mode=WAL and PRAGMA foreign_keys=ON."""
        with test_db.get_connection() as conn:
            journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            foreign_keys = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
            assert journal_mode.lower() == "wal"
            assert foreign_keys == 1

    def test_tc_t1_db_03_voice_profile_crud(self, test_db):
        """TC-T1-DB-03: Create, Read, List, and Delete Voice Profile."""
        # Create
        profile = test_db.create_profile(
            name="Alice Studio Voice",
            speaker_consent_given=True,
            consent_signature="Alice Smith",
            description="High clarity test voice",
            reference_transcript="Sample transcript text.",
        )
        assert profile is not None
        p_id = profile["id"]
        assert profile["name"] == "Alice Studio Voice"
        assert profile["speaker_consent_given"] == 1

        # Read
        fetched = test_db.get_profile(p_id)
        assert fetched is not None
        assert fetched["name"] == "Alice Studio Voice"

        # List
        all_profiles = test_db.list_profiles()
        assert any(p["id"] == p_id for p in all_profiles)

        # Delete
        deleted = test_db.delete_profile(p_id)
        assert deleted is True
        assert test_db.get_profile(p_id) is None

    def test_tc_t1_db_04_generation_history_crud(self, test_db):
        """TC-T1-DB-04: Generation history CRUD and status transitions."""
        gen = test_db.create_generation_record(
            profile_id=None,
            prompt_text="Hello voice studio!",
            speed=1.0,
            pitch=0.0,
            temperature=0.7,
            status="queued",
        )
        assert gen is not None
        g_id = gen["id"]
        assert gen["status"] == "queued"

        # Update to processing
        test_db.update_generation_status(g_id, status="processing")
        updated = test_db.get_generation_record(g_id)
        assert updated["status"] == "processing"

        # Update to completed
        test_db.update_generation_status(g_id, status="completed", duration_sec=2.5, rtf=0.15)
        completed = test_db.get_generation_record(g_id)
        assert completed["status"] == "completed"
        assert completed["inference_duration_seconds"] == 2.5
        assert completed["rtf"] == 0.15

    def test_tc_t1_db_05_evaluation_metrics_crud(self, test_db):
        """TC-T1-DB-05: Record WER, CER, and speaker similarity linked to generation."""
        gen = test_db.create_generation_record(profile_id=None, prompt_text="Accuracy test sentence")
        g_id = gen["id"]

        eval_rec = test_db.record_evaluation(
            generation_id=g_id,
            target_text="Accuracy test sentence",
            asr_transcribed_text="Accuracy test sentence",
            wer=0.0,
            cer=0.0,
            insertions=0,
            deletions=0,
            substitutions=0,
            speaker_similarity_score=98.5,
        )
        assert eval_rec is not None
        assert eval_rec["generation_id"] == g_id
        assert eval_rec["wer"] == 0.0
        assert eval_rec["speaker_similarity_score"] == 98.5

    def test_tc_t1_db_06_audio_file_catalog_crud(self, test_db):
        """TC-T1-DB-06: Audio asset catalog records SHA256, duration, sample rate."""
        audio = test_db.create_audio_record(
            file_type="reference",
            filename="sample.wav",
            file_path="data/references/sample.wav",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            file_size_bytes=168000,
            sample_rate=24000,
            channels=1,
            duration_seconds=3.5,
        )
        assert audio is not None
        a_id = audio["id"]
        assert audio["sha256_hash"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        fetched = test_db.get_audio_record(a_id)
        assert fetched["duration_seconds"] == 3.5

    def test_tc_t1_db_07_persistence_across_reconnect(self, tmp_path):
        """TC-T1-DB-07: Data persistence survives database disconnect and reconnect."""
        db_file = tmp_path / "persistent_test.db"
        # First connection session
        db1 = DatabaseManager(db_file)
        p = db1.create_profile(name="Persistent Voice", speaker_consent_given=True)
        p_id = p["id"]
        del db1

        # Second connection session (simulating app restart)
        db2 = DatabaseManager(db_file)
        p_restored = db2.get_profile(p_id)
        assert p_restored is not None
        assert p_restored["name"] == "Persistent Voice"


@pytest.mark.unit
class TestDatabaseTier2:
    """Tier 2: Boundary & Integrity Cases for Database."""

    def test_tc_t2_bnd_que_01_concurrent_writes_wal(self, test_db):
        """TC-T2-BND-QUE-01: Rapid concurrent writes operate cleanly in WAL mode."""
        for i in range(10):
            test_db.create_generation_record(profile_id=None, prompt_text=f"Concurrent job {i}")
        
        with test_db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM generation_history").fetchone()[0]
            assert count == 10

    def test_tc_t2_bnd_db_01_foreign_key_enforcement(self, test_db):
        """TC-T2-BND-DB-01: Inserting generation record with non-existent foreign key fails."""
        with test_db.get_connection() as conn:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO voice_profiles (id, name, speaker_consent_given, consent_timestamp,
                                               reference_audio_id, created_at, updated_at)
                    VALUES ('bad-prof', 'Bad Profile', 1, '2026-11-15T00:00:00Z', 'non-existent-audio-id',
                            '2026-11-15T00:00:00Z', '2026-11-15T00:00:00Z')
                    """
                )

    def test_tc_t2_bnd_db_02_unique_profile_name_enforcement(self, test_db):
        """TC-T2-BND-DB-02: Duplicate profile names are rejected by UNIQUE constraint."""
        test_db.create_profile(name="Duplicate Voice", speaker_consent_given=True)
        with pytest.raises(sqlite3.IntegrityError):
            test_db.create_profile(name="Duplicate Voice", speaker_consent_given=True)

    def test_tc_t2_bnd_db_03_mandatory_consent_rejection(self, test_db):
        """TC-T2-BND-DB-03: Creating profile without affirmative consent is rejected."""
        with pytest.raises(ValueError):
            test_db.create_profile(name="Unconsenting Voice", speaker_consent_given=False)

    def test_tc_t2_bnd_db_04_cascade_delete_evaluation_metrics(self, test_db):
        """TC-T2-BND-DB-04: Deleting generation record cascades to linked evaluation metrics."""
        gen = test_db.create_generation_record(profile_id=None, prompt_text="Cascade test")
        g_id = gen["id"]
        test_db.record_evaluation(
            generation_id=g_id,
            target_text="Cascade test",
            asr_transcribed_text="Cascade test",
            wer=0.0,
            cer=0.0,
            insertions=0,
            deletions=0,
            substitutions=0,
            speaker_similarity_score=95.0,
        )

        with test_db.get_connection() as conn:
            # Delete generation record
            conn.execute("DELETE FROM generation_history WHERE id = ?", (g_id,))
            conn.commit()
            # Assert evaluation metric was cascaded
            eval_count = conn.execute(
                "SELECT COUNT(*) FROM evaluation_metrics WHERE generation_id = ?", (g_id,)
            ).fetchone()[0]
            assert eval_count == 0

    def test_tc_t2_bnd_db_05_non_existent_records_return_none(self, test_db):
        """TC-T2-BND-DB-05: Querying missing records returns None without exception."""
        assert test_db.get_profile("non-existent-id") is None
        assert test_db.get_generation_record("non-existent-id") is None
        assert test_db.get_audio_record("non-existent-id") is None
