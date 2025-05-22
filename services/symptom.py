"""Hastalık belirtisi (semptom) ile ilgili veritabanı işlemleri."""
from datetime import datetime
from utils.db import db_cursor


def add_symptom(patient_id: int, description: str, severity: str | None = None,
                noted_at: datetime | None = None):
    """Yeni semptom kaydı ekler."""
    noted_at = noted_at or datetime.now()
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO symptoms (patient_id, noted_at, description, severity)
            VALUES (%s, %s, %s, %s)
            """,
            (patient_id, noted_at, description, severity)
        )


def list_recent(patient_id: int, days: int = 30):
    """Belirtilen hasta için son *days* günlük semptom kayıtlarını döndürür."""
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT noted_at, description, severity
            FROM symptoms
            WHERE patient_id=%s AND noted_at >= NOW() - INTERVAL %s DAY
            ORDER BY noted_at DESC
            """,
            (patient_id, days)
        )
        return cur.fetchall() 