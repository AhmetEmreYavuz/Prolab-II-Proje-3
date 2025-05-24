# services/glucose.py
from __future__ import annotations

from datetime import datetime, date
from zoneinfo import ZoneInfo
from utils.db import db_cursor
from datetime import date


# --------------------------------------------------------------------------- #
#  E  K  L  E  M  E
# --------------------------------------------------------------------------- #
def add_glucose(
    patient_id: int,
    value: float,
    when: datetime | None = None,
) -> int:
    """
    Verilen hastaya yeni glukoz ölçümü ekler ve eklenen satırın ID’sini döndürür.

    Parameters
    ----------
    patient_id : int
        Hastanın `users.id` / `patients.id` değeri.
    value : float
        Ölçüm sonucu (mg/dL).
    when : datetime | None
        Ölçümün yapıldığı tarih-saat.  `None` ise Europe/Istanbul saat diliminde
        **şu an** kullanılır.

    Returns
    -------
    int
        `glucose_readings.id` (auto-increment) – eklenen satırın birincil anahtarı
    """
    when = when or datetime.now(ZoneInfo("Europe/Istanbul"))

    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO glucose_readings (patient_id, reading_dt, value_mg_dl)
            VALUES (%s, %s, %s)
            """,
            (patient_id, when, value),
        )
        return cur.lastrowid


# --------------------------------------------------------------------------- #
#  B  U  G  Ü  N  K  Ü   Ö  L  Ç  Ü  M  L  E  R
# --------------------------------------------------------------------------- #
def list_today(patient_id: int) -> list[dict]:
    """Bugünkü (TZ:+03:00) ölçümleri döndürür."""
    today = date.today()
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, reading_dt, value_mg_dl "
            "FROM glucose_readings "
            "WHERE patient_id=%s AND DATE(reading_dt)=%s "
            "ORDER BY reading_dt",
            (patient_id, today),
        )
        rows = cur.fetchall()        # <-- None dönebilir
        return rows or []

def list_for_date(patient_id: int, day: date) -> list[dict]:
    """Verilen güne ait tüm ölçümleri (sıralı) getirir."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, reading_dt, value_mg_dl "
            "FROM glucose_readings "
            "WHERE patient_id=%s AND DATE(reading_dt)=%s "
            "ORDER BY reading_dt",
            (patient_id, day),
        )
        return cur.fetchall()