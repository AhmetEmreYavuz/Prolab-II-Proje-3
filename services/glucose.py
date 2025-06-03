# services/glucose.py
from __future__ import annotations

from datetime import datetime, date
from zoneinfo import ZoneInfo
from utils.db import db_cursor
from datetime import date

def add_glucose(
    patient_id: int,
    value: float,
    when: datetime | None = None,
) -> int:

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


def list_today(patient_id: int) -> list[dict]:

    today = date.today()
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, reading_dt, value_mg_dl "
            "FROM glucose_readings "
            "WHERE patient_id=%s AND DATE(reading_dt)=%s "
            "ORDER BY reading_dt",
            (patient_id, today),
        )
        rows = cur.fetchall()
        return rows or []

def list_for_date(patient_id: int, day: date) -> list[dict]:

    with db_cursor() as cur:
        cur.execute(
            "SELECT id, reading_dt, value_mg_dl "
            "FROM glucose_readings "
            "WHERE patient_id=%s AND DATE(reading_dt)=%s "
            "ORDER BY reading_dt",
            (patient_id, day),
        )
        return cur.fetchall()