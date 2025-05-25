# gui/status.py
import tkinter as tk
from tkinter import ttk
from utils.db import db_cursor


class StatusWindow(tk.Toplevel):
    """Seçilen hastanın son 30 günlük diyet / egzersiz durumlarını gösterir."""

    COLS = ("day", "diet_type", "diet_done", "exercise_type", "exercise_done")

    def __init__(self, master, patient_id: int, full_name: str):
        super().__init__(master)
        self.patient_id = patient_id
        self.full_name = full_name
        self.title(f"Günlük Durum – {full_name}")
        self.geometry("600x400")
        
        # Header frame
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill="x")
        
        ttk.Label(
            header_frame,
            text=f"📊 {full_name} - Diyet & Egzersiz Takibi",
            font=("Segoe UI", 14, "bold"),
            bootstyle="primary"
        ).pack(side="left")
        
        ttk.Button(
            header_frame,
            text="🔄 Yenile",
            bootstyle="info-outline",
            command=self._refresh_data,
            width=12
        ).pack(side="right")

        # Treeview
        self.tree = ttk.Treeview(self, columns=self.COLS, show="headings", height=15)
        hdrs = ["📅 Tarih", "🥗 Diyet", "✅ Uygulandı", "🏃 Egzersiz", "✅ Yapıldı"]
        for col, text in zip(self.COLS, hdrs):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=110, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack components
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10, padx=(0, 10))
        
        # Load initial data
        self._refresh_data()
        
        # Auto-refresh every 30 seconds
        self.after(30000, self._auto_refresh)

    def _refresh_data(self):
        """Verileri yeniden yükle."""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Load fresh data
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT day, diet_type, diet_done, exercise_type, exercise_done
                FROM daily_status
                WHERE patient_id=%s
                  AND day >= CURDATE() - INTERVAL 30 DAY
                ORDER BY day DESC
                """,
                (self.patient_id,),
            )
            rows = cur.fetchall()
            
            if not rows:
                # No data message
                self.tree.insert("", tk.END, values=("Veri yok", "", "", "", ""))
            else:
                for row in rows:
                    # Color coding for better visibility
                    diet_status = "✅ Evet" if row["diet_done"] else "❌ Hayır"
                    exercise_status = "✅ Evet" if row["exercise_done"] else "❌ Hayır"
                    
                    item = self.tree.insert(
                        "", tk.END,
                        values=(
                            row["day"].strftime("%d.%m.%Y"),
                            row["diet_type"].title(),
                            diet_status,
                            row["exercise_type"].title(),
                            exercise_status,
                        ),
                    )
                    
                    # Row coloring based on compliance
                    if row["diet_done"] and row["exercise_done"]:
                        self.tree.set(item, "day", f"🟢 {row['day'].strftime('%d.%m.%Y')}")
                    elif row["diet_done"] or row["exercise_done"]:
                        self.tree.set(item, "day", f"🟡 {row['day'].strftime('%d.%m.%Y')}")
                    else:
                        self.tree.set(item, "day", f"🔴 {row['day'].strftime('%d.%m.%Y')}")
    
    def _auto_refresh(self):
        """Otomatik yenileme."""
        if self.winfo_exists():
            self._refresh_data()
            self.after(30000, self._auto_refresh)