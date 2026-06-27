# schemas.py
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List


# Схеми для користувачів

class AdminUserCreate(BaseModel):
    """Схема для створення користувача адміном"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field("viewer", description="admin, operator, viewer")
    phone: Optional[str] = None


class UserCreate(BaseModel):
    """Стара схема (може знадобитися для внутрішнього використання)"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "viewer"
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRole(BaseModel):
    role: str = Field(..., description="admin, operator, viewer")


# Схеми для зон

class ZoneCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    zone_type: str = Field(..., description="water_supply, reservoir, river, lake, household")
    location: Optional[str] = None
    description: Optional[str] = None


class ZoneResponse(BaseModel):
    id: int
    name: str
    zone_type: str
    location: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Схеми для пристроїв

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    location: Optional[str] = None
    device_type: Optional[str] = None
    zone_id: Optional[int] = None


class DeviceResponse(BaseModel):
    id: int
    name: str
    api_key: str
    location: Optional[str]
    device_type: Optional[str]
    status: str
    user_id: int
    zone_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# Схеми для вимірювань

class MeasurementCreate(BaseModel):
    ph: Optional[float] = Field(None, ge=0, le=14, description="pH value (0-14)")
    temperature: Optional[float] = Field(None, ge=-50, le=100, description="Temperature in °C")
    turbidity: Optional[float] = Field(None, ge=0, description="Turbidity in NTU")
    oxygen: Optional[float] = Field(None, ge=0, description="Oxygen in mg/L")
    nitrates: Optional[float] = Field(None, ge=0, description="Nitrates in mg/L")


class MeasurementResponse(BaseModel):
    id: int
    device_id: int
    recorded_at: datetime
    ph: Optional[float]
    temperature: Optional[float]
    turbidity: Optional[float]
    oxygen: Optional[float]
    nitrates: Optional[float]
    water_quality_index: Optional[float]

    class Config:
        from_attributes = True


# Схеми для порогових значень

class ThresholdCreate(BaseModel):
    parameter: str = Field(..., description="ph, temperature, turbidity, oxygen, nitrates")
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    severity: str = Field("warning", description="info, warning, critical")
    description: Optional[str] = None


class ThresholdResponse(BaseModel):
    id: int
    parameter: str
    min_value: Optional[float]
    max_value: Optional[float]
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True


# Схеми для сповіщень

class AlertResponse(BaseModel):
    id: int
    device_id: int
    parameter: str
    value: float
    message: str
    severity: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Схеми для статистики

class StatsResponse(BaseModel):
    total_devices: int
    total_measurements: int
    active_alerts: int
    avg_water_quality: Optional[float]


# Схеми для аналітики

class AverageValuesResponse(BaseModel):
    device_id: int
    ph_avg: Optional[float]
    temp_avg: Optional[float]
    turbidity_avg: Optional[float]
    oxygen_avg: Optional[float]
    nitrates_avg: Optional[float]
    measurement_count: int
    time_period_hours: int


class SystemHealthResponse(BaseModel):
    total_devices: int
    active_devices: int
    inactive_devices: int
    measurements_last_hour: int
    health_score: float
    timestamp: datetime