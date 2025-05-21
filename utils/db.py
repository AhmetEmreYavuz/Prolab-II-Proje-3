# utils/db.py
import mysql.connector
from contextlib import contextmanager

DB_CONFIG = {
    "user":       "dts_user",
    "password":   "SüperZorParola_123",
    "host":       "localhost",
    "database":   "diabetes",
    "charset":    "utf8mb4",
    "autocommit": True,
}


def get_connection():
    """Her çağrıda yeni MySQL bağlantısı döndürür."""
    return mysql.connector.connect(**DB_CONFIG)


@contextmanager
def db_cursor():
    """
    with db_cursor() as cur:
        cur.execute("SELECT 1")
    """
    cnx = get_connection()
    try:
        cur = cnx.cursor(dictionary=True)
        yield cur
    finally:
        cur.close()
        cnx.close()
