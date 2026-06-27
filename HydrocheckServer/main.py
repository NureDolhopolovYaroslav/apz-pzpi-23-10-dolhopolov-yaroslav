# main.py
from fastapi import FastAPI, Depends, HTTPException, status, Header, Query, Response
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, timedelta
import secrets
from typing import Optional, List

# Імпорт наших модулів
from models import Base, User, Zone, Device, Measurement, Threshold, Alert
from schemas import *
from business_logic import calculate_water_quality_index, check_thresholds, calculate_average_values, predict_ph_trend, \
    get_trend_analysis
from admin_functions import get_all_users, change_user_role, delete_user, get_system_logs, get_system_health, \
    cleanup_old_data, export_data_to_csv

# Налаштування бд
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./water_monitoring.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Створюємо таблиці
Base.metadata.create_all(bind=engine)

# FASTAPI додаток
app = FastAPI(
    title="Water Quality Monitoring API",
    description="REST API для системи моніторингу якості води",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Залежність для отримання сесії бд
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Допоміжна функція
def generate_api_key() -> str:
    """Генерує унікальний API ключ для пристрою"""
    return secrets.token_urlsafe(32)


# Корінь

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Water Quality Monitoring System API",
        "version": "2.0.0",
        "docs": "/docs",
        "admin_endpoints": "/admin/*",
        "analytics_endpoints": "/analytics/*",
        "api_endpoints": "/api/*"
    }


# Адмін ендпоінти для створення користувачів

@app.post("/admin/users/", response_model=UserResponse, tags=["Admin"], status_code=201)
async def admin_create_user(
        user: AdminUserCreate,
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        db: Session = Depends(get_db)
):
    """
    Створити нового користувача (тільки для адміністраторів)
    """
    # Перевірка адмін ключа
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав для створення користувача"
        )

    # Перевірка валідності ролі
    allowed_roles = ["admin", "operator", "viewer"]
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Дозволені ролі: {', '.join(allowed_roles)}"
        )

    # Перевірка, чи користувач вже існує
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()

    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Користувач з таким іменем або email вже існує"
        )

    # Створення користувача
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=user.password,  # Пароль передається адміном
        role=user.role,
        phone=user.phone,
        is_active=True
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.get("/admin/users", response_model=List[UserResponse], tags=["Admin"])
async def admin_get_users(
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        role: Optional[str] = Query(None, description="Фільтр по ролі"),
        db: Session = Depends(get_db)
):
    """
    Отримати список всіх користувачів (тільки для адміністраторів)
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав"
        )

    users = get_all_users(db, skip, limit)

    if role:
        users = [u for u in users if u.role == role]

    return users


@app.patch("/admin/users/{user_id}/role", tags=["Admin"])
async def admin_update_user_role(
        user_id: int,
        role_update: UserUpdateRole,
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        db: Session = Depends(get_db)
):
    """
    Змінити роль користувача
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав"
        )

    user = change_user_role(db, user_id, role_update.role)
    return {
        "message": "Роль успішно оновлено",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    }


@app.delete("/admin/users/{user_id}", tags=["Admin"])
async def admin_delete_user(
        user_id: int,
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        db: Session = Depends(get_db)
):
    """
    Видалити користувача
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав"
        )

    result = delete_user(db, user_id)
    return result


@app.get("/admin/system/logs", tags=["Admin"])
async def admin_get_system_logs(
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        hours: int = Query(24, ge=1, le=168, description="Період у годинах"),
        db: Session = Depends(get_db)
):
    """
    Отримати лог активності системи
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав"
        )

    return get_system_logs(db, hours)


@app.get("/admin/system/health", tags=["Admin"])
async def admin_get_system_health(
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        db: Session = Depends(get_db)
):
    """
    Отримати стан здоров'я системи
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав"
        )

    return get_system_health(db)


@app.post("/admin/system/cleanup", tags=["Admin"])
async def admin_cleanup_old_data(
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        days: int = Query(30, ge=1, le=365, description="Видалити дані старші за N днів"),
        db: Session = Depends(get_db)
):
    """
    Очистити старі дані
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав"
        )

    result = cleanup_old_data(db, days)
    return {
        "message": "Очищення даних виконано",
        **result
    }


