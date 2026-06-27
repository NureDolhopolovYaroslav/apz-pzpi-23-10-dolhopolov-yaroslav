# admin_functions.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import csv
from io import StringIO

from models import User, Device, Measurement, Alert


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Отримати всіх користувачів з пагінацією"""
    return db.query(User).offset(skip).limit(limit).all()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Знайти користувача за ID"""
    return db.query(User).filter(User.id == user_id).first()


def change_user_role(db: Session, user_id: int, new_role: str) -> User:
    """Змінити роль користувача"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    allowed_roles = ["admin", "operator", "viewer"]
    if new_role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Дозволені ролі: {', '.join(allowed_roles)}"
        )

    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> Dict:
    """Видалити користувача та пов'язані дані"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    # Перевіряємо, чи є у користувача пристрої
    user_devices = db.query(Device).filter(Device.user_id == user_id).count()
    if user_devices > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Неможливо видалити користувача. У нього є {user_devices} пристроїв."
        )

    # Перевіряємо, чи користувач створив порогові значення
    user_thresholds = db.query(User).filter(User.id == user_id).first()
    if user_thresholds and user_thresholds.thresholds:
        raise HTTPException(
            status_code=400,
            detail="Неможливо видалити користувача. Він створив порогові значення."
        )

    db.delete(user)
    db.commit()

    return {
        "message": "Користувача успішно видалено",
        "user_id": user_id,
        "username": user.username
    }


def get_system_logs(db: Session, hours: int = 24) -> Dict:
    """Отримати лог активності системи за останні N годин"""
    time_threshold = datetime.utcnow() - timedelta(hours=hours)

    # Статистика вимірювань
    measurements_count = db.query(Measurement).filter(
        Measurement.recorded_at >= time_threshold
    ).count()

    # Статистика сповіщень
    alerts_count = db.query(Alert).filter(
        Alert.created_at >= time_threshold
    ).count()

    # Активні пристрої
    active_devices = db.query(Device).filter(Device.status == "active").count()
    total_devices = db.query(Device).count()

    # Останні 10 сповіщень
    recent_alerts = db.query(Alert).filter(
        Alert.created_at >= time_threshold
    ).order_by(Alert.created_at.desc()).limit(10).all()

    # Останні 10 вимірювань
    recent_measurements = db.query(Measurement).filter(
        Measurement.recorded_at >= time_threshold
    ).order_by(Measurement.recorded_at.desc()).limit(10).all()

    return {
        "time_period_hours": hours,
        "measurements_count": measurements_count,
        "alerts_count": alerts_count,
        "active_devices": active_devices,
        "total_devices": total_devices,
        "device_activity_percentage": round((active_devices / total_devices * 100) if total_devices > 0 else 0, 1),
        "recent_alerts": [
            {
                "id": alert.id,
                "device_id": alert.device_id,
                "parameter": alert.parameter,
                "severity": alert.severity,
                "created_at": alert.created_at
            }
            for alert in recent_alerts
        ],
        "recent_measurements": [
            {
                "id": m.id,
                "device_id": m.device_id,
                "ph": m.ph,
                "temperature": m.temperature,
                "recorded_at": m.recorded_at
            }
            for m in recent_measurements
        ]
    }


