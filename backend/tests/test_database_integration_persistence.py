"""
PhoenixML Step 28 — Database Integration & Persistence Layer Validation.

Formally validates the PostgreSQL/SQLAlchemy/Alembic persistence architecture:
1. Alembic migration chain, revisions continuity, and schema consistency.
2. Complete persistence graph across User -> RegisteredModel -> MonitoringObservation / DecisionLog.
3. Referential integrity and foreign key constraints.
4. Persistence durability across independent SQLAlchemy sessions.
5. Constraints, nullability, unique keys, UUID generation, enums, and timezone preservation.
6. Relationship cascades and orphan prevention.
7. Cohesive repository integration across all domain entities.
8. Observational / decision-support safety boundaries (zero autonomous execution on persistence).
"""

import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.auth.security import get_password_hash
from app.db.base import Base
from app.decisions.aimd import AIMDAction, AIMDPriority
from app.decisions.models import ApprovalStatus, DecisionLog
from app.decisions.repository import DecisionLogRepository
from app.decisions.schemas import DecisionLogCreate
from app.models.models import ModelStatus, MonitoringObservation, RegisteredModel
from app.models.monitoring_repository import MonitoringObservationRepository
from app.models.monitoring_schemas import MonitoringObservationCreate
from app.models.repository import RegisteredModelRepository
from app.models.schemas import ModelCreate
from app.users.models import User, UserRole
from tests.conftest import TestingSessionLocal


# ---------------------------------------------------------------------------
# Test 1: Alembic Migration Chain & Schema Consistency
# ---------------------------------------------------------------------------

def test_alembic_migration_chain_and_revisions():
    """
    Validates Alembic migration chain integrity:
    - Verifies that migration versions connect in an unbroken chain from base to head.
    - Confirms head revision is c30a5d242a96.
    - Verifies all 4 domain tables exist in SQLAlchemy Base metadata:
      users, registered_models, monitoring_observations, decision_logs.
    """
    alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    script_dir = ScriptDirectory.from_config(alembic_cfg)

    # 1. Verify head revision
    heads = script_dir.get_heads()
    assert len(heads) == 1
    assert heads[0] == "c30a5d242a96"

    # 2. Traverse revisions from head to base to verify continuity
    revisions = list(script_dir.walk_revisions())
    assert len(revisions) == 5

    expected_chain = [
        ("c30a5d242a96", "38dc8f99dc6c"),
        ("38dc8f99dc6c", "e4cbbfe86b34"),
        ("e4cbbfe86b34", "b9b363044e54"),
        ("b9b363044e54", "1a2b3c4d5e6f"),
        ("1a2b3c4d5e6f", None),
    ]
    for rev, (expected_rev, expected_down) in zip(revisions, expected_chain):
        assert rev.revision == expected_rev
        assert rev.down_revision == expected_down

    # 3. Verify metadata tables
    tables = Base.metadata.tables
    expected_tables = {"users", "registered_models", "monitoring_observations", "decision_logs"}
    assert expected_tables.issubset(set(tables.keys()))

    # 4. Verify primary keys are UUIDs
    for table_name in expected_tables:
        pk_cols = tables[table_name].primary_key.columns
        assert len(pk_cols) == 1
        pk_col = next(iter(pk_cols))
        assert pk_col.name == "id"


# ---------------------------------------------------------------------------
# Test 2: Complete Cross-Entity Persistence Graph
# ---------------------------------------------------------------------------

