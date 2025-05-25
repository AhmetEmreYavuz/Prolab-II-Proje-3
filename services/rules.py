# services/rules.py
from datetime import date, datetime
from zoneinfo import ZoneInfo
from utils.db import db_cursor
from services.alert import add_alert

LEVELS = [
    ("hypo",        0,    69.9, 0, "yüksek_karb", "dinlen"),
    ("normal",     70,   110.0, 0, "balanced",    "yürüyüş"),
    ("mid_high",  111,   150.0, 1, "low_sugar",   "bisiklet"),
    ("high",      151,   200.0, 2, "sugar_free",  "egzersiz"),
    ("very_high", 201,  9999.0, 3, "sugar_free",  "klinik"),
]

AVG_LEVEL_MSG = {
    "normal":    "Kan şekeri seviyesi normal aralıkta. Hiçbir işlem gerekmez.",
    "mid_high":  "Hastanın kan şekeri 111–150 mg/dL arasında. Durum izlenmeli.",
    "high":      "Hastanın kan şekeri 151–200 mg/dL arasında. Diyabet kontrolü gereklidir.",
    "very_high": "Hastanın kan şekeri 200 mg/dL’nin üzerinde. Hiperglisemi durumu. Acil müdahale gerekebilir."
}

def evaluate_day(patient_id: int, day: date | None = None) -> None:
    day       = day or date.today()
    day_str   = day.strftime("%d.%m.%Y")

    with db_cursor() as cur:
        # <<< THIS IS THE ONLY CHANGE >>>
        cur.execute(
            """
            SELECT value_mg_dl
              FROM glucose_readings
             WHERE patient_id = %s
               AND DATE(CONVERT_TZ(reading_dt, @@session.time_zone, '+03:00')) = %s
            """,
            (patient_id, day)
        )
        readings = [r["value_mg_dl"] for r in cur.fetchall()]

        # 1) hiçbir ölçüm yok
        if not readings:
            add_alert(patient_id, "missing_all",
                      f"{day_str} tarihinde hiç ölçüm yapılmadı.",
                      day)
            return

        # 2) yetersiz ölçüm (<3)
        if len(readings) < 3:
            add_alert(patient_id, "missing_few",
                      f"{day_str} tarihinde yalnızca {len(readings)} ölçüm girildi.",
                      day)

        # 3) günün ortalaması, öneriler ve alert
        avg = sum(readings) / len(readings)
        code, lo, hi, dose, diet_sug, ex_sug = next(
            lvl for lvl in LEVELS if lvl[1] <= avg <= lvl[2]
        )

        # — ortalama alert’ini ekle
        if code in AVG_LEVEL_MSG:
            add_alert(patient_id,
                      code,
                      AVG_LEVEL_MSG[code],
                      day)

        # — insulin_suggestions tablosuna upsert
        cur.execute(
            """
            INSERT INTO insulin_suggestions
              (patient_id, day, avg_glucose, dose_ml)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              avg_glucose = VALUES(avg_glucose),
              dose_ml     = VALUES(dose_ml)
            """,
            (patient_id, day, avg, dose)
        )

        # 4) Kritik eşikler (<70 / >200) — use day_str, no time:
        if min(readings) < 70:
            add_alert(
                patient_id,
                "hypo",
                f"{day_str} tarihinde <70 mg/dL ölçüm tespit edildi (hipoglisemi).",
                day
            )
        if max(readings) > 200:
            add_alert(
                patient_id,
                "very_high",
                f"{day_str} tarihinde >200 mg/dL ölçüm tespit edildi (hiperglisemi).",
                day
            )

    print(f"[evaluate_day] patient={patient_id}, day={day_str}, avg={avg:.1f}, dose={dose}")
