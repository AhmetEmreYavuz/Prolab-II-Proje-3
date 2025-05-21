# gui/patient.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from services.glucose import add_glucose, list_today
from services.rules import evaluate_day
from services.daily import upsert_status



class PatientWindow(tk.Toplevel):
    def __init__(self, master, patient_id: int):
        super().__init__(master)
        self.title("Hasta Paneli")
        self.geometry("320x260")
        self.patient_id = patient_id

        # ---------- Ölçüm girişi ----------
        frame = ttk.LabelFrame(self, text="Yeni Ölçüm")
        frame.pack(padx=12, pady=10, fill="x")

        ttk.Label(frame, text="Değer (mg/dL):").grid(row=0, column=0, padx=6, pady=6)
        self.val_entry = ttk.Entry(frame, width=10)
        self.val_entry.grid(row=0, column=1, padx=6, pady=6)

        ttk.Button(frame, text="Kaydet", command=self._save_reading)\
            .grid(row=0, column=2, padx=6, pady=6)

        # --- Diyet & Egzersiz girişi -------------------------
        st = ttk.LabelFrame(self, text="Diyet / Egzersiz")
        st.pack(padx=12, fill="x")

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


        # ---------- Günlük özet ----------
        self.sum_lbl = ttk.Label(self, text="", font=("Segoe UI", 11, "bold"))
        self.sum_lbl.pack(pady=8)

        self.alerts_box = tk.Text(self, height=5, state="disabled")
        self.alerts_box.pack(padx=10, fill="both", expand=True)

        self._refresh_summary()

    # ----------------------------
    def _save_reading(self):
        try:
            value = float(self.val_entry.get())
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz sayı.")
            return

        add_glucose(self.patient_id, value)
        self.val_entry.delete(0, tk.END)
        self._refresh_summary()

    # ----------------------------
    def _refresh_summary(self):
        # ölçümleri listele
        readings = list_today(self.patient_id)
        if readings:
            avg = sum(r["value_mg_dl"] for r in readings) / len(readings)
            self.sum_lbl.config(text=f"Bugünkü ölçüm sayısı: {len(readings)}  •  Ortalama: {avg:.1f} mg/dL")
        else:
            self.sum_lbl.config(text="Bugün henüz ölçüm yok.")

        # günlük evaluate → doz & gerekirse alert
        evaluate_day(self.patient_id, day=date.today())

        # son uyarıları getir
        from utils.db import db_cursor
        with db_cursor() as cur:
            cur.execute(
                "SELECT created_dt, message FROM alerts "
                "WHERE patient_id=%s ORDER BY created_dt DESC LIMIT 5",
                (self.patient_id,)
            )
            alerts = cur.fetchall()

        self.alerts_box.configure(state="normal")
        self.alerts_box.delete("1.0", tk.END)
        for a in alerts:
            self.alerts_box.insert(tk.END, f"{a['created_dt'].strftime('%H:%M')} - {a['message']}\n")
        self.alerts_box.configure(state="disabled")

        # ------------------------- Diyet/egzersiz kaydet
        def _save_status(self):
            upsert_status(
                self.patient_id,
                self.diet_cmb.get(), self.diet_chk.get(),
                self.ex_cmb.get(), self.ex_chk.get()
            )
            messagebox.showinfo("Bilgi", "Günlük durum kaydedildi.")

