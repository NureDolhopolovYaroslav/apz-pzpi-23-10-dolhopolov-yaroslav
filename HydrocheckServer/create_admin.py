# create_admin.py
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from models import User, Base
from datetime import datetime
import hashlib

DATABASE_URL = "sqlite:///./water_monitoring.db"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


def hash_password(password: str) -> str:
    """Простий хеш пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


def init_admin():
    # Підключення до бд
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Створення таблиць, якщо їх нема
    Base.metadata.create_all(bind=engine)

    # Перевірка, чи є адміни чи нє
    admin_exists = db.query(User).filter(User.role == "admin").first()

    if admin_exists:
        print("Адмін вже існує в системі")
        print(f"Логін: {admin_exists.username}")
        db.close()
        return

    # Створення суперадміна
    admin = User(
        username="superadmin",
        email="admin@watermonitoring.gov.ua",
        password_hash=hash_password("Admin123!"),
        role="admin",
        is_active=True,
        created_at=datetime.utcnow()
    )

    db.add(admin)
    db.commit()

    print("Перший адмін створений успішно!")
    print("Логін: superadmin")
    print("Пароль: Admin123!")

    db.close()


if __name__ == "__main__":
    init_admin()