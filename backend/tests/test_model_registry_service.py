import pytest
import uuid
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.models.service import RegisteredModelService
from app.models.schemas import ModelCreate, ModelUpdate
from app.models.models import RegisteredModel, ModelStatus

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def service(mock_repo):
    # Pass None for db since we mock the repo
    svc = RegisteredModelService(db=None)
    svc.repo = mock_repo
    return svc

def test_create_model(service, mock_repo):
    owner_id = uuid.uuid4()
    model_in = ModelCreate(name='TestModel', framework='scikit-learn')
    expected_model = RegisteredModel(id=uuid.uuid4(), name='TestModel', owner_id=owner_id)
    mock_repo.create.return_value = expected_model

    result = service.create_model(model_in, owner_id)
    
    mock_repo.create.assert_called_once_with(model_in, owner_id=owner_id)
    assert result == expected_model

def test_get_model_success(service, mock_repo):
    model_id = uuid.uuid4()
    expected_model = RegisteredModel(id=model_id, owner_id=uuid.uuid4())
    mock_repo.get_by_id.return_value = expected_model

    result = service.get_model(model_id)
    
    mock_repo.get_by_id.assert_called_once_with(model_id)
    assert result == expected_model

def test_get_model_not_found(service, mock_repo):
    model_id = uuid.uuid4()
    mock_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        service.get_model(model_id)
        
    assert exc.value.status_code == 404
    assert exc.value.detail == 'Model not found'

def test_get_model_wrong_owner(service, mock_repo):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    wrong_owner_id = uuid.uuid4()
    expected_model = RegisteredModel(id=model_id, owner_id=owner_id)
    mock_repo.get_by_id.return_value = expected_model

    with pytest.raises(HTTPException) as exc:
        service.get_model(model_id, owner_id=wrong_owner_id)
        
    assert exc.value.status_code == 404
    assert exc.value.detail == 'Model not found'

def test_list_models(service, mock_repo):
    owner_id = uuid.uuid4()
    expected_models = [RegisteredModel(), RegisteredModel()]
    mock_repo.list.return_value = expected_models

    result = service.list_models(skip=10, limit=5, owner_id=owner_id)
    
    mock_repo.list.assert_called_once_with(skip=10, limit=5, owner_id=owner_id)
    assert result == expected_models

def test_update_model(service, mock_repo):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    model_in = ModelUpdate(status=ModelStatus.ACTIVE)
    
    existing_model = RegisteredModel(id=model_id, owner_id=owner_id)
    updated_model = RegisteredModel(id=model_id, owner_id=owner_id, status=ModelStatus.ACTIVE)
    
    mock_repo.get_by_id.return_value = existing_model
    mock_repo.update.return_value = updated_model

    result = service.update_model(model_id, model_in, owner_id=owner_id)
    
    mock_repo.get_by_id.assert_called_once_with(model_id)
    mock_repo.update.assert_called_once_with(existing_model, model_in)
    assert result == updated_model

def test_delete_model(service, mock_repo):
    model_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    existing_model = RegisteredModel(id=model_id, owner_id=owner_id)
    
    mock_repo.get_by_id.return_value = existing_model

    service.delete_model(model_id, owner_id=owner_id)
    
    mock_repo.get_by_id.assert_called_once_with(model_id)
    mock_repo.delete.assert_called_once_with(existing_model)
