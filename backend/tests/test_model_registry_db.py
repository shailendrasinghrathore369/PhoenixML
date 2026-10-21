import pytest
import uuid
from app.users.models import User, UserRole
from app.models.models import RegisteredModel, ModelStatus
from app.models.schemas import ModelCreate, ModelUpdate
from app.models.repository import RegisteredModelRepository
from app.users.repository import UserRepository
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

def test_create_registered_model(db_session):
    # Setup User
    user_repo = UserRepository(db_session)
    from app.users.schemas import UserCreate
    user_in = UserCreate(full_name='Test User', email='test@example.com', username='testuser', password='password')
    user = user_repo.create_user(user_in, 'hashed')
    
    # Test Model Creation
    repo = RegisteredModelRepository(db_session)
    model_in = ModelCreate(name='MyModel', framework='scikit-learn')
    model = repo.create(model_in, owner_id=user.id)
    
    assert model.id is not None
    assert isinstance(model.id, uuid.UUID)
    assert model.name == 'MyModel'
    assert model.framework == 'scikit-learn'
    assert model.status == ModelStatus.DEVELOPMENT
    assert model.owner_id == user.id
    assert model.created_at is not None
    assert model.updated_at is not None

def test_get_by_id(db_session):
    user_repo = UserRepository(db_session)
    from app.users.schemas import UserCreate
    user_in = UserCreate(full_name='Test User 2', email='test2@example.com', username='testuser2', password='password')
    user = user_repo.create_user(user_in, 'hashed')
    
    repo = RegisteredModelRepository(db_session)
    model = repo.create(ModelCreate(name='GetModel', framework='TensorFlow'), owner_id=user.id)
    
    fetched = repo.get_by_id(model.id)
    assert fetched is not None
    assert fetched.id == model.id
    assert fetched.name == 'GetModel'

def test_list_models(db_session):
    user_repo = UserRepository(db_session)
    from app.users.schemas import UserCreate
    user_in = UserCreate(full_name='Test User 3', email='test3@example.com', username='testuser3', password='password')
    user = user_repo.create_user(user_in, 'hashed')
    
    repo = RegisteredModelRepository(db_session)
    repo.create(ModelCreate(name='Model1', framework='PyTorch'), owner_id=user.id)
    repo.create(ModelCreate(name='Model2', framework='PyTorch'), owner_id=user.id)
    
    models = repo.list(owner_id=user.id)
    assert len(models) == 2

def test_update_model(db_session):
    user_repo = UserRepository(db_session)
    from app.users.schemas import UserCreate
    user_in = UserCreate(full_name='Test User 4', email='test4@example.com', username='testuser4', password='password')
    user = user_repo.create_user(user_in, 'hashed')
    
    repo = RegisteredModelRepository(db_session)
    model = repo.create(ModelCreate(name='UpdateModel', framework='scikit-learn'), owner_id=user.id)
    
    updated = repo.update(model, ModelUpdate(status=ModelStatus.ACTIVE, description='Updated'))
    assert updated.status == ModelStatus.ACTIVE
    assert updated.description == 'Updated'
    assert updated.name == 'UpdateModel'

def test_delete_model(db_session):
    user_repo = UserRepository(db_session)
    from app.users.schemas import UserCreate
    user_in = UserCreate(full_name='Test User 5', email='test5@example.com', username='testuser5', password='password')
    user = user_repo.create_user(user_in, 'hashed')
    
    repo = RegisteredModelRepository(db_session)
    model = repo.create(ModelCreate(name='DeleteModel', framework='scikit-learn'), owner_id=user.id)
    
    repo.delete(model)
    fetched = repo.get_by_id(model.id)
    assert fetched is None

def test_invalid_owner_rejected(db_session):
    repo = RegisteredModelRepository(db_session)
    model_in = ModelCreate(name='NoOwnerModel', framework='scikit-learn')
    with pytest.raises(IntegrityError):
        repo.create(model_in, owner_id=uuid.uuid4())

def test_model_owner_relationship(db_session):
    user_repo = UserRepository(db_session)
    from app.users.schemas import UserCreate
    user_in = UserCreate(full_name='Rel User', email='rel@example.com', username='reluser', password='password')
    user = user_repo.create_user(user_in, 'hashed')
    
    repo = RegisteredModelRepository(db_session)
    model = repo.create(ModelCreate(name='RelModel', framework='scikit-learn'), owner_id=user.id)
    
    assert model.owner == user
    assert model in user.models

def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        ModelCreate(name='InvalidStatusModel', framework='scikit-learn', status='INVALID_STATUS')
