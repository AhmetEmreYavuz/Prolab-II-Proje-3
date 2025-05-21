# services/schema.py
"""Eksik tabloları oluşturmak için tek seferlik yardımcı."""

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
  gender        ENUM('F','M','O')
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
  reading_dt   DATETIME NOT NULL,
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
  created_dt   DATETIME NOT NULL,
  alert_type   ENUM('hypo','mid_high','high','very_high',
                    'missing_all','missing_few'),
  message      TEXT,
  is_read      BOOL DEFAULT 0,
  FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
) ENGINE=InnoDB;
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
        for stmt in SCHEMA_SQL.strip().split(";"):
            s = stmt.strip()
            if s:
                cur.execute(s)
    print("Eksik tablolar oluşturuldu (var olanlara dokunulmadı).")
