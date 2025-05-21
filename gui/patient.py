# gui/patient.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from services.glucose import add_glucose, list_today
from services.daily import upsert_status
from services.rules import evaluate_day
from utils.db import db_cursor


class PatientWindow(tk.Toplevel):
    """Hastanın ölçüm, diyet ve egzersiz girebildiği pencere."""

    def __init__(self, master, patient_id: int):
        super().__init__(master)
        self.patient_id = patient_id
        self.title("Hasta Paneli")
        self.geometry("340x370")

        # ---------- Yeni Ölçüm ----------
        meas_frm = ttk.LabelFrame(self, text="Kan Şekeri Ölçümü")
        meas_frm.pack(padx=12, pady=8, fill="x")

        ttk.Label(meas_frm, text="Değer (mg/dL):")\
            .grid(row=0, column=0, padx=6, pady=6)
        self.val_ent = ttk.Entry(meas_frm, width=10)
        self.val_ent.grid(row=0, column=1, padx=6, pady=6)

        ttk.Button(meas_frm, text="Kaydet", command=self._save_glucose)\
            .grid(row=0, column=2, padx=6, pady=6)

        # ---------- Diyet & Egzersiz ----------
        st = ttk.LabelFrame(self, text="Diyet / Egzersiz")
        st.pack(padx=12, pady=4, fill="x")

        ttk.Label(st, text="Diyet Türü:").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.diet_cmb = ttk.Combobox(st, width=12, state="readonly",
                                     values=("low_sugar", "sugar_free", "balanced"))
        self.diet_cmb.current(0)
        self.diet_cmb.grid(row=0, column=1, padx=4, pady=4)

        self.diet_chk = tk.BooleanVar()
        ttk.Checkbutton(st, text="Uygulandı", variable=self.diet_chk)\
            .grid(row=0, column=2, padx=4, pady=4)

        ttk.Label(st, text="Egzersiz Türü:").grid(row=1, column=0, padx=4, pady=4, sticky="e")
        self.ex_cmb = ttk.Combobox(st, width=12, state="readonly",
                                   values=("walk", "bike", "clinic"))
        self.ex_cmb.current(0)
        self.ex_cmb.grid(row=1, column=1, padx=4, pady=4)

        self.ex_chk = tk.BooleanVar()
        ttk.Checkbutton(st, text="Yapıldı", variable=self.ex_chk)\
            .grid(row=1, column=2, padx=4, pady=4)

        ttk.Button(st, text="Kaydet", command=self._save_status)\
            .grid(row=2, columnspan=3, pady=6)

        # ---------- Günlük Özet ----------
        self.sum_lbl = ttk.Label(self, text="", font=("Segoe UI", 10, "bold"))
        self.sum_lbl.pack(pady=6)

        self.alert_box = tk.Text(self, height=6, state="disabled")
        self.alert_box.pack(padx=10, fill="both", expand=True)

        self._refresh()

    # ------------------------------------------------------------------
    def _save_glucose(self):
        """Kan şekeri ölçümünü kaydeder."""
        try:
            value = float(self.val_ent.get())
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz sayı.")
            return

        add_glucose(self.patient_id, value)
        self.val_ent.delete(0, tk.END)
        self._refresh()

    # ------------------------------------------------------------------
    def _save_status(self):
        """Günlük diyet & egzersiz durumunu kaydeder."""
        upsert_status(
            self.patient_id,
            self.diet_cmb.get(),  self.diet_chk.get(),
            self.ex_cmb.get(),    self.ex_chk.get()
        )
        messagebox.showinfo("Bilgi", "Günlük durum kaydedildi.")

    # ------------------------------------------------------------------
    def _refresh(self):
        """Ölçüm özetini ve uyarıları yeniler."""
        readings = list_today(self.patient_id)
        if readings:
            avg = sum(r["value_mg_dl"] for r in readings) / len(readings)
            self.sum_lbl.config(text=f"{len(readings)} ölçüm  •  Ortalama {avg:.1f}")
        else:
            self.sum_lbl.config(text="Bugün ölçüm yok.")

        # Doz & uyarı hesapla
        evaluate_day(self.patient_id, date.today())

        # Son 5 uyarıyı getir
        with db_cursor() as cur:
            cur.execute(
                "SELECT created_dt, message FROM alerts "
                "WHERE patient_id=%s ORDER BY created_dt DESC LIMIT 5",
                (self.patient_id,),
            )
            alerts = cur.fetchall()

        self.alert_box.configure(state="normal")
        self.alert_box.delete("1.0", tk.END)
        for a in alerts:
            t = a["created_dt"].strftime("%H:%M")
            self.alert_box.insert(tk.END, f"{t}  {a['message']}\n")
        self.alert_box.configure(state="disabled")
