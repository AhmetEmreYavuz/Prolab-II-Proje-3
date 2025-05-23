# gui/glucose_history.py
import tkinter as tk
import ttkbootstrap as ttk
from utils.db import db_cursor
from datetime import datetime, timedelta

class GlucoseHistoryWindow(tk.Toplevel):
    """Seçilen hastanın geçmiş kan şekeri ölçümlerini gösterir."""
    COLS = ("dt", "value")

    def __init__(self, master, patient_id: int, full_name: str):
        super().__init__(master)
        self.title(f"Glukoz Geçmişi – {full_name}")
        self.geometry("500x500")

        # Tarih filtresi
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="Son kaç gün:", font=("Segoe UI", 10)).pack(side="left")
        self.days_var = tk.IntVar(value=30)
        ttk.Spinbox(top_frame, from_=1, to=365, width=5, textvariable=self.days_var).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Göster", command=lambda: self._load()).pack(side="left", padx=5)

        # Treeview
        tree = ttk.Treeview(self, columns=self.COLS, show="headings", height=18, bootstyle="info")
        tree.heading("dt", text="Tarih/Saat")
        tree.heading("value", text="Değer (mg/dL)")
        tree.column("dt", width=180, anchor="center")
        tree.column("value", width=120, anchor="center")
        tree.pack(expand=True, fill="both", padx=10, pady=(0,10))
        self.tree = tree

        self.patient_id = patient_id
        self._load()

    def _load(self):
        days = self.days_var.get() or 30
        since = datetime.now() - timedelta(days=days)
        self.tree.delete(*self.tree.get_children())
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT reading_dt, value_mg_dl
                FROM glucose_readings
                WHERE patient_id=%s AND reading_dt >= %s
                ORDER BY reading_dt DESC
                """,
                (self.patient_id, since)
            )
            for row in cur:
                dt_str = row["reading_dt"].strftime("%d-%m-%Y %H:%M:%S")
                self.tree.insert("", tk.END, values=(dt_str, f"{row['value_mg_dl']:.1f}")) 