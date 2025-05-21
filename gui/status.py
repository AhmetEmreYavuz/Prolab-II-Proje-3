# gui/status.py
import tkinter as tk
from tkinter import ttk
from utils.db import db_cursor


class StatusWindow(tk.Toplevel):
    """Seçilen hastanın son 30 günlük diyet / egzersiz durumlarını gösterir."""

    COLS = ("day", "diet_type", "diet_done", "exercise_type", "exercise_done")

    def __init__(self, master, patient_id: int, full_name: str):
        super().__init__(master)
        self.title(f"Günlük Durum – {full_name}")
        self.geometry("520x350")

        tree = ttk.Treeview(self, columns=self.COLS, show="headings", height=15)
        hdrs = ["Tarih", "Diyet", "Uygulandı", "Egzersiz", "Yapıldı"]
        for col, text in zip(self.COLS, hdrs):
            tree.heading(col, text=text)
            tree.column(col, width=95, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT day, diet_type, diet_done, exercise_type, exercise_done
                FROM daily_status
                WHERE patient_id=%s
                  AND day >= CURDATE() - INTERVAL 30 DAY
                ORDER BY day DESC
                """,
                (patient_id,),
            )
            for row in cur:
                tree.insert(
                    "", tk.END,
                    values=(
                        row["day"],
                        row["diet_type"],
                        "Evet" if row["diet_done"] else "Hayır",
                        row["exercise_type"],
                        "Evet" if row["exercise_done"] else "Hayır",
                    ),
                )
