from utils.db import db_cursor
from utils.hashing import hash_password, verify_password


def update_password(user_id: int, current_password: str, new_password: str) -> bool:

    with db_cursor() as cur:
        cur.execute("SELECT password_hash FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()

        if not row or not verify_password(current_password, row["password_hash"]):
            return False


    password_hash = hash_password(new_password)
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash=%s WHERE id=%s",
            (password_hash, user_id)
        )

    return True 