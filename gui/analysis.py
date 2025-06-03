# gui/analysis.py
import tkinter as tk
import ttkbootstrap as ttk
from utils.db import db_cursor
from datetime import date, timedelta, datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib

matplotlib.use("TkAgg")


class AnalysisWindow(tk.Toplevel):
    """İstatistik ve analizler (grafiksel gösterimlerle)."""

    def __init__(self, master, patient_id: int, full_name: str):
        super().__init__(master)
        self.title(f"Analiz – {full_name}")
        self.geometry("900x600")  # Daha büyük pencere
        self.patient_id = patient_id
        self.full_name = full_name


        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)


        stats_frame = ttk.Frame(notebook, padding=15)
        notebook.add(stats_frame, text="İstatistikler")


        glucose_frame = ttk.Frame(notebook, padding=15)
        notebook.add(glucose_frame, text="Kan Şekeri Grafikleri")


        compliance_frame = ttk.Frame(notebook, padding=15)
        notebook.add(compliance_frame, text="Diyet & Egzersiz")


        self._create_stats_tab(stats_frame)


        self._create_glucose_graphs(glucose_frame)


        self._create_compliance_graphs(compliance_frame)

    def _create_stats_tab(self, frame):
        """Temel istatistikleri göster - mevcut kod"""
        ttk.Label(frame, text="Son 30 Günlük Kan Şekeri İstatistikleri", font=("Segoe UI", 12, "bold")).pack(
            pady=(0, 10))

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
                (self.patient_id,)
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
        ttk.Label(frame, text="\nSon 30 Günlük Diyet & Egzersiz Uyum Oranı", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", pady=(10, 5))
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT SUM(diet_done) AS diet_ok, SUM(exercise_done) AS ex_ok, COUNT(*) AS days
                FROM daily_status
                WHERE patient_id=%s AND day >= CURDATE() - INTERVAL 30 DAY
                """,
                (self.patient_id,)
            )
            res = cur.fetchone()
        if res and res["days"]:
            diet_rate = 100 * res["diet_ok"] / res["days"] if res["days"] else 0
            ex_rate = 100 * res["ex_ok"] / res["days"] if res["days"] else 0
            ttk.Label(frame, text=f"Diyet uyumu:     {diet_rate:.0f}%").pack(anchor="w", pady=2)
            ttk.Label(frame, text=f"Egzersiz uyumu: {ex_rate:.0f}%").pack(anchor="w", pady=2)
        else:
            ttk.Label(frame, text="Bu dönemde veri yok.").pack(anchor="w", pady=5)

    def _create_glucose_graphs(self, frame):


        control_frame = ttk.Frame(frame)
        control_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(control_frame, text="Zaman aralığı:").pack(side="left", padx=(0, 10))
        self.days_var = tk.IntVar(value=30)
        days_combo = ttk.Combobox(control_frame, textvariable=self.days_var, width=10,
                                  values=(7, 14, 30, 90))
        days_combo.pack(side="left", padx=(0, 10))
        ttk.Label(control_frame, text="gün").pack(side="left", padx=(0, 20))

        ttk.Button(control_frame, text="Yenile", command=self._refresh_glucose_graph).pack(side="left")


        self.glucose_graph_frame = ttk.Frame(frame)
        self.glucose_graph_frame.pack(fill="both", expand=True)


        self._refresh_glucose_graph()

    def _refresh_glucose_graph(self):

        for widget in self.glucose_graph_frame.winfo_children():
            widget.destroy()


        days = self.days_var.get() or 30
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)


        with db_cursor() as cur:
            cur.execute(
                """
                SELECT reading_dt, value_mg_dl
                FROM glucose_readings
                WHERE patient_id=%s AND reading_dt >= %s
                ORDER BY reading_dt
                """,
                (self.patient_id, start_date)
            )
            readings = cur.fetchall()


            cur.execute(
                """
                SELECT day, diet_type, diet_done, exercise_type, exercise_done
                FROM daily_status
                WHERE patient_id=%s AND day >= %s
                ORDER BY day
                """,
                (self.patient_id, start_date.date())
            )
            status_data = cur.fetchall()

        if not readings:
            ttk.Label(self.glucose_graph_frame,
                      text="Bu zaman aralığında veri bulunmamaktadır.").pack(pady=50)
            return


        fig, ax = plt.subplots(figsize=(8, 4))


        dates = [r["reading_dt"] for r in readings]
        values = [r["value_mg_dl"] for r in readings]


        ax.plot(dates, values, 'o-', color='blue', label='Kan Şekeri')


        ax.axhline(y=70, color='orange', linestyle='--', label='Alt Limit (70 mg/dL)')
        ax.axhline(y=180, color='red', linestyle='--', label='Üst Limit (180 mg/dL)')


        if status_data:
            diet_days = [r["day"] for r in status_data if r["diet_done"]]
            exercise_days = [r["day"] for r in status_data if r["exercise_done"]]

            if diet_days:

                for day in diet_days:
                    ax.axvline(x=day, color='green', alpha=0.3, linewidth=5)

            if exercise_days:

                for day in exercise_days:
                    ax.axvline(x=day, color='purple', alpha=0.3, linewidth=5)


        ax.set_title(f"{self.full_name} - Kan Şekeri Takibi")
        ax.set_xlabel("Tarih/Zaman")
        ax.set_ylabel("Kan Şekeri (mg/dL)")
        ax.legend(loc='upper right')
        ax.grid(True, linestyle='--', alpha=0.7)


        plt.xticks(rotation=45)


        canvas = FigureCanvasTkAgg(fig, master=self.glucose_graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _create_compliance_graphs(self, frame):

        days_back = 30
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT SUM(diet_done) AS diet_ok, 
                       COUNT(*) - SUM(diet_done) AS diet_missed,
                       SUM(exercise_done) AS ex_ok, 
                       COUNT(*) - SUM(exercise_done) AS ex_missed,
                       COUNT(*) AS total_days
                FROM daily_status
                WHERE patient_id=%s AND day >= %s
                """,
                (self.patient_id, start_date)
            )
            compliance = cur.fetchone()

            cur.execute(
                """
                SELECT diet_type, COUNT(*) AS count
                FROM daily_status 
                WHERE patient_id=%s AND day >= %s AND diet_done = true
                GROUP BY diet_type
                """,
                (self.patient_id, start_date)
            )
            diet_types = cur.fetchall()

            cur.execute(
                """
                SELECT exercise_type, COUNT(*) AS count
                FROM daily_status 
                WHERE patient_id=%s AND day >= %s AND exercise_done = true
                GROUP BY exercise_type
                """,
                (self.patient_id, start_date)
            )
            exercise_types = cur.fetchall()

        if not compliance or not compliance["total_days"]:
            ttk.Label(frame, text="Bu zaman aralığında veri bulunmamaktadır.").pack(pady=50)
            return

        left_frame = ttk.Frame(frame)
        left_frame.pack(side="left", fill="both", expand=True)
        right_frame = ttk.Frame(frame)
        right_frame.pack(side="right", fill="both", expand=True)


        self._create_pie_chart(
            left_frame,
            [compliance["diet_ok"] or 0, compliance["diet_missed"] or 0],
            ["Yapıldı", "Yapılmadı"],
            ["green", "red"],
            "Diyet Uyumu"
        )
        self._create_pie_chart(
            right_frame,
            [compliance["ex_ok"] or 0, compliance["ex_missed"] or 0],
            ["Yapıldı", "Yapılmadı"],
            ["blue", "red"],
            "Egzersiz Uyumu"
        )


        if diet_types:
            diet_types_frame = ttk.Frame(left_frame)
            diet_types_frame.pack(fill="both", expand=True, pady=10)


            raw_labels = [row["diet_type"] for row in diet_types]
            values = [row["count"] for row in diet_types]


            diet_map = {
                "sugar_free": "Şekersiz Diyet",
                "balanced": "Dengeli Beslenme",
                "low_sugar": "Az Şekerli Diyet",
            }
            labels = [diet_map.get(lbl, lbl) for lbl in raw_labels]

            self._create_bar_chart(
                diet_types_frame,
                labels,
                values,
                "Diyet Türleri Dağılımı"
            )


        if exercise_types:
            ex_types_frame = ttk.Frame(right_frame)
            ex_types_frame.pack(fill="both", expand=True, pady=10)

            raw_labels = [row["exercise_type"] for row in exercise_types]
            values = [row["count"] for row in exercise_types]

            ex_map = {
                "walk": "Yürüyüş",
                "bike": "Bisiklet",
                "clinic": "Klinik Egzersiz",
            }
            labels = [ex_map.get(lbl, lbl) for lbl in raw_labels]

            self._create_bar_chart(
                ex_types_frame,
                labels,
                values,
                "Egzersiz Türleri Dağılımı"
            )

    def _create_pie_chart(self, parent, values, labels, colors, title):

        fig, ax = plt.subplots(figsize=(4, 3))


        total = sum(values)
        percentages = [100 * val / total if total else 0 for val in values]


        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )


        ax.set_title(title)


        for text in autotexts:
            text.set_color('white')
            text.set_fontweight('bold')

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _create_bar_chart(self, parent, labels, values, title):

        fig, ax = plt.subplots(figsize=(4, 3))


        bars = ax.bar(labels, values, color='skyblue')


        for i, v in enumerate(values):
            ax.text(i, v + 0.1, str(v), ha='center')


        ax.set_title(title)
        ax.set_ylabel('Gün Sayısı')


        plt.xticks(rotation=45 if len(labels) > 3 else 0)


        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True) 