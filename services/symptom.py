
from utils.db import db_cursor
import re

# ────────────────────────── CRUD ────────────────────────── #
def add_symptom(patient_id: int, description: str, severity: str | None):

    clean_desc = re.sub(r"\s*\([^)]*\)", "", description).strip()

    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO symptoms (patient_id, description, severity) "
            "VALUES (%s, %s, %s)",
            (patient_id, clean_desc, severity)
        )

def remove_symptom(patient_id: int, description: str):

    with db_cursor() as cur:
        cur.execute(
            """
            DELETE s
            FROM symptoms AS s
            JOIN (
                SELECT id
                FROM symptoms
                WHERE patient_id = %s AND description = %s
                ORDER BY noted_at DESC
                LIMIT 1
            ) AS x ON x.id = s.id
            """,
            (patient_id, description)
        )

def list_symptoms(patient_id: int) -> list[str]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT description FROM symptoms "
            "WHERE patient_id=%s ORDER BY noted_at ASC",
            (patient_id,)
        )
        return [r["description"] for r in cur.fetchall()]


def list_today(patient_id: int) -> list[str]:

    from datetime import date
    with db_cursor() as cur:
        cur.execute(
            "SELECT description FROM symptoms "
            "WHERE patient_id=%s AND DATE(noted_at)=%s",
            (patient_id, date.today())
        )
        return [row["description"].lower() for row in cur.fetchall()]

