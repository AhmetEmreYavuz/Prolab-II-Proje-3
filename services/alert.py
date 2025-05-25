from datetime import datetime
from utils.db import db_cursor

def add_alert(patient_id: int,
              alert_type: str,
              message: str,
              day: datetime | None = None) -> None:
    """
    alerts tablosuna tek satır ekler. Aynı gün & tip için UNIQUE
    (patient_id, alert_type, day) anahtarıyla tekrarları engeller.
    """
    day = day or datetime.today().date()
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO alerts 
              (patient_id, created_dt, alert_type, message, day)
            VALUES (%s, NOW(), %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              message     = VALUES(message),
              created_dt  = NOW()
        """, (patient_id, alert_type, message, day))
