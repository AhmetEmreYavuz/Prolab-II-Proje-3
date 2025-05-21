# gui/login.py
import tkinter as tk
import ttkbootstrap as ttk
from utils.db import db_cursor
from utils.hashing import verify_password


class LoginDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Diyabet Takip | Giriş")
        self.geometry("400x320")
        self.resizable(False, False)
        self.configure(bg="#2b3e50")  # Superhero temasına uygun arka plan
        
        # Ana frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill="both")
        
        # Başlık
        ttk.Label(
            main_frame, 
            text="Diyabet Takip Sistemi", 
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(10, 20))
        
        # Form frame
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="x", pady=10)
        
        # TC Kimlik alanı
        ttk.Label(
            form_frame, 
            text="TC Kimlik No:", 
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(0, 5))
        
        self.tc_entry = ttk.Entry(form_frame, width=30, font=("Segoe UI", 11))
        self.tc_entry.pack(fill="x", pady=(0, 15))
        
        # Parola alanı
        ttk.Label(
            form_frame, 
            text="Parola:", 
            font=("Segoe UI", 11)
        ).pack(anchor="w", pady=(0, 5))
        
        self.pw_entry = ttk.Entry(form_frame, width=30, font=("Segoe UI", 11), show="●")
        self.pw_entry.pack(fill="x", pady=(0, 15))
        
        # Rol bilgisi
        self.role_lbl = ttk.Label(
            form_frame, 
            text="",
            font=("Segoe UI", 10)
        )
        self.role_lbl.pack(pady=5)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Giriş butonu - daha belirgin ve büyük
        self.login_btn = ttk.Button(
            button_frame, 
            text="Giriş Yap", 
            style="success.TButton",
            command=self._on_login,
            width=15
        )
        self.login_btn.pack(side="left", padx=(0, 10))
        
        ttk.Button(
            button_frame, 
            text="İptal", 
            style="danger.TButton",
            command=self.destroy,
            width=15
        ).pack(side="right")

        self.result = None
        self.tc_entry.focus()
        
        # Enter tuşu ile giriş yapma
        self.bind("<Return>", lambda event: self._on_login())
        self.tc_entry.bind("<Return>", lambda event: self._on_login())
        self.pw_entry.bind("<Return>", lambda event: self._on_login())

    # ----------------------------
    def _on_login(self):
        tc = self.tc_entry.get().strip()
        pw = self.pw_entry.get().strip()
        
        # Alanları kontrol et
        if not tc or not pw:
            self.role_lbl.configure(
                text="TC No ve parola alanları boş olamaz!",
                bootstyle="danger"
            )
            return

        with db_cursor() as cur:
            cur.execute("SELECT id, password_hash, role FROM users WHERE tc_no=%s", (tc,))
            row = cur.fetchone()

        if row and verify_password(pw, row["password_hash"]):
            self.role_lbl.configure(
                text=f"Giriş başarılı → {row['role'].capitalize()}",
                bootstyle="success"
            )
            self.result = {"user_id": row["id"], "role": row["role"]}
            self.after(700, self.destroy)   # kısa gecikme sonra pencere kapanır
        else:
            self.role_lbl.configure(
                text="TC No veya parola yanlış!",
                bootstyle="danger"
            )
