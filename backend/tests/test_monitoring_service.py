import pytest
import uuid
from unittest.mock import MagicMock
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.monitoring_service import MonitoringObservationService
from app.models.monitoring_schemas import MonitoringObservationCreate
from app.models.models import RegisteredModel, MonitoringObservation

@pytest.fixture
def mock_obs_repo():
    return MagicMock()

@pytest.fixture
def mock_model_repo():
    return MagicMock()

@pytest.fixture
def service(mock_obs_repo, mock_model_repo):
    svc = MonitoringObservationService(db=None)
    svc.obs_repo = mock_obs_repo
    svc.model_repo = mock_model_repo
    return svc

def test_create_observation_owned_model(service, mock_obs_repo, mock_model_repo):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    mock_model = RegisteredModel(id=model_id, owner_id=owner_id)
    mock_model_repo.get_by_id.return_value = mock_model
    
    obs_in = MonitoringObservationCreate(
        model_id=model_id,
        observed_at=datetime.now(timezone.utc),
        prediction_count=100
    )
    
    expected_obs = MonitoringObservation(id=uuid.uuid4(), model_id=model_id)
    mock_obs_repo.create.return_value = expected_obs
    
    result = service.create_observation(model_id, obs_in, owner_id=owner_id)
    
    mock_model_repo.get_by_id.assert_called_once_with(model_id)
    mock_obs_repo.create.assert_called_once_with(obs_in)
    assert result == expected_obs
    assert obs_in.model_id == model_id

def test_create_observation_nonexistent_model(service, mock_model_repo):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    mock_model_repo.get_by_id.return_value = None
    
    obs_in = MonitoringObservationCreate(
        model_id=model_id,
        observed_at=datetime.now(timezone.utc)
    )
    
    with pytest.raises(HTTPException) as exc:
        service.create_observation(model_id, obs_in, owner_id=owner_id)
        
    assert exc.value.status_code == 404
    assert exc.value.detail == "Model not found"

def test_create_observation_another_users_model(service, mock_model_repo):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    wrong_owner_id = uuid.uuid4()
    
    mock_model = RegisteredModel(id=model_id, owner_id=wrong_owner_id)
    mock_model_repo.get_by_id.return_value = mock_model
    
    obs_in = MonitoringObservationCreate(
        model_id=model_id,
        observed_at=datetime.now(timezone.utc)
    )
    
    with pytest.raises(HTTPException) as exc:
        service.create_observation(model_id, obs_in, owner_id=owner_id)
        
    assert exc.value.status_code == 404

def test_get_observation_success(service, mock_obs_repo, mock_model_repo):
    obs_id = uuid.uuid4()
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    mock_obs = MonitoringObservation(id=obs_id, model_id=model_id)
    mock_obs_repo.get_by_id.return_value = mock_obs
    
    mock_model = RegisteredModel(id=model_id, owner_id=owner_id)
    mock_model_repo.get_by_id.return_value = mock_model
    
    result = service.get_observation(obs_id, owner_id=owner_id)
    
    mock_obs_repo.get_by_id.assert_called_once_with(obs_id)
    mock_model_repo.get_by_id.assert_called_once_with(model_id)
    assert result == mock_obs

def test_get_nonexistent_observation(service, mock_obs_repo):
    obs_id = uuid.uuid4()
    mock_obs_repo.get_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        service.get_observation(obs_id)
        
    assert exc.value.status_code == 404

def test_get_another_users_observation(service, mock_obs_repo, mock_model_repo):
    obs_id = uuid.uuid4()
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    wrong_owner_id = uuid.uuid4()
    
    mock_obs = MonitoringObservation(id=obs_id, model_id=model_id)
    mock_obs_repo.get_by_id.return_value = mock_obs
    
    mock_model = RegisteredModel(id=model_id, owner_id=wrong_owner_id)
    mock_model_repo.get_by_id.return_value = mock_model
    
    with pytest.raises(HTTPException) as exc:
        service.get_observation(obs_id, owner_id=owner_id)
        
    assert exc.value.status_code == 404

def test_list_observations_owned_model(service, mock_obs_repo, mock_model_repo):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    mock_model = RegisteredModel(id=model_id, owner_id=owner_id)
    mock_model_repo.get_by_id.return_value = mock_model
    
    expected_list = [MonitoringObservation(), MonitoringObservation()]
    mock_obs_repo.list_by_model.return_value = expected_list
    
    result = service.list_observations(model_id, skip=10, limit=20, owner_id=owner_id)
    
    mock_model_repo.get_by_id.assert_called_once_with(model_id)
    mock_obs_repo.list_by_model.assert_called_once_with(model_id, skip=10, limit=20)
    assert result == expected_list

def test_list_observations_another_users_model(service, mock_model_repo):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    wrong_owner_id = uuid.uuid4()
    
    mock_model = RegisteredModel(id=model_id, owner_id=wrong_owner_id)
    mock_model_repo.get_by_id.return_value = mock_model
    
    with pytest.raises(HTTPException) as exc:
        service.list_observations(model_id, owner_id=owner_id)
        
    assert exc.value.status_code == 404

def test_delete_observation_success(service, mock_obs_repo, mock_model_repo):
    obs_id = uuid.uuid4()
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    
    mock_obs = MonitoringObservation(id=obs_id, model_id=model_id)
    mock_obs_repo.get_by_id.return_value = mock_obs
    
    mock_model = RegisteredModel(id=model_id, owner_id=owner_id)
    mock_model_repo.get_by_id.return_value = mock_model
    
    service.delete_observation(obs_id, owner_id=owner_id)
    
    mock_obs_repo.delete.assert_called_once_with(obs_id)

def test_delete_nonexistent_observation(service, mock_obs_repo):
    obs_id = uuid.uuid4()
    mock_obs_repo.get_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        service.delete_observation(obs_id)
        
    assert exc.value.status_code == 404

def test_delete_another_users_observation(service, mock_obs_repo, mock_model_repo):
    obs_id = uuid.uuid4()
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    wrong_owner_id = uuid.uuid4()
    
    mock_obs = MonitoringObservation(id=obs_id, model_id=model_id)
    mock_obs_repo.get_by_id.return_value = mock_obs
    
    mock_model = RegisteredModel(id=model_id, owner_id=wrong_owner_id)
    mock_model_repo.get_by_id.return_value = mock_model
    
    with pytest.raises(HTTPException) as exc:
        service.delete_observation(obs_id, owner_id=owner_id)
        
    assert exc.value.status_code == 404