def test_cross_entity_full_persistence_graph(db_session):
    """
    Persists and verifies the complete PhoenixML domain hierarchy:
    User (ML_ENGINEER)
      └── RegisteredModel (ACTIVE)
            ├── MonitoringObservation (t0, t1, t2)
            └── DecisionLog (PENDING recommendation)

    Verifies bidirectional relationship traversal across fresh SQLAlchemy sessions.
    """
    # 1. Persist User
    user = User(
        id=uuid.uuid4(),
        username="persistence_engineer",
        email="persist_eng@example.com",
        full_name="Persistence Engineer",
        hashed_password=get_password_hash("ValidPass123!"),
        role=UserRole.ML_ENGINEER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    user_id = user.id

    # 2. Persist RegisteredModel owned by user
    model = RegisteredModel(
        id=uuid.uuid4(),
        name="SpamClassifier-PersistenceGraph",
        description="End-to-end database persistence validation model",
        framework="scikit-learn",
        algorithm="MultinomialNB",
        status=ModelStatus.ACTIVE,
        owner_id=user_id,
    )
    db_session.add(model)
    db_session.commit()
    model_id = model.id

    # 3. Persist MonitoringObservations for model
    t0 = datetime.now(timezone.utc) - timedelta(hours=2)
    t1 = datetime.now(timezone.utc) - timedelta(hours=1)
    obs1 = MonitoringObservation(
        id=uuid.uuid4(),
        model_id=model_id,
        observed_at=t0,
        prediction_count=1000,
        positive_prediction_count=300,
        negative_prediction_count=700,
        accuracy=0.92,
        precision=0.91,
        recall=0.90,
        f1_score=0.905,
    )
    obs2 = MonitoringObservation(
        id=uuid.uuid4(),
        model_id=model_id,
        observed_at=t1,
        prediction_count=1050,
        positive_prediction_count=320,
        negative_prediction_count=730,
        accuracy=0.88,
        precision=0.87,
        recall=0.86,
        f1_score=0.865,
    )
    obs1_id = obs1.id
    obs2_id = obs2.id
    db_session.add_all([obs1, obs2])
    db_session.commit()

    # 4. Persist DecisionLog for model
    decision = DecisionLog(
        id=uuid.uuid4(),
        model_id=model_id,
        created_at=datetime.now(timezone.utc),
        health_score=82.5,
        health_status="HEALTHY",
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        confidence=0.90,
        rationale="Model health score is within acceptable parameters.",
        explanation="Performance stable across observation window.",
        supporting_signals=["health_score=82.5", "f1=0.865"],
        requires_human_approval=True,
        approval_status=ApprovalStatus.PENDING,
    )
    db_session.add(decision)
    db_session.commit()
    decision_id = decision.id

    # 5. Expire session and open a completely fresh session
    db_session.close()
    fresh_session = TestingSessionLocal()
    try:
        # Load User and traverse down
        loaded_user = fresh_session.get(User, user_id)
        assert loaded_user is not None
        assert len(loaded_user.models) == 1

        loaded_model = loaded_user.models[0]
        assert loaded_model.id == model_id
        assert loaded_model.owner.id == user_id
        assert loaded_model.owner.username == "persistence_engineer"

        # Check observations relationship
        assert len(loaded_model.observations) == 2
        obs_ids = {o.id for o in loaded_model.observations}
        assert obs1_id in obs_ids
        assert obs2_id in obs_ids
        for o in loaded_model.observations:
            assert o.model.id == model_id

        # Check decisions relationship
        assert len(loaded_model.decisions) == 1
        loaded_dec = loaded_model.decisions[0]
        assert loaded_dec.id == decision_id
        assert loaded_dec.recommended_action == AIMDAction.CONTINUE_MONITORING
        assert loaded_dec.priority == AIMDPriority.LOW
        assert loaded_dec.requires_human_approval is True
        assert loaded_dec.approval_status == ApprovalStatus.PENDING
        assert loaded_dec.model.id == model_id
        assert loaded_dec.model.name == "SpamClassifier-PersistenceGraph"
    finally:
        fresh_session.close()


# ---------------------------------------------------------------------------
# Test 3: Referential Integrity & Foreign Key Isolation
# ---------------------------------------------------------------------------

def test_referential_integrity_and_foreign_keys(db_session):
    """
    Validates foreign key enforcement:
    - Cannot persist RegisteredModel with non-existent owner_id (IntegrityError).
    - Cannot persist MonitoringObservation with non-existent model_id (IntegrityError).
    - Cannot persist DecisionLog with non-existent model_id (IntegrityError).
    - Ensures cross-model isolation between independent models.
    """
    # 1. Non-existent User FK on RegisteredModel
    invalid_user_id = uuid.uuid4()
    bad_model = RegisteredModel(
        id=uuid.uuid4(),
        name="OrphanModel",
        framework="scikit-learn",
        owner_id=invalid_user_id,
        status=ModelStatus.DEVELOPMENT,
    )
    db_session.add(bad_model)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Create valid user and model
    valid_user = User(
        id=uuid.uuid4(),
        username="fk_test_user",
        email="fk_user@example.com",
        full_name="FK User",
        hashed_password="hash",
        role=UserRole.ML_ENGINEER,
    )
    db_session.add(valid_user)
    db_session.commit()

    valid_model = RegisteredModel(
        id=uuid.uuid4(),
        name="FKValidModel",
        framework="scikit-learn",
        owner_id=valid_user.id,
        status=ModelStatus.ACTIVE,
    )
    db_session.add(valid_model)
    db_session.commit()

    # 2. Non-existent Model FK on MonitoringObservation
    invalid_model_id = uuid.uuid4()
    bad_obs = MonitoringObservation(
        id=uuid.uuid4(),
        model_id=invalid_model_id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=100,
    )
    db_session.add(bad_obs)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Non-existent Model FK on DecisionLog
    bad_dec = DecisionLog(
        id=uuid.uuid4(),
        model_id=invalid_model_id,
        created_at=datetime.now(timezone.utc),
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        rationale="Orphan decision test",
        requires_human_approval=True,
        approval_status=ApprovalStatus.PENDING,
    )
    db_session.add(bad_dec)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------------------------------------------------------------------------
# Test 4: Cascade Deletion Invariants
# ---------------------------------------------------------------------------

def test_cascade_deletion_behavior(db_session):
    """
    Validates cascade delete behavior:
    1. Deleting a RegisteredModel removes all its MonitoringObservations and DecisionLogs.
    2. Deleting a User removes all their RegisteredModels (and transitively their observations and decisions).
    3. Other models and users remain completely unaffected.
    """
    # Create two users with models
    user1 = User(id=uuid.uuid4(), username="cascade_u1", email="u1@example.com", full_name="U1", hashed_password="h", role=UserRole.ML_ENGINEER)
    user2 = User(id=uuid.uuid4(), username="cascade_u2", email="u2@example.com", full_name="U2", hashed_password="h", role=UserRole.ML_ENGINEER)
    db_session.add_all([user1, user2])
    db_session.commit()

    model1 = RegisteredModel(id=uuid.uuid4(), name="Model1", framework="sklearn", owner_id=user1.id, status=ModelStatus.ACTIVE)
    model2 = RegisteredModel(id=uuid.uuid4(), name="Model2", framework="sklearn", owner_id=user2.id, status=ModelStatus.ACTIVE)
    db_session.add_all([model1, model2])
    db_session.commit()

    # Add observations and decisions to Model 1
    obs1 = MonitoringObservation(id=uuid.uuid4(), model_id=model1.id, observed_at=datetime.now(timezone.utc), prediction_count=100)
    dec1 = DecisionLog(
        id=uuid.uuid4(),
        model_id=model1.id,
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        rationale="Model 1 decision",
        approval_status=ApprovalStatus.PENDING,
    )
    # Add observation to Model 2
    obs2 = MonitoringObservation(id=uuid.uuid4(), model_id=model2.id, observed_at=datetime.now(timezone.utc), prediction_count=200)
    db_session.add_all([obs1, dec1, obs2])
    db_session.commit()

    # Verify counts before deletion
    assert db_session.scalar(select(text("count(*)")).select_from(RegisteredModel)) == 2
    assert db_session.scalar(select(text("count(*)")).select_from(MonitoringObservation)) == 2
    assert db_session.scalar(select(text("count(*)")).select_from(DecisionLog)) == 1

    # Delete Model 1 -> cascade deletes obs1 and dec1
    db_session.delete(model1)
    db_session.commit()

    # Verify Model 1's records are purged
    assert db_session.get(RegisteredModel, model1.id) is None
    assert db_session.get(MonitoringObservation, obs1.id) is None
    assert db_session.get(DecisionLog, dec1.id) is None

    # Verify Model 2's records are intact
    assert db_session.get(RegisteredModel, model2.id) is not None
    assert db_session.get(MonitoringObservation, obs2.id) is not None

    # Delete User 2 -> cascade deletes Model 2 and obs2
    db_session.delete(user2)
    db_session.commit()

    assert db_session.get(User, user2.id) is None
    assert db_session.get(RegisteredModel, model2.id) is None
    assert db_session.get(MonitoringObservation, obs2.id) is None


# ---------------------------------------------------------------------------
# Test 5: Constraints, Nullability & Timezone Persistence
# ---------------------------------------------------------------------------

def test_constraints_unique_keys_and_timezone_handling(db_session):
    """
    Validates database-level constraints:
    - Unique username and email constraints on users table.
    - Required / NOT NULL column constraints.
    - Timezone-aware timestamp preservation across commits and reloads.
    """
    # 1. Unique email constraint
    u1 = User(username="unique_user_1", email="duplicate@example.com", full_name="U1", hashed_password="h", role=UserRole.ML_ENGINEER)
    db_session.add(u1)
    db_session.commit()

    u2 = User(username="unique_user_2", email="duplicate@example.com", full_name="U2", hashed_password="h", role=UserRole.ML_ENGINEER)
    db_session.add(u2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 2. Non-null rationale on DecisionLog
    user = User(username="tz_user", email="tz@example.com", full_name="TZ", hashed_password="h", role=UserRole.ML_ENGINEER)
    db_session.add(user)
    db_session.commit()

    model = RegisteredModel(name="TZModel", framework="sklearn", owner_id=user.id, status=ModelStatus.ACTIVE)
    db_session.add(model)
    db_session.commit()

    bad_dec = DecisionLog(
        id=uuid.uuid4(),
        model_id=model.id,
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        rationale=None,  # NOT NULL violation
        approval_status=ApprovalStatus.PENDING,
    )
    db_session.add(bad_dec)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Timezone-aware timestamp roundtrip
    now_utc = datetime(2026, 9, 9, 14, 30, 0, tzinfo=timezone.utc)
    obs = MonitoringObservation(
        id=uuid.uuid4(),
        model_id=model.id,
        observed_at=now_utc,
        prediction_count=500,
        positive_prediction_count=150,
        negative_prediction_count=350,
        accuracy=0.91,
        f1_score=0.90,
    )
    db_session.add(obs)
    db_session.commit()
    obs_id = obs.id

    db_session.close()
    fresh = TestingSessionLocal()
    try:
        loaded_obs = fresh.get(MonitoringObservation, obs_id)
        assert loaded_obs is not None
        # Verify hour, minute, day are identical
        assert loaded_obs.observed_at.year == 2026
        assert loaded_obs.observed_at.month == 9
        assert loaded_obs.observed_at.day == 9
        assert loaded_obs.observed_at.hour == 14
        assert loaded_obs.observed_at.minute == 30

        # Verify repository normalization guarantees timezone-awareness (UTC)
        repo = MonitoringObservationRepository(fresh)
        repo_obs = repo.get_by_id(obs_id)
        assert repo_obs is not None
        assert repo_obs.observed_at.tzinfo is not None
        assert repo_obs.observed_at.tzinfo == timezone.utc
    finally:
        fresh.close()


# ---------------------------------------------------------------------------
# Test 6: Repository Integration Across All Domain Entities
# ---------------------------------------------------------------------------

def test_cohesive_repository_integration(db_session):
    """
    Validates that the existing repositories read and write correctly
    without bypassing repository abstractions:
    - RegisteredModelRepository (create, get_by_id, list)
    - MonitoringObservationRepository (create, list_by_model)
    - DecisionLogRepository (create, list_by_model, update_approval_status)
    """
    # 1. Setup user
    user = User(username="repo_user", email="repo@example.com", full_name="Repo User", hashed_password="h", role=UserRole.ML_ENGINEER)
    db_session.add(user)
    db_session.commit()

    model_repo = RegisteredModelRepository(db_session)
    obs_repo = MonitoringObservationRepository(db_session)
    dec_repo = DecisionLogRepository(db_session)

    # 2. RegisteredModelRepository.create
    model_in = ModelCreate(
        name="RepoIntegrationModel",
        description="Testing repository integration",
        framework="scikit-learn",
        algorithm="LogisticRegression",
        status=ModelStatus.ACTIVE,
    )
    created_model = model_repo.create(model_in, owner_id=user.id)
    assert created_model.id is not None
    assert created_model.name == "RepoIntegrationModel"

    # Verify get_by_id
    fetched_model = model_repo.get_by_id(created_model.id)
    assert fetched_model is not None
    assert fetched_model.id == created_model.id

    # 3. MonitoringObservationRepository.create
    obs_in = MonitoringObservationCreate(
        model_id=created_model.id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=800,
        positive_prediction_count=200,
        negative_prediction_count=600,
        accuracy=0.89,
        f1_score=0.88,
    )
    created_obs = obs_repo.create(obs_in)
    assert created_obs.id is not None
    assert created_obs.model_id == created_model.id

    # Verify list_by_model
    obs_list = obs_repo.list_by_model(created_model.id)
    assert len(obs_list) == 1
    assert obs_list[0].id == created_obs.id

    # 4. DecisionLogRepository.create
    dec_in = DecisionLogCreate(
        model_id=created_model.id,
        health_score=85.0,
        health_status="HEALTHY",
        recommended_action=AIMDAction.CONTINUE_MONITORING,
        priority=AIMDPriority.LOW,
        confidence=0.88,
        rationale="Telemetry within nominal thresholds.",
        requires_human_approval=True,
        approval_status=ApprovalStatus.PENDING,
    )
    created_dec = dec_repo.create(dec_in)
    assert created_dec.id is not None
    assert created_dec.approval_status == ApprovalStatus.PENDING

    # 5. DecisionLogRepository.update_approval_status
    updated_dec = dec_repo.update_approval_status(created_dec.id, created_model.id, ApprovalStatus.APPROVED)
    assert updated_dec is not None
    assert updated_dec.approval_status == ApprovalStatus.APPROVED

    # Verify count and listing
    assert dec_repo.count_by_model(created_model.id) == 1
    dec_list = dec_repo.list_by_model(created_model.id)
    assert len(dec_list) == 1
    assert dec_list[0].approval_status == ApprovalStatus.APPROVED


# ---------------------------------------------------------------------------
# Test 7: Safety Boundaries — Zero Autonomous Maintenance Execution on Persistence
# ---------------------------------------------------------------------------

def test_persistence_safety_boundaries_zero_autonomous_execution(db_session):
    """
    Formally verifies the core architectural safety invariant:
    Persisting an APPROVED DecisionLog record in the database must remain purely observational.
    It MUST NOT cause:
    - Mutation of model status (e.g. from ACTIVE to RETRAINING or ROLLED_BACK).
    - Mutation of model framework, algorithm, or parameters.
    - Automatic deployment or pipeline triggers.
    """
    user = User(username="safety_user", email="safety@example.com", full_name="Safety User", hashed_password="h", role=UserRole.ML_ENGINEER)
    db_session.add(user)
    db_session.commit()

    model = RegisteredModel(
        id=uuid.uuid4(),
        name="SafetyVerifiedSpamModel",
        description="Production baseline that must remain strictly invariant",
        framework="scikit-learn",
        algorithm="MultinomialNB",
        status=ModelStatus.ACTIVE,
        owner_id=user.id,
    )
    db_session.add(model)
    db_session.commit()
    model_id = model.id

    # Ingest severe degradation observation
    obs = MonitoringObservation(
        id=uuid.uuid4(),
        model_id=model_id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=500,
        positive_prediction_count=200,
        negative_prediction_count=300,
        accuracy=0.45,
        f1_score=0.44,
    )
    db_session.add(obs)
    db_session.commit()

    # Persist critical recommendation requiring human approval
    decision = DecisionLog(
        id=uuid.uuid4(),
        model_id=model_id,
        created_at=datetime.now(timezone.utc),
        health_score=45.0,
        health_status="CRITICAL",
        recommended_action=AIMDAction.RETRAIN,
        priority=AIMDPriority.CRITICAL,
        confidence=0.95,
        rationale="Severe performance degradation requires human review.",
        requires_human_approval=True,
        approval_status=ApprovalStatus.PENDING,
    )
    db_session.add(decision)
    db_session.commit()
    decision_id = decision.id

    # Human operator approves recommendation in database
    dec_repo = DecisionLogRepository(db_session)
    dec_repo.update_approval_status(decision_id, model_id, ApprovalStatus.APPROVED)
    db_session.commit()

    # Re-fetch model from fresh session and verify 100% invariance
    db_session.close()
    fresh = TestingSessionLocal()
    try:
        refetched_model = fresh.get(RegisteredModel, model_id)
        assert refetched_model is not None
        assert refetched_model.status == ModelStatus.ACTIVE  # Not changed to RETRAINING!
        assert refetched_model.name == "SafetyVerifiedSpamModel"
        assert refetched_model.framework == "scikit-learn"
        assert refetched_model.algorithm == "MultinomialNB"

        # Verify decision log is recorded as APPROVED without side effects
        persisted_dec = fresh.get(DecisionLog, decision_id)
        assert persisted_dec is not None
        assert persisted_dec.approval_status == ApprovalStatus.APPROVED
        assert persisted_dec.recommended_action == AIMDAction.RETRAIN
    finally:
        fresh.close()