@app.get("/admin/export/{data_type}", tags=["Admin"])
async def admin_export_data(
        data_type: str,
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        device_id: Optional[int] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        status: Optional[str] = Query(None),
        severity: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    """
    Експорт даних у CSV формат
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав"
        )

    if data_type not in ["measurements", "alerts", "devices"]:
        raise HTTPException(status_code=400, detail="Невірний тип даних")

    filters = {}
    if device_id:
        filters["device_id"] = device_id
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if status:
        filters["status"] = status
    if severity:
        filters["severity"] = severity

    csv_data = export_data_to_csv(db, data_type, **filters)

    filename = f"{data_type}_export_{datetime.now().date()}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# Аналітика та бізнес-логіка

@app.get("/analytics/average/{device_id}", tags=["Analytics"])
async def get_average_values(
        device_id: int,
        hours: int = Query(24, ge=1, le=720, description="Період у годинах"),
        db: Session = Depends(get_db)
):
    """
    Отримати середні значення параметрів для пристрою
    """
    averages = calculate_average_values(db, device_id, hours)
    return averages


@app.get("/analytics/trend/{device_id}/{parameter}", tags=["Analytics"])
async def get_parameter_trend(
        device_id: int,
        parameter: str,
        hours: int = Query(24, ge=3, le=168, description="Період аналізу у годинах"),
        db: Session = Depends(get_db)
):
    """
    Отримати аналіз тренду параметра
    """
    allowed_params = ["ph", "temperature", "turbidity", "oxygen", "nitrates"]
    if parameter not in allowed_params:
        raise HTTPException(
            status_code=400,
            detail=f"Дозволені параметри: {', '.join(allowed_params)}"
        )

    trend = get_trend_analysis(db, device_id, parameter, hours)
    return trend


@app.get("/analytics/predict/ph/{device_id}", tags=["Analytics"])
async def predict_ph(
        device_id: int,
        db: Session = Depends(get_db)
):
    """
    Прогнозування pH на наступну годину
    """
    predicted_ph = predict_ph_trend(db, device_id)

    if predicted_ph is None:
        raise HTTPException(
            status_code=404,
            detail="Недостатньо даних для прогнозування"
        )

    return {
        "device_id": device_id,
        "predicted_ph": round(predicted_ph, 2),
        "timestamp": datetime.utcnow(),
        "message": "Прогноз на основі останніх вимірювань"
    }


# Публічні ендопінти без аунтифікації

@app.get("/api/stats/", response_model=StatsResponse, tags=["Statistics"])
async def get_statistics(
        user_id: Optional[int] = Query(None, description="ID користувача для фільтра"),
        zone_id: Optional[int] = Query(None, description="ID зони для фільтра"),
        db: Session = Depends(get_db)
):
    """
    Отримати статистику системи (публічний доступ)
    """
    try:
        # Підрахунок пристроїв
        device_query = db.query(Device)
        if user_id is not None:
            device_query = device_query.filter(Device.user_id == user_id)
        if zone_id is not None:
            device_query = device_query.filter(Device.zone_id == zone_id)
        total_devices = device_query.count()

        # Підрахунок вимірювань
        measurement_query = db.query(Measurement)
        if user_id is not None or zone_id is not None:
            measurement_query = measurement_query.join(Device)
            if user_id is not None:
                measurement_query = measurement_query.filter(Device.user_id == user_id)
            if zone_id is not None:
                measurement_query = measurement_query.filter(Device.zone_id == zone_id)
        total_measurements = measurement_query.count()

        # Підрахунок активних сповіщень
        alert_query = db.query(Alert).filter(Alert.status == "active")
        if user_id is not None or zone_id is not None:
            alert_query = alert_query.join(Device)
            if user_id is not None:
                alert_query = alert_query.filter(Device.user_id == user_id)
            if zone_id is not None:
                alert_query = alert_query.filter(Device.zone_id == zone_id)
        active_alerts = alert_query.count()

        # Середній індекс якості води
        wqi_query = db.query(func.avg(Measurement.water_quality_index))
        if user_id is not None or zone_id is not None:
            wqi_query = wqi_query.join(Device)
            if user_id is not None:
                wqi_query = wqi_query.filter(Device.user_id == user_id)
            if zone_id is not None:
                wqi_query = wqi_query.filter(Device.zone_id == zone_id)

        avg_wqi_result = wqi_query.scalar()
        avg_water_quality = round(avg_wqi_result, 2) if avg_wqi_result is not None else None

        return StatsResponse(
            total_devices=total_devices,
            total_measurements=total_measurements,
            active_alerts=active_alerts,
            avg_water_quality=avg_water_quality
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Помилка при отриманні статистики: {str(e)}"
        )


# Ендпоінти для інтеграції з API-ключем

@app.post("/api/iot/measurements/", response_model=MeasurementResponse, tags=["IoT Measurements"], status_code=201)
async def create_measurement_iot(
        measurement: MeasurementCreate,
        api_key: str = Header(..., alias="X-API-Key", description="API ключ пристрою"),
        db: Session = Depends(get_db)
):
    """
    Додати вимірювання від IoT пристрою
    """
    device = db.query(Device).filter(
        Device.api_key == api_key,
        Device.status == "active"
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Невірний або неактивний API ключ"
        )

    wqi = calculate_water_quality_index(measurement.dict())

    db_measurement = Measurement(
        device_id=device.id,
        ph=measurement.ph,
        temperature=measurement.temperature,
        turbidity=measurement.turbidity,
        oxygen=measurement.oxygen,
        nitrates=measurement.nitrates,
        water_quality_index=wqi
    )

    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)

    await check_thresholds(db, db_measurement)
    return db_measurement


# Ендпоінти для перегляду даних

@app.get("/api/devices/{device_id}/measurements/", response_model=List[MeasurementResponse], tags=["Measurements"])
async def get_device_measurements(
        device_id: int,
        start_date: Optional[datetime] = Query(None, description="Початкова дата"),
        end_date: Optional[datetime] = Query(None, description="Кінцева дата"),
        limit: int = Query(100, ge=1, le=1000),
        db: Session = Depends(get_db)
):
    """
    Отримати вимірювання конкретного пристрою
    """
    query = db.query(Measurement).filter(Measurement.device_id == device_id)

    if start_date:
        query = query.filter(Measurement.recorded_at >= start_date)
    if end_date:
        query = query.filter(Measurement.recorded_at <= end_date)

    measurements = query.order_by(Measurement.recorded_at.desc()).limit(limit).all()

    if not measurements:
        raise HTTPException(status_code=404, detail="Вимірювання не знайдено")

    return measurements


@app.get("/api/alerts/", response_model=List[AlertResponse], tags=["Alerts"])
async def get_alerts(
        device_id: Optional[int] = Query(None, description="Фільтр по пристрою"),
        zone_id: Optional[int] = Query(None, description="Фільтр по зоні"),
        status: Optional[str] = Query("active", description="Фільтр по статусу"),
        severity: Optional[str] = Query(None, description="Фільтр по серйозності"),
        db: Session = Depends(get_db)
):
    """
    Отримати список сповіщень
    """
    query = db.query(Alert)

    if device_id:
        query = query.filter(Alert.device_id == device_id)
    if zone_id:
        query = query.join(Device).filter(Device.zone_id == zone_id)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)

    alerts = query.order_by(Alert.created_at.desc()).all()
    return alerts


@app.get("/api/alerts/summary", tags=["Alerts"])
async def get_alerts_summary(
        days: int = Query(7, ge=1, le=30),
        db: Session = Depends(get_db)
):
    """
    Отримати зведену статистику сповіщень
    """
    time_threshold = datetime.utcnow() - timedelta(days=days)

    # Загальна кількість сповіщень
    total_alerts = db.query(Alert).filter(
        Alert.created_at >= time_threshold
    ).count()

    # Сповіщення по статусах
    active_alerts = db.query(Alert).filter(
        Alert.status == "active",
        Alert.created_at >= time_threshold
    ).count()

    resolved_alerts = db.query(Alert).filter(
        Alert.status == "resolved",
        Alert.created_at >= time_threshold
    ).count()

    # Сповіщення по серйозності
    critical_alerts = db.query(Alert).filter(
        Alert.severity == "critical",
        Alert.created_at >= time_threshold
    ).count()

    warning_alerts = db.query(Alert).filter(
        Alert.severity == "warning",
        Alert.created_at >= time_threshold
    ).count()

    info_alerts = db.query(Alert).filter(
        Alert.severity == "info",
        Alert.created_at >= time_threshold
    ).count()

    # Сповіщення по параметрах
    alerts_by_param = {}
    parameters = ["ph", "temperature", "turbidity", "oxygen", "nitrates"]

    for param in parameters:
        count = db.query(Alert).filter(
            Alert.parameter == param,
            Alert.created_at >= time_threshold
        ).count()
        alerts_by_param[param] = count

    return {
        "period_days": days,
        "total_alerts": total_alerts,
        "by_status": {
            "active": active_alerts,
            "resolved": resolved_alerts
        },
        "by_severity": {
            "critical": critical_alerts,
            "warning": warning_alerts,
            "info": info_alerts
        },
        "by_parameter": alerts_by_param,
        "most_common_parameter": max(alerts_by_param, key=alerts_by_param.get) if total_alerts > 0 else None
    }


@app.get("/api/zones/", response_model=List[ZoneResponse], tags=["Zones"])
async def get_zones(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """
    Отримати список зон моніторингу
    """
    zones = db.query(Zone).offset(skip).limit(limit).all()
    return zones


@app.get("/api/devices/", response_model=List[DeviceResponse], tags=["Devices"])
async def get_devices(
        user_id: Optional[int] = Query(None, description="Фільтр по власнику"),
        zone_id: Optional[int] = Query(None, description="Фільтр по зоні"),
        status: Optional[str] = Query(None, description="Фільтр по статусу"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """
    Отримати список пристроїв
    """
    query = db.query(Device)

    if user_id:
        query = query.filter(Device.user_id == user_id)
    if zone_id:
        query = query.filter(Device.zone_id == zone_id)
    if status:
        query = query.filter(Device.status == status)

    devices = query.offset(skip).limit(limit).all()
    return devices


@app.post("/api/zones/", response_model=ZoneResponse, tags=["Zones"], status_code=201)
async def create_zone(
        zone: ZoneCreate,
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        db: Session = Depends(get_db)
):
    """
    Створити нову зону моніторингу
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав для створення зони"
        )

    db_zone = Zone(
        name=zone.name,
        zone_type=zone.zone_type,
        location=zone.location,
        description=zone.description
    )

    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone


