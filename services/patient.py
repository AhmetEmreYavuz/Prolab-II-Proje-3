# services/patient.py
from secrets import choice
from string import ascii_letters, digits
from utils.db import db_cursor, get_connection
from utils.hashing import hash_password
from utils.emailer import send_mail


def _gen_pass(k: int = 10) -> str:
    alphabet = ascii_letters + digits
    return "".join(choice(alphabet) for _ in range(k))


def register_patient(tc_no: str, full_name: str, email: str,
                     birth_date: str, gender: str,
                     doctor_id: int) -> tuple[int, str]:
    """
    Yeni hastayı (users + patients) ekler.
    :returns: (user_id, plain_password)
    """
    plain_pw = _gen_pass()
    
    # Explicit transaction management
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        
        # users
        cur.execute(
            "INSERT INTO users "
            "(tc_no, full_name, email, password_hash, role, birth_date, gender) "
            "VALUES (%s,%s,%s,%s,'patient',%s,%s)",
            (tc_no, full_name, email, hash_password(plain_pw), birth_date, gender)
        )
        uid = cur.lastrowid
        
        # patients
        cur.execute(
            "INSERT INTO patients (id, doctor_id) VALUES (%s,%s)",
            (uid, doctor_id)
        )
        
        # Explicitly commit the transaction
        conn.commit()
        print(f"Patient added successfully. User ID: {uid}")
        
        # Mail gönder
        send_mail(
            email,
            "Diyabet Takip Sistemi Giriş Bilgileri",
            f"Merhaba {full_name},\n\n"
            f"Sisteme giriş için:\nTC No : {tc_no}\nParola : {plain_pw}\n\n"
            "Lütfen ilk girişten sonra parolanızı değiştirin."
        )
        
        return uid, plain_pw
    
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error adding patient: {str(e)}")
        raise
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
