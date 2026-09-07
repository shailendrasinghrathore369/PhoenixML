import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from app.models.models import RegisteredModel, ModelStatus, MonitoringObservation
from app.models.monitoring_schemas import MonitoringObservationCreate, MonitoringObservationRead
from app.models.monitoring_repository import MonitoringObservationRepository
from app.users.models import User, UserRole
from tests.conftest import TestingSessionLocal
from app.auth.security import get_password_hash

@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = User(
        username="monitoring_user",
        email="monitor@example.com",
        full_name="Monitoring Admin",
        hashed_password=get_password_hash("password123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture
def test_model(test_user):
    db = TestingSessionLocal()
    model = RegisteredModel(
        id=uuid.uuid4(),
        name="SpamMonitorModel",
        framework="Scikit-Learn",
        status=ModelStatus.ACTIVE,
        owner_id=test_user.id
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    yield model
    
    # Reload model from DB in case the previous session is closed
    db_model = db.get(RegisteredModel, model.id)
    if db_model:
        db.delete(db_model)
        db.commit()
    db.close()

def test_observation_creation_and_retrieval(test_model):
    db = TestingSessionLocal()
    repo = MonitoringObservationRepository(db)
    
    obs_in = MonitoringObservationCreate(
        model_id=test_model.id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=100,
        positive_prediction_count=40,
        negative_prediction_count=60,
        accuracy=0.95,
        precision=0.92,
        recall=0.94,
        f1_score=0.93
    )
    obs = repo.create(obs_in)
    
    assert obs.id is not None
    assert isinstance(obs.id, uuid.UUID)
    
    # 2. observation retrieval
    fetched_obs = repo.get_by_id(obs.id)
    assert fetched_obs is not None
    assert fetched_obs.accuracy == 0.95
    db.close()

def test_listing_observations_by_model(test_model):
    db = TestingSessionLocal()
    repo = MonitoringObservationRepository(db)
    
    now = datetime.now(timezone.utc)
    repo.create(MonitoringObservationCreate(model_id=test_model.id, observed_at=now, prediction_count=10))
    repo.create(MonitoringObservationCreate(model_id=test_model.id, observed_at=now, prediction_count=20))
    
    obs_list = repo.list_by_model(test_model.id)
    assert len(obs_list) >= 2
    assert all(o.model_id == test_model.id for o in obs_list)
    db.close()

def test_deletion(test_model):
    db = TestingSessionLocal()
    repo = MonitoringObservationRepository(db)
    obs = repo.create(MonitoringObservationCreate(model_id=test_model.id, observed_at=datetime.now(timezone.utc)))
    
    assert repo.get_by_id(obs.id) is not None
    assert repo.delete(obs.id) is True
    assert repo.get_by_id(obs.id) is None
    db.close()

def test_model_observations_relationship_and_cascade(test_user):
    db = TestingSessionLocal()
    model = RegisteredModel(
        id=uuid.uuid4(), name="CascadeModel", framework="PyTorch", owner_id=test_user.id
    )
    db.add(model)
    db.commit()
    
    repo = MonitoringObservationRepository(db)
    obs = repo.create(MonitoringObservationCreate(
        model_id=model.id, observed_at=datetime.now(timezone.utc), prediction_count=50
    ))
    
    # Relationship test (from Model to Observations)
    db_model = db.get(RegisteredModel, model.id)
    assert len(db_model.observations) == 1
    assert db_model.observations[0].id == obs.id
    
    # Orphan prevention / Cascade delete
    db.delete(db_model)
    db.commit()
    
    assert repo.get_by_id(obs.id) is None
    db.close()

def test_negative_prediction_count_rejection():
    with pytest.raises(ValidationError):
        MonitoringObservationCreate(
            model_id=uuid.uuid4(),
            observed_at=datetime.now(timezone.utc),
            prediction_count=-1
        )

def test_invalid_metric_range_rejection():
    # Value over 1
    with pytest.raises(ValidationError):
        MonitoringObservationCreate(
            model_id=uuid.uuid4(),
            observed_at=datetime.now(timezone.utc),
            accuracy=1.1
        )
    # Value below 0
    with pytest.raises(ValidationError):
        MonitoringObservationCreate(
            model_id=uuid.uuid4(),
            observed_at=datetime.now(timezone.utc),
            precision=-0.1
        )

def test_invalid_prediction_count_consistency_rejection():
    with pytest.raises(ValueError, match="cannot exceed total prediction count"):
        MonitoringObservationCreate(
            model_id=uuid.uuid4(),
            observed_at=datetime.now(timezone.utc),
            prediction_count=100,
            positive_prediction_count=60,
            negative_prediction_count=50  # 60 + 50 = 110 > 100
        )

def test_nullable_performance_metrics(test_model):
    db = TestingSessionLocal()
    repo = MonitoringObservationRepository(db)
    
    # Metrics left as None
    obs_in = MonitoringObservationCreate(
        model_id=test_model.id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=5
    )
    obs = repo.create(obs_in)
    
    assert obs.accuracy is None
    assert obs.precision is None
    assert obs.recall is None
    assert obs.f1_score is None
    db.close()

def test_timezone_aware_observed_at():
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        MonitoringObservationCreate(
            model_id=uuid.uuid4(),
            observed_at=datetime.now() # Naive
        )

def test_invalid_model_foreign_key_handling():
    db = TestingSessionLocal()
    repo = MonitoringObservationRepository(db)
    
    obs_in = MonitoringObservationCreate(
        model_id=uuid.uuid4(), # Non-existent model ID
        observed_at=datetime.now(timezone.utc)
    )
    with pytest.raises(IntegrityError):
        repo.create(obs_in)
    db.close()
