# gui/login.py
import tkinter as tk
import ttkbootstrap as ttk
from utils.db import db_cursor
from utils.hashing import verify_password
from gui.utils import setup_responsive_dialog


class LoginDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)


        width, height = setup_responsive_dialog(
            self,
            "🔐 Sisteme Giriş",
            width=450,
            height=350,
            min_width=400,
            min_height=300
        )

        self.result = None
        self._create_login_form()

    def _create_login_form(self):


        main_frame = ttk.Frame(self, padding=30)
        main_frame.pack(fill="both", expand=True)


        title_label = ttk.Label(
            main_frame,
            text="💊 Sisteme Giriş",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        )
        title_label.pack(pady=(0, 30))


        self._create_form_fields(main_frame)


        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 10),
            justify="center"
        )
        self.status_label.pack(pady=(15, 0))


        self._create_buttons(main_frame)


        self.tc_entry.focus()
        self._setup_key_bindings()

    def _create_form_fields(self, parent):


        tc_frame = ttk.Frame(parent)
        tc_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            tc_frame,
            text="👤 TC Kimlik No:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))

        self.tc_entry = ttk.Entry(
            tc_frame,
            font=("Segoe UI", 12),
            width=30
        )
        self.tc_entry.pack(fill="x")


        pw_frame = ttk.Frame(parent)
        pw_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            pw_frame,
            text="🔒 Parola:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))

        self.pw_entry = ttk.Entry(
            pw_frame,
            font=("Segoe UI", 12),
            show="●",
            width=30
        )
        self.pw_entry.pack(fill="x")

    def _create_buttons(self, parent):

        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(20, 0))


        login_btn = ttk.Button(
            button_frame,
            text="✓ Giriş Yap",
            command=self._on_login,
            bootstyle="success",
            width=15
        )
        login_btn.pack(side="left", padx=(0, 10))


        cancel_btn = ttk.Button(
            button_frame,
            text="✖ İptal",
            command=self.destroy,
            bootstyle="danger",
            width=15
        )
        cancel_btn.pack(side="right")

    def _setup_key_bindings(self):

        self.bind("<Return>", lambda event: self._on_login())
        self.tc_entry.bind("<Return>", lambda event: self.pw_entry.focus())
        self.pw_entry.bind("<Return>", lambda event: self._on_login())

    def _on_login(self):

        tc = self.tc_entry.get().strip()
        pw = self.pw_entry.get().strip()


        self.status_label.configure(text="")


        if not tc or not pw:
            self._show_status("❌ TC No ve parola alanları boş olamaz!", "danger")
            return


        self._show_status("🔄 Giriş yapılıyor...", "info")
        self._set_form_state(False)


        self.after(300, lambda: self._perform_login(tc, pw))

    def _perform_login(self, tc, pw):

        try:
            with db_cursor() as cur:
                cur.execute(
                    "SELECT id, password_hash, role, full_name FROM users WHERE tc_no=%s",
                    (tc,)
                )
                row = cur.fetchone()

            if row and verify_password(pw, row["password_hash"]):

                self._show_status(
                    f"✅ Giriş başarılı! {row['full_name']}",
                    "success"
                )

                self.result = {
                    "user_id": row["id"],
                    "role": row["role"],
                    "name": row["full_name"]
                }


                self.after(800, self.destroy)
            else:

                self._show_status("❌ TC No veya parola hatalı!", "danger")
                self._set_form_state(True)
                self.pw_entry.delete(0, tk.END)
                self.tc_entry.focus()

        except Exception as e:
            self._show_status(f"❌ Bağlantı hatası: {str(e)}", "danger")
            self._set_form_state(True)

    def _show_status(self, message, style):

        self.status_label.configure(text=message, bootstyle=style)

    def _set_form_state(self, enabled):

        state = "normal" if enabled else "disabled"
        self.tc_entry.configure(state=state)
        self.pw_entry.configure(state=state)