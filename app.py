# app.py  –  Diyabet Takip Sistemi (ham-SQL)

from utils.db import db_cursor
from utils.hashing import hash_password
from services.schema import create_missing_tables
from services.glucose import add_glucose
from services.rules import evaluate_day



def seed() -> None:
    with db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE tc_no=%s", ("12345678901",))
        if cur.fetchone():
            print("Örnek doktor zaten var.")
            return

        cur.execute(
            "INSERT INTO users (tc_no, full_name, email, password_hash, role) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                "12345678901",
                "Ahmet Esad",
                "doctoremail@ornek.com",
                hash_password("drpass"),
                "doctor",
            ),
        )
        doc_id = cur.lastrowid


        cur.execute(
            "INSERT IGNORE INTO patients (id, doctor_id) VALUES (%s, %s)",
            (doc_id, doc_id),
        )
        print("Örnek doktor ve hasta eklendi, id:", doc_id)


def cli_add_glucose(args: list[str]) -> None:
    if len(args) != 2:
        print("Kullanım: python app.py add_glucose <hasta_id> <değer>")
        return
    try:
        patient_id = int(args[0])
        value = float(args[1])
    except ValueError:
        print("Hata: <hasta_id> tamsayı, <değer> sayı olmalıdır.")
        return

    row_id = add_glucose(patient_id, value)
    print(f"Ölçüm eklendi. Row ID = {row_id}")


def cli_evaluate(args: list[str]) -> None:
    if len(args) != 1:
        print("Kullanım: python app.py evaluate <hasta_id>")
        return
    try:
        patient_id = int(args[0])
    except ValueError:
        print("Hata: <hasta_id> tamsayı olmalıdır.")
        return

    evaluate_day(patient_id)



if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "init_schema":
        create_missing_tables()

    elif cmd == "seed":
        seed()

    elif cmd == "add_glucose":
        cli_add_glucose(sys.argv[2:])

    elif cmd == "evaluate":
        cli_evaluate(sys.argv[2:])

    else:
        print(
            "Kullanım:\n"
            "  python app.py init_schema\n"
            "  python app.py seed\n"
            "  python app.py add_glucose <hasta_id> <değer>\n"
            "  python app.py evaluate <hasta_id>"
        )