@app.post("/api/devices/", response_model=DeviceResponse, tags=["Devices"], status_code=201)
async def create_device(
        device: DeviceCreate,
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        user_id: int = Query(..., description="ID користувача-власника"),
        db: Session = Depends(get_db)
):
    """
    Створити новий пристрій (датчик)
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав для створення пристрою"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    if device.zone_id:
        zone = db.query(Zone).filter(Zone.id == device.zone_id).first()
        if not zone:
            raise HTTPException(status_code=404, detail="Зону не знайдено")

    api_key = generate_api_key()
    db_device = Device(
        name=device.name,
        api_key=api_key,
        location=device.location,
        device_type=device.device_type,
        user_id=user_id,
        zone_id=device.zone_id
    )

    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@app.post("/api/thresholds/", response_model=ThresholdResponse, tags=["Thresholds"], status_code=201)
async def create_threshold(
        threshold: ThresholdCreate,
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        user_id: int = Query(..., description="ID користувача, який створює"),
        db: Session = Depends(get_db)
):
    """
    Створити порогове значення
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав для створення порогів"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    db_threshold = Threshold(
        parameter=threshold.parameter,
        min_value=threshold.min_value,
        max_value=threshold.max_value,
        severity=threshold.severity,
        description=threshold.description,
        created_by=user_id
    )

    db.add(db_threshold)
    db.commit()
    db.refresh(db_threshold)
    return db_threshold


@app.get("/api/thresholds/", response_model=List[ThresholdResponse], tags=["Thresholds"])
async def get_thresholds(
        parameter: Optional[str] = Query(None, description="Фільтр по параметру"),
        db: Session = Depends(get_db)
):
    """
    Отримати список порогових значень
    """
    query = db.query(Threshold)

    if parameter:
        query = query.filter(Threshold.parameter == parameter)

    thresholds = query.order_by(Threshold.parameter).all()
    return thresholds


@app.patch("/api/alerts/{alert_id}/resolve/", tags=["Alerts"])
async def resolve_alert(
        alert_id: int,
        admin_key: str = Header(..., description="Секретний ключ адміна"),
        db: Session = Depends(get_db)
):
    """
    Позначити сповіщення як вирішене
    """
    if admin_key != "SECRET_ADMIN_KEY_123":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав для зміни статусу сповіщень"
        )

    alert = db.query(Alert).filter(Alert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Сповіщення не знайдено")

    if alert.status == "resolved":
        return {"message": "Сповіщення вже вирішено"}

    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()

    db.commit()
    return {"message": "Сповіщення позначено як вирішене", "alert_id": alert_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)