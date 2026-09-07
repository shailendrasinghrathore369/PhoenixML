import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator

class MonitoringObservationBase(BaseModel):
    model_id: uuid.UUID
    observed_at: datetime
    
    prediction_count: int = Field(default=0, ge=0)
    positive_prediction_count: int = Field(default=0, ge=0)
    negative_prediction_count: int = Field(default=0, ge=0)
    
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)
    precision: Optional[float] = Field(None, ge=0.0, le=1.0)
    recall: Optional[float] = Field(None, ge=0.0, le=1.0)
    f1_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    @model_validator(mode='after')
    def validate_prediction_consistency(self):
        if self.positive_prediction_count + self.negative_prediction_count > self.prediction_count:
            raise ValueError('positive and negative predictions cannot exceed total prediction count')
        return self

    @model_validator(mode='after')
    def validate_timezone_aware(self):
        if self.observed_at.tzinfo is None:
            raise ValueError('observed_at must be timezone-aware')
        return self

class MonitoringObservationCreate(MonitoringObservationBase):
    pass

class MonitoringObservationRead(MonitoringObservationBase):
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
