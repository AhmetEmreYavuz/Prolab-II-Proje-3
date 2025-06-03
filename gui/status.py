# gui/status.py
import tkinter as tk
from tkinter import ttk
from utils.db import db_cursor


DIET_DISPLAY = {
    "sugar_free": "🚫 Şekersiz",
    "balanced":   "⚖️ Dengeli",
    "low_sugar":  "🥦 Düşük Şeker",
}
EXERCISE_DISPLAY = {
    "walk":   "🚶 Yürüyüş",
    "bike":   "🚴 Bisiklet",
    "clinic": "🏥 Klinik Egzersiz",
}


class StatusWindow(tk.Toplevel):


    COLS = ("day", "diet_type", "diet_done", "exercise_type", "exercise_done")

    def __init__(self, master, patient_id: int, full_name: str):
        super().__init__(master)
        self.title(f"Günlük Durum – {full_name}")
        self.geometry("520x350")

        tree = ttk.Treeview(self, columns=self.COLS, show="headings", height=15)
        headers = ["Tarih", "Diyet", "Uygulandı", "Egzersiz", "Yapıldı"]
        for col, text in zip(self.COLS, headers):
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

                day_val = row["day"]
                day_str = day_val.strftime("%d.%m.%Y") if hasattr(day_val, "strftime") else str(day_val)


                diet_code = row["diet_type"]
                diet_txt = DIET_DISPLAY.get(diet_code, diet_code)

                ex_code = row["exercise_type"]
                ex_txt = EXERCISE_DISPLAY.get(ex_code, ex_code)


                diet_done_txt = "Evet" if row["diet_done"] else "Hayır"
                ex_done_txt = "Evet" if row["exercise_done"] else "Hayır"

                tree.insert(
                    "",
                    tk.END,
                    values=(
                        day_str,
                        diet_txt,
                        diet_done_txt,
                        ex_txt,
                        ex_done_txt,
                    ),
                )
