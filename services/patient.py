# services/patient.py
from secrets import choice
from datetime import date
from string import ascii_letters, digits
from utils.db import db_cursor, get_connection
from utils.hashing import hash_password
from utils.emailer import send_mail


def _gen_pass(k: int = 10) -> str:
    alphabet = ascii_letters + digits
    return "".join(choice(alphabet) for _ in range(k))


def register_patient(tc_no: str, full_name: str, email: str,
                     birth_date: date | None, gender: str,
                     doctor_id: int, profile_image=None) -> tuple[int, str]:
    plain_pw = _gen_pass()

    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "INSERT INTO users "
            "(tc_no, full_name, email, password_hash, role, birth_date, gender, password_change_needed) "
            "VALUES (%s,%s,%s,%s,'patient',%s,%s,1)",
            (tc_no, full_name, email, hash_password(plain_pw), birth_date, gender)
        )
        uid = cur.lastrowid

        if profile_image:
            cur.execute(
                "INSERT INTO patients (id, doctor_id, profile_img) VALUES (%s,%s,%s)",
                (uid, doctor_id, profile_image)
            )
        else:
            cur.execute(
                "INSERT INTO patients (id, doctor_id) VALUES (%s,%s)",
                (uid, doctor_id)
            )

        conn.commit()
        print(f"Patient added successfully. User ID: {uid}")

        send_mail(
            email,
            "Diyabet Takip Sistemi Giriş Bilgileri",
            f"Merhaba {full_name},\n\n"
            f"Sisteme giriş için:\nTC No : {tc_no}\nParola : {plain_pw}\n\n"
            "Lütfen ilk girişten sonra parolanızı değiştirin."
        )

        return uid, plain_pw

    except Exception as e:

        conn.rollback()
        print(f"Error adding patient: {str(e)}")
        raise

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_profile_image(patient_id: int):
    with db_cursor() as cur:
        cur.execute(
            "SELECT profile_img FROM patients WHERE id=%s",
            (patient_id,)
        )
        result = cur.fetchone()
        return result["profile_img"] if result and "profile_img" in result else None


def update_profile_image(patient_id: int, profile_image):
    with db_cursor() as cur:
        cur.execute(
            "UPDATE patients SET profile_img=%s WHERE id=%s",
            (profile_image, patient_id)
        )
