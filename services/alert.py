from datetime import datetime
from utils.db import db_cursor

def add_alert(patient_id: int,
              alert_type: str,
              message: str,
              day: datetime | None = None) -> None:
    """
    alerts tablosuna tek satır ekler. Mevcut yapıya uygun olarak sadece
    patient_id, message ve created_dt alanlarını kullanır.
    """
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO alerts 
              (patient_id, created_dt, message)
            VALUES (%s, NOW(), %s)
        """, (patient_id, message))
