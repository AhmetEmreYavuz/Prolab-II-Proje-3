from datetime import date
from utils.db import db_cursor

def upsert_status(patient_id: int,
                  diet_type: str, diet_done: bool,
                  ex_type: str,   ex_done: bool,
                  day: date | None = None):
    """
    Günlük diyet / egzersiz durumunu ekler veya günceller.
    """
    day = day or date.today()
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO daily_status
            (patient_id, day, diet_type, diet_done, exercise_type, exercise_done)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              diet_type=VALUES(diet_type),
              diet_done=VALUES(diet_done),
              exercise_type=VALUES(exercise_type),
              exercise_done=VALUES(exercise_done)
        """, (patient_id, day, diet_type, diet_done, ex_type, ex_done))
