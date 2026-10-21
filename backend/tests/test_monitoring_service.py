import pytest
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from unittest.mock import MagicMock

from app.monitoring.service import MonitoringService
from app.models.monitoring_schemas import MonitoringObservationCreate
from app.models.models import MonitoringObservation, RegisteredModel


@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def service(mock_db):
    svc = MonitoringService(mock_db)
    # Mock the internal repositories for isolated testing
    svc.obs_repo = MagicMock()
    svc.model_repo = MagicMock()
    return svc


def test_create_observation_success(service):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    # Mock model
    mock_model = RegisteredModel(id=model_id, owner_id=owner_id)
    service.model_repo.get_by_id.return_value = mock_model
    
    # Mock observation input
    obs_in = MonitoringObservationCreate(
        model_id=model_id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=100
    )
    
    # Mock create return
    mock_obs = MonitoringObservation(id=uuid.uuid4(), model_id=model_id)
    service.obs_repo.create.return_value = mock_obs
    
    result = service.create_observation(obs_in, model_id, owner_id)
    
    assert result == mock_obs
    service.obs_repo.create.assert_called_once_with(obs_in)

def test_create_observation_cross_owner_rejected(service):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    wrong_owner_id = uuid.uuid4()
    
    # Mock model owned by someone else
    mock_model = RegisteredModel(id=model_id, owner_id=wrong_owner_id)
    service.model_repo.get_by_id.return_value = mock_model
    
    obs_in = MonitoringObservationCreate(
        model_id=model_id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=100
    )
    
    with pytest.raises(HTTPException) as exc:
        service.create_observation(obs_in, model_id, owner_id)
    
    assert exc.value.status_code == 404

def test_create_observation_mismatched_url_body_model_id(service):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    wrong_model_id = uuid.uuid4()
    
    mock_model = RegisteredModel(id=model_id, owner_id=owner_id)
    service.model_repo.get_by_id.return_value = mock_model
    
    # Client passes a different model_id in the body
    obs_in = MonitoringObservationCreate(
        model_id=wrong_model_id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=100
    )
    
    with pytest.raises(HTTPException) as exc:
        service.create_observation(obs_in, model_id, owner_id)
    
    assert exc.value.status_code == 422
    assert "URL model_id and body model_id do not match" in exc.value.detail

def test_get_observation_success(service):
    obs_id = uuid.uuid4()
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    mock_obs = MonitoringObservation(id=obs_id, model_id=model_id)
    mock_model = RegisteredModel(id=model_id, owner_id=owner_id)
    
    service.obs_repo.get_by_id.return_value = mock_obs
    service.model_repo.get_by_id.return_value = mock_model
    
    result = service.get_observation(obs_id, owner_id)
    assert result == mock_obs

def test_get_observation_not_found(service):
    obs_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    service.obs_repo.get_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        service.get_observation(obs_id, owner_id)
    
    assert exc.value.status_code == 404

def test_get_observation_cross_owner_rejected(service):
    obs_id = uuid.uuid4()
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    wrong_owner_id = uuid.uuid4()
    
    mock_obs = MonitoringObservation(id=obs_id, model_id=model_id)
    mock_model = RegisteredModel(id=model_id, owner_id=wrong_owner_id)
    
    service.obs_repo.get_by_id.return_value = mock_obs
    service.model_repo.get_by_id.return_value = mock_model
    
    with pytest.raises(HTTPException) as exc:
        service.get_observation(obs_id, owner_id)
    
    assert exc.value.status_code == 404

def test_list_observations(service):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    mock_model = RegisteredModel(id=model_id, owner_id=owner_id)
    service.model_repo.get_by_id.return_value = mock_model
    
    mock_list = [MagicMock(), MagicMock()]
    service.obs_repo.list_by_model.return_value = mock_list
    
    result = service.list_observations(model_id, owner_id, skip=10, limit=5)
    
    assert result == mock_list
    service.obs_repo.list_by_model.assert_called_once_with(model_id, skip=10, limit=5)

def test_delete_observation_success(service):
    obs_id = uuid.uuid4()
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    mock_obs = MonitoringObservation(id=obs_id, model_id=model_id)
    mock_model = RegisteredModel(id=model_id, owner_id=owner_id)
    
    service.obs_repo.get_by_id.return_value = mock_obs
    service.model_repo.get_by_id.return_value = mock_model
    
    service.delete_observation(obs_id, owner_id)
    service.obs_repo.delete.assert_called_once_with(obs_id)

def test_architecture_no_direct_sql_query():
    # Structural verification that the service file doesn't import sqlalchemy query building logic directly
    with open("app/monitoring/service.py", "r") as f:
        content = f.read()
        
    assert "session.query" not in content
    assert "db.execute" not in content
    assert "session.execute(" not in content
    assert "select(" not in content
    assert "update(" not in content
    assert "session.delete(" not in content
