# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")  # admin, operator, viewer
    is_active = Column(Boolean, default=True)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    devices = relationship("Device", back_populates="owner")
    thresholds = relationship("Threshold", back_populates="creator")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50))  # water_supply, reservoir, river, lake, household
    location = Column(String(255))
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    devices = relationship("Device", back_populates="zone")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    api_key = Column(String(100), unique=True, nullable=False)
    location = Column(String(255))
    device_type = Column(String(50))
    status = Column(String(20), default="active")  # active, inactive, maintenance
    user_id = Column(Integer, ForeignKey("users.id"))
    zone_id = Column(Integer, ForeignKey("zones.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="devices")
    zone = relationship("Zone", back_populates="devices")
    measurements = relationship("Measurement", back_populates="device")
    alerts = relationship("Alert", back_populates="device")


class Measurement(Base):
    __tablename__ = "measurements"
    __table_args__ = (
        CheckConstraint('ph >= 0 AND ph <= 14', name='check_ph_range'),
        CheckConstraint('temperature >= -50 AND temperature <= 100', name='check_temp_range'),
    )

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    recorded_at = Column(DateTime, default=datetime.utcnow)
    ph = Column(Float)  # Водневий показник (0-14)
    temperature = Column(Float)  # Температура (°C)
    turbidity = Column(Float)  # Мутність (NTU)
    oxygen = Column(Float)  # Кисень (mg/L)
    nitrates = Column(Float)  # Нітрати (mg/L)
    water_quality_index = Column(Float)  # Загальний індекс якості

    device = relationship("Device", back_populates="measurements")
    alert = relationship("Alert", back_populates="measurement", uselist=False)


class Threshold(Base):
    __tablename__ = "thresholds"

    id = Column(Integer, primary_key=True, index=True)
    parameter = Column(String(50), nullable=False)  # ph, temperature, etc.
    min_value = Column(Float)
    max_value = Column(Float)
    severity = Column(String(20), default="warning")  # info, warning, critical
    description = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="thresholds")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    measurement_id = Column(Integer, ForeignKey("measurements.id"))
    parameter = Column(String(50))
    value = Column(Float)
    message = Column(String(255))
    severity = Column(String(20))
    status = Column(String(20), default="active")  # active, resolved, acknowledged
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="alerts")
    measurement = relationship("Measurement", back_populates="alert")