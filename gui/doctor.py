import tkinter as tk
from tkinter import ttk, messagebox
from utils.db import db_cursor
from gui.add_patient import AddPatientDialog


class DoctorWindow(tk.Toplevel):
    def __init__(self, master, doctor_id: int):
        super().__init__(master)
        self.title("Doktor Paneli")
        self.geometry("380x320")

        self.doctor_id = doctor_id           # <––  id'yi saklıyoruz

        # ---- Hasta listesi tablosu ----
        self.tree = ttk.Treeview(self, columns=("tc", "name"), show="headings")
        self.tree.heading("tc", text="TC No")
        self.tree.heading("name", text="Hasta Adı")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(self, text="Yeni Hasta Ekle",
                   command=lambda: AddPatientDialog(self, doctor_id, self._refresh))\
            .pack(pady=(0, 10))

        self._refresh()                      # <–– eski _load_patients yerine

    # ------------------------------------------------------------------
    def _refresh(self):
        """Tablodaki satırları yeniler."""
        # önce temizle
        for item in self.tree.get_children():
            self.tree.delete(item)

        with db_cursor() as cur:
            cur.execute(
                "SELECT u.tc_no, u.full_name "
                "FROM patients p JOIN users u ON p.id = u.id "
                "WHERE p.doctor_id = %s",
                (self.doctor_id,)
            )
            rows = cur.fetchall()

        for tc, name in rows:
            self.tree.insert("", tk.END, values=(tc, name))

        if not rows:
            messagebox.showinfo("Bilgi", "Bu doktora bağlı hasta yok.")
