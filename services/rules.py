# services/rules.py
"""
Gün sonu ortalama, insülin dozu ve uyarı üretir.
Ham-SQL kullanır.
"""

from datetime import date, datetime
from utils.db import db_cursor

# ---- Sabitler ----
# (type, lo, hi, insulin_dose, diet, exercise)
LEVELS = [
    ("hypo",        0,   69.9, 0, "yüksek_karb", "dinlen"),
    ("normal",     70,  110.0, 0, "balanced",    "yürüyüş"),
    ("mid_high",  111,  150.0, 1, "low_sugar",   "bisiklet"),
    ("high",      151,  200.0, 2, "sugar_free", "egzersiz"),
    ("very_high", 201, 9999.0, 3, "sugar_free", "klinik"),
]


# ---- Yardımcı ----
def _insert_alert(cur, patient_id: int, alert_type: str, msg: str):
    cur.execute(
        "INSERT INTO alerts (patient_id, created_dt, alert_type, message) "
        "VALUES (%s, %s, %s, %s)",
        (patient_id, datetime.now(), alert_type, msg),
    )


# ---- Ana fonksiyon ----
def evaluate_day(patient_id: int, day: date | None = None):
    """
    Verilen hastada gün içi ölçümleri değerlendirir,
    insulin_suggestions ve gerekirse alerts tablolarına yazar.
    """
    day = day or date.today()

    with db_cursor() as cur:
        # 1) Günlük ölçümleri al
        cur.execute(
            "SELECT value_mg_dl FROM glucose_readings "
            "WHERE patient_id=%s AND DATE(reading_dt)=%s",
            (patient_id, day),
        )
        readings = [row["value_mg_dl"] for row in cur.fetchall()]

        if not readings:
            _insert_alert(
                cur,
                patient_id,
                "missing_all",
                f"{day} tarihinde hiç ölçüm yapılmadı.",
            )
            print("Uyarı: hiç ölçüm yok.")
            return

        if len(readings) < 3:
            _insert_alert(
                cur,
                patient_id,
                "missing_few",
                f"{day} tarihinde yalnızca {len(readings)} ölçüm girildi.",
            )

        # 2) Ortalama & doz ve öneriler
        avg = sum(readings) / len(readings)
        level = next(t for t in LEVELS if t[1] <= avg <= t[2])
        dose = level[3]
        diet_sug = level[4]
        ex_sug   = level[5]

        # insulin_suggestions upsert
        cur.execute(
            """
            INSERT INTO insulin_suggestions
            (patient_id, day, avg_glucose, dose_ml)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                avg_glucose = VALUES(avg_glucose),
                dose_ml     = VALUES(dose_ml)
            """,
            (patient_id, day, avg, dose),
        )

        # Diyet & egzersiz önerisi alert
        _insert_alert(
            cur,
            patient_id,
            "info",
            f"{day} ort. {avg:.1f} mg/dL → Diyet: {diet_sug}, Egzersiz: {ex_sug}"
        )

        # 3) Kritik eşiklere bak → acil uyarı
        if min(readings) < 70:
            _insert_alert(
                cur,
                patient_id,
                "hypo",
                f"{day} tarihinde <70 mg/dL ölçüm tespit edildi (hipoglisemi).",
            )
        if max(readings) > 200:
            _insert_alert(
                cur,
                patient_id,
                "very_high",
                f"{day} tarihinde >200 mg/dL ölçüm tespit edildi (hiperglisemi).",
            )

        print(f"Günlük ortalama: {avg:.1f} mg/dL → {dose} ml önerildi.")
