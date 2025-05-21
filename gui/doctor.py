# gui/doctor.py
import tkinter as tk
from tkinter import ttk, messagebox
from utils.db import db_cursor
from gui.add_patient import AddPatientDialog
from gui.patient import PatientWindow          # Hasta paneli
from gui.status import StatusWindow            # Günlük diyet/egzersiz

class DoctorWindow(tk.Toplevel):
    """Doktorun hasta listesini görüntülediği ve yönetebildiği pencere."""

    def __init__(self, master, doctor_id: int):
        super().__init__(master)
        self.title("Doktor Paneli")
        self.geometry("400x380")

        self.doctor_id = doctor_id   # giriş yapan doktorun id’si

        # ---------- Hasta listesi ----------
        self.tree = ttk.Treeview(
            self, columns=("tc", "name"), show="headings", height=13
        )
        self.tree.heading("tc", text="TC No")
        self.tree.heading("name", text="Hasta Adı")
        self.tree.column("tc", width=120, anchor="center")
        self.tree.column("name", width=230, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree.bind("<Double-1>", self._open_patient)   # çift tıkla aç

        # ---------- Butonlar ----------
        btn_frm = ttk.Frame(self)
        btn_frm.pack(pady=(0, 12))

        ttk.Button(
            btn_frm, text="Yeni Hasta Ekle",
            command=lambda: AddPatientDialog(self, doctor_id, self._refresh)
        ).grid(row=0, column=0, padx=6)

        ttk.Button(
            btn_frm, text="Ölçüm Gir",
            command=self._open_patient
        ).grid(row=0, column=1, padx=6)

        ttk.Button(                                   # ← yeni düğme
            btn_frm, text="Günlük Durum Göster",
            command=self._show_status
        ).grid(row=0, column=2, padx=6)

        self._refresh()   # ilk tablo yüklemesi

    # ------------------------------------------------------------
    def _refresh(self):
        """Hasta listesini yeniler."""
        self.tree.delete(*self.tree.get_children())

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.tc_no, u.full_name
                FROM patients p
                JOIN users    u ON p.id = u.id
                WHERE p.doctor_id = %s
                """,
                (self.doctor_id,)
            )
            rows = cur.fetchall()

        for row in rows:
            # item kimliğinde hasta id’sini saklıyoruz
            self.tree.insert(
                "", tk.END,
                iid=row["id"],
                values=(row["tc_no"], row["full_name"])
            )

        if not rows:
            messagebox.showinfo("Bilgi", "Bu doktora bağlı hasta yok.")

    # ------------------------------------------------------------
    def _open_patient(self, event=None):
        """Seçili hastayı Hasta Paneli olarak aç."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin.")
            return
        patient_id = int(sel[0])          # item id = hasta id
        PatientWindow(self, patient_id)

    # ------------------------------------------------------------
    def _show_status(self):
        """Seçili hastanın diyet / egzersiz geçmişini gösterir."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir hasta seçin.")
            return
        patient_id = int(sel[0])
        full_name  = self.tree.item(sel[0], "values")[1]
        StatusWindow(self, patient_id, full_name)