def export_data_to_csv(db: Session, data_type: str, **filters) -> str:
    """Експорт даних у формат CSV"""
    output = StringIO()
    writer = csv.writer(output)

    if data_type == "measurements":
        query = db.query(Measurement)

        # Застосовуємо фільтри
        if "device_id" in filters:
            query = query.filter(Measurement.device_id == filters["device_id"])
        if "start_date" in filters:
            query = query.filter(Measurement.recorded_at >= filters["start_date"])
        if "end_date" in filters:
            query = query.filter(Measurement.recorded_at <= filters["end_date"])

        measurements = query.order_by(Measurement.recorded_at).all()

        # Заголовки
        writer.writerow([
            "ID", "Device ID", "Timestamp", "pH", "Temperature (°C)",
            "Turbidity (NTU)", "Oxygen (mg/L)", "Nitrates (mg/L)",
            "Water Quality Index"
        ])

        # Дані
        for m in measurements:
            writer.writerow([
                m.id, m.device_id, m.recorded_at,
                m.ph, m.temperature, m.turbidity,
                m.oxygen, m.nitrates, m.water_quality_index
            ])

    elif data_type == "alerts":
        query = db.query(Alert)

        if "status" in filters:
            query = query.filter(Alert.status == filters["status"])
        if "severity" in filters:
            query = query.filter(Alert.severity == filters["severity"])

        alerts = query.order_by(Alert.created_at.desc()).all()

        writer.writerow([
            "ID", "Device ID", "Parameter", "Value", "Severity",
            "Message", "Status", "Created At", "Resolved At"
        ])

        for a in alerts:
            writer.writerow([
                a.id, a.device_id, a.parameter, a.value,
                a.severity, a.message, a.status,
                a.created_at, a.resolved_at
            ])

    elif data_type == "devices":
        devices = db.query(Device).all()

        writer.writerow([
            "ID", "Name", "Type", "Location", "Status",
            "Owner ID", "Zone ID", "Created At"
        ])

        for d in devices:
            writer.writerow([
                d.id, d.name, d.device_type, d.location,
                d.status, d.user_id, d.zone_id, d.created_at
            ])

    return output.getvalue()


def cleanup_old_data(db: Session, days: int = 30) -> Dict:
    """Очистити старі дані"""
    time_threshold = datetime.utcnow() - timedelta(days=days)

    # Видалити старі вимірювання
    old_measurements = db.query(Measurement).filter(
        Measurement.recorded_at < time_threshold
    ).delete(synchronize_session=False)

    # Видалити вирішені сповіщення
    resolved_alerts = db.query(Alert).filter(
        Alert.status == "resolved",
        Alert.created_at < time_threshold
    ).delete(synchronize_session=False)

    db.commit()

    return {
        "deleted_measurements": old_measurements,
        "deleted_resolved_alerts": resolved_alerts,
        "older_than_days": days,
        "cleanup_date": datetime.utcnow()
    }


def get_system_health(db: Session) -> Dict:
    """Отримати стан здоров'я системи"""
    total_devices = db.query(Device).count()
    active_devices = db.query(Device).filter(Device.status == "active").count()

    last_hour = datetime.utcnow() - timedelta(hours=1)
    measurements_last_hour = db.query(Measurement).filter(
        Measurement.recorded_at >= last_hour
    ).count()

    active_alerts = db.query(Alert).filter(Alert.status == "active").count()

    # Перевірка проблемних пристроїв
    problem_devices = []
    devices = db.query(Device).all()

    for device in devices:
        # Перевіряємо, чи були вимірювання за останню годину
        last_measurement = db.query(Measurement).filter(
            Measurement.device_id == device.id
        ).order_by(Measurement.recorded_at.desc()).first()

        if last_measurement:
            time_since_last = datetime.utcnow() - last_measurement.recorded_at
            if time_since_last > timedelta(hours=2) and device.status == "active":
                problem_devices.append({
                    "device_id": device.id,
                    "name": device.name,
                    "last_measurement": last_measurement.recorded_at,
                    "hours_since": round(time_since_last.total_seconds() / 3600, 1)
                })

    return {
        "total_devices": total_devices,
        "active_devices": active_devices,
        "inactive_devices": total_devices - active_devices,
        "measurements_last_hour": measurements_last_hour,
        "active_alerts": active_alerts,
        "health_score": round((active_devices / total_devices * 100) if total_devices > 0 else 0, 1),
        "problem_devices": problem_devices,
        "problem_devices_count": len(problem_devices),
        "timestamp": datetime.utcnow()
    }