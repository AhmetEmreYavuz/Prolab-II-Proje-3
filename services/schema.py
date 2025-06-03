# services/schema.py


from utils.db import db_cursor

SCHEMA_SQL = """
/* -------------- USERS -------------- */
CREATE TABLE IF NOT EXISTS users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  tc_no         CHAR(11)      NOT NULL UNIQUE,
  full_name     VARCHAR(100)  NOT NULL,
  email         VARCHAR(120)  NOT NULL UNIQUE,
  password_hash CHAR(60)      NOT NULL,
  role          ENUM('doctor','patient') NOT NULL,
  birth_date    DATE,
  gender        ENUM('F','M','O'),
  password_change_needed TINYINT(1) DEFAULT 0
) ENGINE=InnoDB;

/* -------------- PATIENTS -------------- */
CREATE TABLE IF NOT EXISTS patients (
  id        INT PRIMARY KEY,
  doctor_id INT NOT NULL,
  profile_img LONGBLOB,
  FOREIGN KEY (id)        REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

/* -------------- GLUCOSE -------------- */
CREATE TABLE IF NOT EXISTS glucose_readings (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  patient_id   INT NOT NULL,
  reading_dt   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  value_mg_dl  DECIMAL(5,2) NOT NULL,
  FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
  INDEX idx_patient_dt (patient_id, reading_dt)
) ENGINE=InnoDB;

/* -------------- INSULIN SUGGESTIONS -------------- */
CREATE TABLE IF NOT EXISTS insulin_suggestions (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  patient_id   INT NOT NULL,
  day          DATE NOT NULL,
  avg_glucose  DECIMAL(5,2),
  dose_ml      DECIMAL(4,1),
  UNIQUE KEY uk_patient_day (patient_id, day),
  FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
) ENGINE=InnoDB;

/* -------------- ALERTS -------------- */
CREATE TABLE IF NOT EXISTS alerts (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  patient_id   INT NOT NULL,
  created_dt   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  alert_type   ENUM('hypo','mid_high','high','very_high',
                    'missing_all','missing_few'),
  message      TEXT,
  is_read      BOOL DEFAULT 0,
  FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
) ENGINE=InnoDB;

/* -------------- SYMPTOMS -------------- */
CREATE TABLE IF NOT EXISTS symptoms (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  patient_id  INT NOT NULL,
  noted_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  description TEXT NOT NULL,
  severity    VARCHAR(50),
  FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
  INDEX idx_patient_dt (patient_id, noted_at)
) ENGINE=InnoDB;

/* -------------- PATIENT_SYMPTOMS -------------- */
CREATE TABLE IF NOT EXISTS patient_symptoms (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  patient_id   INT NOT NULL,
  symptom_code VARCHAR(30) NOT NULL,
  added_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_patient_symptom (patient_id, symptom_code),
  FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

/* -------------- DAILY STATUS -------------- */
CREATE TABLE IF NOT EXISTS daily_status (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  patient_id    INT NOT NULL,
  day           DATE NOT NULL,
  diet_type     ENUM('low_sugar','sugar_free','balanced'),
  diet_done     BOOL,
  exercise_type ENUM('walk','bike','clinic'),
  exercise_done BOOL,
  UNIQUE KEY uk_patient_day (patient_id, day),
  FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
) ENGINE=InnoDB;
"""


def create_missing_tables():
    with db_cursor() as cur:
        # 1) CREATE TABLE komutları
        for stmt in SCHEMA_SQL.strip().split(";"):
            s = stmt.strip()
            if s:
                cur.execute(s + ";")

        # 2) Eksik sütun varsa ekle
        cur.execute("""
            SELECT COUNT(*) AS cnt
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = 'users'
              AND COLUMN_NAME  = 'password_change_needed'
        """)
        if cur.fetchone()["cnt"] == 0:
            cur.execute("""
                ALTER TABLE users
                ADD COLUMN password_change_needed TINYINT(1) NOT NULL DEFAULT 0
            """)


    print("Eksik tablolar ve sütunlar oluşturuldu / güncellendi.")
