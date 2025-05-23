# services/rules.py
"""
Gün sonu ortalama, insülin dozu ve uyarı üretir.
Ham-SQL kullanır.
Tüm timestamp’ler DD.MM.YYYY HH:MM:SS Zaman Dilimi (Europe/Istanbul) formatında kaydedilir,
mesajlarda tarih GG.AA.YYYY formatında gösterilir.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo
from utils.db import db_cursor

# ---- Sabitler ----
# (type, lo, hi, insulin_dose, diet, exercise)
LEVELS = [
    ("hypo",        0,   69.9, 0, "yüksek_karb", "dinlen"),
    ("normal",     70,  110.0, 0, "balanced",    "yürüyüş"),
    ("mid_high",  111,  150.0, 1, "low_sugar",   "bisiklet"),
    ("high",      151,  200.0, 2, "sugar_free",  "egzersiz"),
    ("very_high", 201, 9999.0, 3, "sugar_free",  "klinik"),
]


# ---- Yardımcı ----
def _insert_alert(cur, patient_id: int, alert_type: str, msg: str):
    """alerts.created_dt sütununa Europe/Istanbul zaman damgası ekler."""
    now = datetime.now(ZoneInfo("Europe/Istanbul"))
    cur.execute(
        "INSERT INTO alerts (patient_id, created_dt, alert_type, message) "
        "VALUES (%s, %s, %s, %s)",
        (patient_id, now, alert_type, msg),
    )


# ---- Ana fonksiyon ----
def evaluate_day(patient_id: int, day: date | None = None):
    """
    Verilen hastada gün içi ölçümleri değerlendirir,
    insulin_suggestions ve gerekirse alerts tablolarına yazar.
    """
    day = day or date.today()
    day_str = day.strftime("%d.%m.%Y")  # GG.AA.YYYY formatı

    with db_cursor() as cur:
        cur.execute(
            """
            SELECT value_mg_dl
            FROM glucose_readings
            WHERE patient_id=%s
              AND DATE(CONVERT_TZ(reading_dt, @@session.time_zone, '+03:00')) = %s
              AND (
                    TIME(reading_dt) BETWEEN '07:00:00' AND '08:00:00'
                 OR TIME(reading_dt) BETWEEN '12:00:00' AND '13:00:00'
                 OR TIME(reading_dt) BETWEEN '15:00:00' AND '16:00:00'
                 OR TIME(reading_dt) BETWEEN '18:00:00' AND '19:00:00'
                 OR TIME(reading_dt) BETWEEN '22:00:00' AND '23:00:00'
              )
            """,
            (patient_id, day),
        )
        readings = [row["value_mg_dl"] for row in cur.fetchall()]

        # Ölçüm yoksa uyarı
        if not readings:
            _insert_alert(
                cur,
                patient_id,
                "missing_all",
                f"{day_str} tarihinde hiç ölçüm yapılmadı.",
            )
            return

        # Az ölçüm varsa uyarı
        if len(readings) < 3:
            _insert_alert(
                cur,
                patient_id,
                "missing_few",
                f"{day_str} tarihinde yalnızca {len(readings)} ölçüm girildi.",
            )

        # 2) Ortalama & doz ve öneriler
        avg = sum(readings) / len(readings)
        level = next(t for t in LEVELS if t[1] <= avg <= t[2])
        dose, diet_sug, ex_sug = level[3], level[4], level[5]

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
            f"{day_str} ort. {avg:.1f} mg/dL → Diyet: {diet_sug}, Egzersiz: {ex_sug}"
        )

        # 3) Kritik eşiklere bak → acil uyarı
        now = datetime.now(ZoneInfo("Europe/Istanbul"))
        timestamp = now.strftime("%d.%m.%Y %H:%M:%S %Z")

        if min(readings) < 70:
            _insert_alert(
                cur,
                patient_id,
                "hypo",
                f"{timestamp} tarihinde <70 mg/dL ölçüm tespit edildi (hipoglisemi).",
            )
        if max(readings) > 200:
            _insert_alert(
                cur,
                patient_id,
                "very_high",
                f"{timestamp} tarihinde >200 mg/dL ölçüm tespit edildi (hiperglisemi).",
            )

    # Konsola bilgi
    print(f"Günlük ortalama: {avg:.1f} mg/dL → {dose} ml önerildi.")
