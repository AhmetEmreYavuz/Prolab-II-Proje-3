# services/glucose.py
from datetime import datetime, date
from utils.db import db_cursor
from zoneinfo import ZoneInfo



def add_glucose(patient_id: int, value: float,
                when: datetime | None = None) -> int:
    """Yeni ölçüm ekler, eklenen satırın ID'sini döndürür."""
    # Eğer dışarıdan datetime verilmediyse, Europe/Istanbul TZ’li zamanı kullan
    when = when or datetime.now(ZoneInfo("Europe/Istanbul"))

    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO glucose_readings (patient_id, reading_dt, value_mg_dl) "
            "VALUES (%s, %s, %s)",
            (patient_id, when, value),
        )
        return cur.lastrowid



def list_today(patient_id: int) -> list[dict]:
    """Bugünkü ölçümleri döndürür."""
    today = date.today()
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, reading_dt, value_mg_dl "
            "FROM glucose_readings "
            "WHERE patient_id=%s AND DATE(reading_dt)=%s "
            "ORDER BY reading_dt",
            (patient_id, today),
        )
        return cur.fetchall()