# gui/login.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils.db import db_cursor
from utils.hashing import verify_password


class LoginDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Diyabet Takip | Giriş")
        self.resizable(False, False)

        ttk.Label(self, text="TC Kimlik No:").grid(row=0, column=0, padx=8, pady=6, sticky="e")
        self.tc_entry = ttk.Entry(self, width=20)
        self.tc_entry.grid(row=0, column=1, padx=8, pady=6)

        ttk.Label(self, text="Parola:").grid(row=1, column=0, padx=8, pady=6, sticky="e")
        self.pw_entry = ttk.Entry(self, width=20, show="●")
        self.pw_entry.grid(row=1, column=1, padx=8, pady=6)

        self.role_lbl = ttk.Label(self, text="")        # ← rol bilgisi
        self.role_lbl.grid(row=2, columnspan=2, pady=3)

        ttk.Button(self, text="Giriş", command=self._on_login)\
            .grid(row=3, columnspan=2, pady=8)

        self.result = None
        self.tc_entry.focus()

    # ----------------------------
    def _on_login(self):
        tc = self.tc_entry.get().strip()
        pw = self.pw_entry.get().strip()

        with db_cursor() as cur:
            cur.execute("SELECT id, password_hash, role FROM users WHERE tc_no=%s", (tc,))
            row = cur.fetchone()

        if row and verify_password(pw, row["password_hash"]):
            self.role_lbl.configure(text=f"Giriş başarılı → {row['role'].capitalize()}")
            self.result = {"user_id": row["id"], "role": row["role"]}
            self.after(700, self.destroy)   # kısa gecikme sonra pencere kapanır
        else:
            messagebox.showerror("Hata", "TC No veya parola yanlış.")
