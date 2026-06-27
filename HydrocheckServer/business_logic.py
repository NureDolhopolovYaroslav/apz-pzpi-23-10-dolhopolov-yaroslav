# business_logic.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Optional
import statistics

from models import Measurement, Alert, Threshold


def calculate_water_quality_index(measurement: dict) -> float:
    """Розраховує індекс якості води (WQI)"""
    wqi = 100
    if measurement.get('ph'):
        wqi -= abs(7.0 - measurement['ph']) * 5
    if measurement.get('temperature'):
        wqi -= max(0, measurement['temperature'] - 20) * 0.5
    if measurement.get('nitrates'):
        wqi -= min(measurement['nitrates'] * 2, 30)
    return max(0, min(100, wqi))


async def check_thresholds(db: Session, measurement: Measurement):
    """Перевіряє порогові значення та створює сповіщення"""
    thresholds = db.query(Threshold).filter(Threshold.parameter.in_([
        "ph", "temperature", "turbidity", "oxygen", "nitrates"
    ])).all()

    measurement_dict = {
        "ph": measurement.ph,
        "temperature": measurement.temperature,
        "turbidity": measurement.turbidity,
        "oxygen": measurement.oxygen,
        "nitrates": measurement.nitrates
    }

    alerts_created = []

    for threshold in thresholds:
        value = measurement_dict.get(threshold.parameter)
        if value is None:
            continue

        message = None

        if threshold.min_value is not None and value < threshold.min_value:
            message = f"{threshold.parameter} ({value}) нижче мінімального порогу ({threshold.min_value})"
        elif threshold.max_value is not None and value > threshold.max_value:
            message = f"{threshold.parameter} ({value}) вище максимального порогу ({threshold.max_value})"

        if message:
            alert = Alert(
                device_id=measurement.device_id,
                measurement_id=measurement.id,
                parameter=threshold.parameter,
                value=value,
                message=message,
                severity=threshold.severity,
                status="active"
            )
            alerts_created.append(alert)
            db.add(alert)

    if alerts_created:
        db.commit()

    return alerts_created

def calculate_average_values(db: Session, device_id: int, hours: int = 24) -> Dict:
    """
    Розрахувати середні значення для пристрою за останні N годин
    """
    time_threshold = datetime.utcnow() - timedelta(hours=hours)

    measurements = db.query(Measurement).filter(
        Measurement.device_id == device_id,
        Measurement.recorded_at >= time_threshold
    ).all()

    if not measurements:
        return {
            "device_id": device_id,
            "measurement_count": 0,
            "time_period_hours": hours
        }

    # Збираємо всі значення
    ph_values = [m.ph for m in measurements if m.ph is not None]
    temp_values = [m.temperature for m in measurements if m.temperature is not None]
    turbidity_values = [m.turbidity for m in measurements if m.turbidity is not None]
    oxygen_values = [m.oxygen for m in measurements if m.oxygen is not None]
    nitrates_values = [m.nitrates for m in measurements if m.nitrates is not None]

    result = {
        "device_id": device_id,
        "ph_avg": statistics.mean(ph_values) if ph_values else None,
        "temp_avg": statistics.mean(temp_values) if temp_values else None,
        "turbidity_avg": statistics.mean(turbidity_values) if turbidity_values else None,
        "oxygen_avg": statistics.mean(oxygen_values) if oxygen_values else None,
        "nitrates_avg": statistics.mean(nitrates_values) if nitrates_values else None,
        "measurement_count": len(measurements),
        "time_period_hours": hours
    }

    return result


def predict_ph_trend(db: Session, device_id: int) -> Optional[float]:
    """
    Простий прогноз pH на наступну годину (середнє останніх 3 вимірювань)
    """
    time_threshold = datetime.utcnow() - timedelta(hours=6)

    measurements = db.query(Measurement).filter(
        Measurement.device_id == device_id,
        Measurement.recorded_at >= time_threshold,
        Measurement.ph.isnot(None)
    ).order_by(Measurement.recorded_at.desc()).limit(3).all()

    if len(measurements) < 2:
        return None

    ph_values = [m.ph for m in measurements]
    return statistics.mean(ph_values)


def get_trend_analysis(db: Session, device_id: int, parameter: str, hours: int = 24) -> Dict:
    """
    Аналіз тренду параметра (збільшується, зменшується, стабільний)
    """
    time_threshold = datetime.utcnow() - timedelta(hours=hours)

    measurements = db.query(Measurement).filter(
        Measurement.device_id == device_id,
        Measurement.recorded_at >= time_threshold,
        getattr(Measurement, parameter).isnot(None)
    ).order_by(Measurement.recorded_at).all()

    if len(measurements) < 3:
        return {"trend": "insufficient_data", "message": "Недостатньо даних для аналізу"}

    values = [getattr(m, parameter) for m in measurements]

    # Простий аналіз тренду
    first_half = values[:len(values) // 2]
    second_half = values[len(values) // 2:]

    avg_first = statistics.mean(first_half)
    avg_second = statistics.mean(second_half)

    if avg_second > avg_first * 1.1:
        trend = "increasing"
    elif avg_second < avg_first * 0.9:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "parameter": parameter,
        "trend": trend,
        "first_half_avg": round(avg_first, 2),
        "second_half_avg": round(avg_second, 2),
        "measurements_count": len(values),
        "change_percentage": round(((avg_second - avg_first) / avg_first * 100) if avg_first != 0 else 0, 2)
    }