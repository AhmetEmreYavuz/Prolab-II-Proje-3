# gui/analysis.py
import tkinter as tk
import ttkbootstrap as ttk
from utils.db import db_cursor
from datetime import date, timedelta

class AnalysisWindow(tk.Toplevel):
    """Basit istatistik ve analizler."""
    def __init__(self, master, patient_id: int, full_name: str):
        super().__init__(master)
        self.title(f"Analiz – {full_name}")
        self.geometry("450x300")
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Son 30 Günlük Kan Şekeri İstatistikleri", font=("Segoe UI", 12, "bold")).pack(pady=(0,10))

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT AVG(value_mg_dl) AS avg_glucose,
                       MIN(value_mg_dl) AS min_g,
                       MAX(value_mg_dl) AS max_g,
                       COUNT(*)          AS cnt
                FROM glucose_readings
                WHERE patient_id=%s AND reading_dt >= CURDATE() - INTERVAL 30 DAY
                """,
                (patient_id,)
            )
            stats = cur.fetchone()

        if stats and stats["cnt"]:
            ttk.Label(frame, text=f"Ölçüm Sayısı: {stats['cnt']}").pack(anchor="w", pady=2)
            ttk.Label(frame, text=f"Ortalama: {stats['avg_glucose']:.1f} mg/dL").pack(anchor="w", pady=2)
            ttk.Label(frame, text=f"Minimum:  {stats['min_g']:.1f} mg/dL").pack(anchor="w", pady=2)
            ttk.Label(frame, text=f"Maksimum: {stats['max_g']:.1f} mg/dL").pack(anchor="w", pady=2)
        else:
            ttk.Label(frame, text="Bu dönemde ölçüm yok.").pack(anchor="w", pady=5)

        # Diyet / egzersiz uyum oranı
        ttk.Label(frame, text="\nSon 30 Günlük Diyet & Egzersiz Uyum Oranı", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10,5))
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT SUM(diet_done) AS diet_ok, SUM(exercise_done) AS ex_ok, COUNT(*) AS days
                FROM daily_status
                WHERE patient_id=%s AND day >= CURDATE() - INTERVAL 30 DAY
                """,
                (patient_id,)
            )
            res = cur.fetchone()
        if res and res["days"]:
            diet_rate = 100*res["diet_ok"] / res["days"] if res["days"] else 0
            ex_rate   = 100*res["ex_ok"]   / res["days"] if res["days"] else 0
            ttk.Label(frame, text=f"Diyet uyumu:     {diet_rate:.0f}%").pack(anchor="w", pady=2)
            ttk.Label(frame, text=f"Egzersiz uyumu: {ex_rate:.0f}%").pack(anchor="w", pady=2)
        else:
            ttk.Label(frame, text="Bu dönemde veri yok.").pack(anchor="w", pady=5) 