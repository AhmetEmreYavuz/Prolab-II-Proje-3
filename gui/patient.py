# gui/patient.py
import tkinter as tk
import ttkbootstrap as ttk
from datetime import date, datetime, time
from services.glucose import add_glucose, list_today, list_for_date
from tkinter import TclError
from services.symptom import list_symptoms  # 追加
from ttkbootstrap.scrolled import ScrolledFrame   # +++ EKLENDİ +++
from gui.status import StatusWindow

from services.rules import evaluate_day
from services.patient import get_profile_image
from utils.db import db_cursor
from PIL import Image, ImageTk
import io


SLOT_RANGES = {
    "sabah":  (time(7, 0),  time(8, 0)),
    "ogle":   (time(12, 0), time(13, 0)),
    "ikindi": (time(15, 0), time(16, 0)),
    "aksam":  (time(18, 0), time(19, 0)),
    "gece":   (time(22, 0), time(23, 0)),
}

SLOT_ORDER = ["sabah", "ogle", "ikindi", "aksam", "gece"]



class PatientWindow(tk.Toplevel):
    """Modern hasta paneli – dashboard ve navigation sistemi."""


    def __init__(self, master, patient_id: int, skip_password_change: bool = False):
        super().__init__(master)
        self.patient_id = patient_id
        self.master_window = master
        self.title("💊 Hasta Paneli")
        self.geometry("1400x900")
        self.configure(bg="#2b3e50")


        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")




        self._load_patient_info(skip_password_change)


        try:
            self._create_dashboard()
        except TclError as e:
            if "Horizontal.TScrollbar.thumb" in str(e):

                return

            raise

    #   HASTA ADI & İLK ŞİFRE KONTROLÜ

    def _load_patient_info(self, skip_password_change: bool):
        try:
            with db_cursor() as cur:
                cur.execute(
                    "SELECT full_name, password_change_needed "
                    "FROM users WHERE id=%s", (self.patient_id,))
                row = cur.fetchone() or {}
                self.patient_name = row.get("full_name", "Hasta")

                if not skip_password_change and row.get("password_change_needed"):
                    from gui.change_password import ChangePasswordDialog
                    self.after(
                        100,
                        lambda: ChangePasswordDialog(
                            self, self.patient_id, is_first_login=True
                        ),
                    )
                    cur.execute(
                        "UPDATE users SET password_change_needed=0 WHERE id=%s",
                        (self.patient_id,),
                    )
        except Exception as err:
            print("Hasta bilgisi alınamadı:", err)
            self.patient_name = "Hasta"


    def _create_dashboard(self):



        for w in self.winfo_children():
            w.destroy()


        self.scroll_fr = ScrolledFrame(self, autohide=True)
        self.scroll_fr.pack(fill="both", expand=True)


        interior = getattr(self.scroll_fr, "scrollable_frame", self.scroll_fr)


        main = ttk.Frame(interior, padding=20)
        main.pack(fill="both", expand=True)


        self._create_header(main)
        self._create_dashboard_grid(main)
        self._create_footer(main)

        self._refresh_dashboard()
        self.scroll_fr.update_idletasks()


    def _create_header(self, parent):
        hdr = ttk.Frame(parent)
        hdr.pack(fill="x", pady=(0, 25))


        wrapper = ttk.Frame(hdr, width=100, height=100)
        wrapper.pack(side="left", padx=(0, 20))
        wrapper.pack_propagate(False)
        self.profile_lbl = ttk.Label(wrapper)
        self.profile_lbl.pack(fill="both", expand=True)
        self._load_profile_image()


        box = ttk.Frame(hdr)
        box.pack(side="left", fill="x", expand=True)

        ttk.Label(
            box,
            text=f"🏥 Hasta Dashboard - {self.patient_name}",
            font=("Segoe UI", 22, "bold"),
            bootstyle="primary",
        ).pack(anchor="w")

        today_str = datetime.now().strftime("%d %B %Y")
        ttk.Label(
            box,
            text=f"📅 Bugün: {today_str} | Sağlık takip ve yönetim sistemi",
            font=("Segoe UI", 12),
            bootstyle="secondary",
        ).pack(anchor="w", pady=(5, 0))


    def _create_dashboard_grid(self, parent):
        grid = ttk.Frame(parent)
        grid.pack(fill="both", expand=True)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=1)
        grid.rowconfigure(1, weight=1)

        self._create_glucose_card(grid)     # (0,0)
        self._create_summary_card(grid)     # (0,1)
        self._create_lifestyle_card(grid)   # (1,0)
        self._create_actions_card(grid)     # (1,1)


    def _create_glucose_card(self, parent):
        card = ttk.LabelFrame(
            parent, text="📊 Kan Şekeri Takibi", padding=20, bootstyle="info"
        )
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))

        ttk.Label(
            card,
            text="🩸 Yeni Ölçüm Ekle",
            font=("Segoe UI", 14, "bold"),
            bootstyle="primary",
        ).pack(anchor="w", pady=(0, 10))


        inp = ttk.Frame(card)
        inp.pack(fill="x", pady=(0, 10))

        ttk.Label(inp, text="💉 Değer (mg/dL):", font=("Segoe UI", 11, "bold")).pack(side="left")
        self.val_ent = ttk.Entry(inp, font=("Segoe UI", 12), width=8)
        self.val_ent.pack(side="left", padx=(5, 15))

        ttk.Label(inp, text="📅 Tarih (GG.AA.YYYY):", font=("Segoe UI", 11)).pack(side="left")
        self.date_ent = ttk.Entry(inp, width=12, font=("Segoe UI", 11))
        self.date_ent.insert(0, date.today().strftime("%d.%m.%Y"))
        self.date_ent.pack(side="left", padx=(5, 15))

        ttk.Label(inp, text="⏰ Saat (HH:MM:SS):", font=("Segoe UI", 11)).pack(side="left")
        self.time_ent = ttk.Entry(inp, width=9, font=("Segoe UI", 11))
        self.time_ent.insert(0, datetime.now().strftime("%H:%M:%S"))
        self.time_ent.pack(side="left", padx=(5, 15))

        ttk.Label(inp, text="🕒 Vakit:", font=("Segoe UI", 11)).pack(side="left")
        self.slot_var = tk.StringVar(value="sabah")
        slot_fr = ttk.Frame(inp)
        slot_fr.pack(side="left", padx=(5, 0))
        for txt, val in [
            ("Sabah", "sabah"),
            ("Öğle", "ogle"),
            ("İkindi", "ikindi"),
            ("Akşam", "aksam"),
            ("Gece", "gece"),
            ("Ayrı", "extra"),
        ]:
            ttk.Radiobutton(
                slot_fr, text=txt, variable=self.slot_var, value=val, bootstyle="info"
            ).pack(side="left", padx=2)


        btn_fr = ttk.Frame(card)
        btn_fr.pack(anchor="w", pady=(5, 15))

        ttk.Button(
            btn_fr, text="💾 Kaydet", bootstyle="success",
            width=18, command=self._save_glucose
        ).pack(side="left", padx=(0, 10))

        self.endday_btn = ttk.Button(
            btn_fr, text="📅 Gün Sonu", bootstyle="warning",
            width=18, command=self._end_day
        )
        self.endday_btn.pack(side="left")


        self.glucose_summary_frame = ttk.Frame(card)
        self.glucose_summary_frame.pack(fill="x", pady=(0, 10))
        self._build_today_history(card)


    def _build_today_history(self, parent):
        frm = ttk.Frame(parent)
        frm.pack(fill="both", expand=True)

        ttk.Label(
            frm, text="📈 Bugünkü Ölçümler", font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))

        cols = ("time", "value", "status")
        self.history_tree = ttk.Treeview(
            frm, columns=cols, show="headings", height=8, bootstyle="info"
        )
        self.history_tree.heading("time", text="⏰ Saat")
        self.history_tree.heading("value", text="📊 Değer")
        self.history_tree.heading("status", text="🎯 Durum")
        self.history_tree.column("time", width=80, anchor="center")
        self.history_tree.column("value", width=100, anchor="center")
        self.history_tree.column("status", width=120, anchor="center")

        scr = ttk.Scrollbar(frm, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scr.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        scr.pack(side="right", fill="y")


    def _create_summary_card(self, parent):
        card = ttk.LabelFrame(
            parent, text="📋 Günlük Özet", padding=20, bootstyle="success"
        )
        card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))
        self.summary_content_frame = ttk.Frame(card)
        self.summary_content_frame.pack(fill="both", expand=True)



    def _create_lifestyle_card(self, parent):

        from datetime import date
        lifestyle_card = ttk.LabelFrame(
            parent, text="🍎 Diyet ve Egzersiz",
            padding=20, bootstyle="warning"
        )
        lifestyle_card.grid(row=1, column=0, sticky="nsew",
                            padx=(0, 10), pady=(10, 0))


        diet_sec = ttk.LabelFrame(
            lifestyle_card, text="🥗 Diyet Planı",
            padding=15, bootstyle="info"
        )
        diet_sec.pack(fill="x", pady=(0, 15))

        ttk.Label(diet_sec, text="📋 Diyet Türü:",
                  font=("Segoe UI", 11, "bold")
                  ).pack(anchor="w", pady=(0, 5))

        row = ttk.Frame(diet_sec)
        row.pack(fill="x", pady=(0, 10))

        self.diet_cmb = ttk.Combobox(
            row, state="readonly", font=("Segoe UI", 11),
            values=("🚫 Şekersiz", "⚖️ Dengeli", "🥦 Düşük Şeker")
        )
        self.diet_cmb.current(0)
        self.diet_cmb.pack(side="left", padx=(0, 10))

        self.diet_chk = tk.BooleanVar()
        ttk.Checkbutton(
            row, text="✅ Uygulandı",
            variable=self.diet_chk, bootstyle="round-toggle"
        ).pack(side="left")


        ex_sec = ttk.LabelFrame(
            lifestyle_card, text="🏃 Egzersiz Planı",
            padding=15, bootstyle="secondary"
        )
        ex_sec.pack(fill="x", pady=(0, 15))

        ttk.Label(ex_sec, text="🎯 Egzersiz Türü:",
                  font=("Segoe UI", 11, "bold")
                  ).pack(anchor="w", pady=(0, 5))

        row2 = ttk.Frame(ex_sec)
        row2.pack(fill="x", pady=(0, 10))

        self.ex_cmb = ttk.Combobox(
            row2, state="readonly", font=("Segoe UI", 11),
            values=("🚶 Yürüyüş", "🚴 Bisiklet", "🏥 Klinik Egzersiz")
        )
        self.ex_cmb.current(0)
        self.ex_cmb.pack(side="left", padx=(0, 10))

        self.ex_chk = tk.BooleanVar()
        ttk.Checkbutton(
            row2, text="✅ Yapıldı",
            variable=self.ex_chk, bootstyle="round-toggle"
        ).pack(side="left")


        ttk.Separator(lifestyle_card, orient="horizontal").pack(fill="x", pady=(10, 10))
        ttk.Label(
            lifestyle_card, text="📅 Durum Tarihi (GG.AA.YYYY):",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")
        self.status_date_ent = ttk.Entry(
            lifestyle_card, font=("Segoe UI", 11), width=12
        )
        self.status_date_ent.insert(0, date.today().strftime("%d.%m.%Y"))
        self.status_date_ent.pack(anchor="w", pady=(0, 15))


        ttk.Button(
            lifestyle_card, text="💾 Durum Kaydet",
            command=self._save_status, bootstyle="success", width=20
        ).pack(pady=(0, 10))


        suggest_fr = ttk.LabelFrame(
            lifestyle_card,
            text="📑 Diyet Planı ve Egzersiz Önerisi",
            padding=15, bootstyle="primary"
        )
        suggest_fr.pack(fill="x", pady=(15, 0))

        self.suggest_lbl = ttk.Label(
            suggest_fr, text="—",
            font=("Segoe UI", 11),
            bootstyle="secondary",
            justify="left", wraplength=500
        )
        self.suggest_lbl.pack(anchor="w")


        ttk.Button(
            suggest_fr,
            text="💡 Plan Önerisi",
            bootstyle="primary-outline",
            width=18,
            command=self._show_plan_suggestion
        ).pack(anchor="e", pady=(8, 0))


    def _create_actions_card(self, parent):

        card = ttk.LabelFrame(
            parent, text="⚡ Hızlı İşlemler", padding=20, bootstyle="primary"
        )
        card.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))

        for col in (0, 1):
            card.columnconfigure(col, weight=1)

        actions = [
            ("📊 Glukoz Geçmişi", "info", self._show_history, 0, 0),
            ("📈 Analiz Raporu", "success", self._show_analysis, 0, 1),
            ("💉 İnsülin Önerisi", "warning", self._show_insulin_suggestion, 1, 0),
            ("🔄 Yenile", "secondary", self._refresh_dashboard, 1, 1),
            ("📋 Günlük Durum", "warning", self._show_status, 2, 0),
            ("🔒 Şifre Değiştir", "danger", self._change_password, 2, 1),
        ]

        for text, style, cmd, r, c in actions:
            ttk.Button(
                card,
                text=text,
                bootstyle=f"{style}-outline",
                command=cmd,
                width=18,
            ).grid(row=r, column=c, padx=5, pady=5, sticky="ew")




        tips_frame = ttk.Frame(card)
        tips_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(15, 0))

        ttk.Label(
            tips_frame,
            text="💡 İpucu ve Öneriler",
            font=("Segoe UI", 12, "bold"),
            bootstyle="primary",
        ).pack(anchor="w", pady=(0, 10))

        self.tips_label = ttk.Label(
            tips_frame,
            text=(
                "• Günde en az 3 kez ölçüm yapın\n"
                "• Diyet planınıza sadık kalın\n"
                "• Düzenli egzersiz yapmayı unutmayın"
            ),
            font=("Segoe UI", 10),
            bootstyle="secondary",
            justify="left",
        )
        self.tips_label.pack(anchor="w")


        self.symptom_lbl = ttk.Label(
            tips_frame,
            text="Hastadaki belirtiler: —",
            font=("Segoe UI", 10),
            bootstyle="secondary",
            justify="left"
        )
        self.symptom_lbl.pack(anchor="w", pady=(8, 0))


        self._update_symptom_info()


    def _create_footer(self, parent):
        f = ttk.Frame(parent)
        f.pack(fill="x")
        ttk.Label(
            f,
            text="© 2025 Diyabet Takip Sistemi - Hasta Paneli",
            font=("Segoe UI", 9),
            bootstyle="secondary",
        ).pack(side="left")
        ttk.Button(
            f, text="❌ Çıkış", bootstyle="danger-outline", width=15, command=self.destroy
        ).pack(side="right")


    def _load_profile_image(self):
        data = get_profile_image(self.patient_id)
        try:
            if data:
                img = Image.open(io.BytesIO(data))
                img.thumbnail((90, 90))
                ph = ImageTk.PhotoImage(img)
                self.profile_lbl.config(image=ph)
                self.profile_lbl.image = ph
            else:
                self.profile_lbl.config(text="👤", font=("Segoe UI", 40), foreground="white")
        except Exception as err:
            print("Profil resmi hatası:", err)
            self.profile_lbl.config(text="👤", font=("Segoe UI", 40), foreground="white")



    def _save_glucose(self):

        try:

            dt_txt = f"{self.date_ent.get().strip()} {self.time_ent.get().strip()}"
            dt = datetime.strptime(dt_txt, "%d.%m.%Y %H:%M:%S")


            if getattr(self, "closed_date", None) == dt.date():
                ttk.dialogs.Messagebox.show_warning(
                    "Bu gün için 'Gün Sonu' yapıldı; yeni ölçüm ekleyemezsiniz.",
                    "Gün Kapalı",
                    parent=self,
                )
                return


            value = float(self.val_ent.get().strip().replace(",", "."))
            if value <= 0:
                raise ValueError("Pozitif değer giriniz.")


            slot = self.slot_var.get()
            if slot in SLOT_RANGES:
                lo, hi = SLOT_RANGES[slot]
                if not (lo <= dt.time() <= hi):
                    ttk.dialogs.Messagebox.show_error(
                        f"Seçilen vakit ({slot.capitalize()}) ile saat uyuşmuyor!",
                        "Zaman Uyumsuzluğu",
                        parent=self,
                    )
                    return
            else:
                ttk.dialogs.Messagebox.show_warning(
                    "Bu ölçüm izinli saat aralığının dışında.\n"
                    "Kaydedildi ama ortalamaya dahil edilmeyecek.",
                    "Uyarı",
                    parent=self,
                )


            add_glucose(self.patient_id, value, dt)
            self.val_ent.delete(0, tk.END)
            self._refresh_dashboard()

        except Exception as err:
            ttk.dialogs.Messagebox.show_error(
                f"Hata:\n{err}", "Kayıt Hatası", parent=self
            )


    def _save_status(self):

        from datetime import datetime


        date_str = self.status_date_ent.get().strip()
        try:
            day = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            ttk.dialogs.Messagebox.show_error(
                "Geçersiz tarih formatı! Lütfen GG.AA.YYYY biçiminde girin.",
                "Hata",
                parent=self
            )
            return


        diet_map = {
            "🚫 Şekersiz": "sugar_free",
            "⚖️ Dengeli": "balanced",
            "🥦 Düşük Şeker": "low_sugar",
        }
        ex_map = {
            "🚶 Yürüyüş": "walk",
            "🚴 Bisiklet": "bike",
            "🏥 Klinik Egzersiz": "clinic",
        }
        diet_type = diet_map.get(self.diet_cmb.get(), "balanced")
        exercise_type = ex_map.get(self.ex_cmb.get(), "walk")
        diet_done = self.diet_chk.get()
        exercise_done = self.ex_chk.get()


        from services.daily import upsert_status
        upsert_status(
            self.patient_id,
            diet_type,
            diet_done,
            exercise_type,
            exercise_done,
            day
        )


        ttk.dialogs.Messagebox.show_info(
            f"{day.strftime('%d.%m.%Y')} için durum kaydedildi.",
            "Başarılı",
            parent=self
        )


    def _refresh_dashboard(self):

        readings = list_for_date(self.patient_id, self.current_date) or []


        for item_id in self.history_tree.get_children():
            self.history_tree.delete(item_id)
        for w in self.summary_content_frame.winfo_children():
            w.destroy()


        if not readings:
            ttk.Label(
                self.summary_content_frame,
                text="📝 Henüz ölçüm yok",
                font=("Segoe UI", 14, "bold"),
                bootstyle="warning",
            ).pack(pady=(20, 10))
            evaluate_day(self.patient_id, date.today())
            return


        slot_avgs, slot_vals = self._compute_slot_averages(readings)


        missing = [s.capitalize() for s, v in slot_vals.items() if not v]
        if missing:
            ttk.dialogs.Messagebox.show_warning(
                "Ölçüm eksik! " + ", ".join(missing) +
                " vakit(ler)inde ölçüm yok – ortalamaya katılmadı.",
                "Eksik Ölçüm", parent=self
            )


        if len(readings) <= 3:
            ttk.dialogs.Messagebox.show_warning(
                "Yetersiz veri! Ortalama hesaplaması güvenilir değildir.",
                "Uyarı", parent=self
            )


        def _row(frm, label, value):
            r = ttk.Frame(frm);
            r.pack(fill="x", pady=2)
            ttk.Label(r, text=label, font=("Segoe UI", 11, "bold")
                      ).pack(side="left")
            ttk.Label(r, text=value, font=("Segoe UI", 11),
                      bootstyle="primary").pack(side="right")

        sum_fr = ttk.Frame(self.summary_content_frame);
        sum_fr.pack(fill="x")
        ttk.Label(
            sum_fr, text="📊 Vakit Ortalamaları",
            font=("Segoe UI", 14, "bold"), bootstyle="success"
        ).pack(anchor="w", pady=(0, 10))

        for s in SLOT_ORDER:
            avg_val = slot_avgs[s]
            _row(
                sum_fr,
                f"{s.capitalize()}:",
                f"{avg_val:.1f} mg/dL" if avg_val is not None else "—"
            )


        for r in readings:
            t_str = r["reading_dt"].strftime("%H:%M")
            val = r["value_mg_dl"]
            tag = "success" if 70 <= val <= 180 else "danger"
            self.history_tree.insert(
                "", "end",
                values=(
                    t_str,
                    f"{val:.1f}",
                    "🟢 Normal" if tag == "success" else "🔴 Anormal"
                ),
                tags=(tag,)
            )
        self.history_tree.tag_configure("danger", background="#f8d7da")
        self.history_tree.tag_configure("success", background="#d4edda")


        day_avg = sum(r["value_mg_dl"] for r in readings) / len(readings)
        self._latest_avg = day_avg

        self._update_symptom_info()
        self._update_lifestyle_suggestion(day_avg)


        evaluate_day(self.patient_id, self.current_date)


        if hasattr(self, "scroll_fr"):
            self.scroll_fr.update_idletasks()


    def _update_summary_card(self, readings, avg, min_v, max_v):
        stats_fr = ttk.Frame(self.summary_content_frame)
        stats_fr.pack(fill="x", pady=(0, 15))
        ttk.Label(
            stats_fr,
            text="📊 İstatistikler",
            font=("Segoe UI", 14, "bold"),
            bootstyle="success",
        ).pack(anchor="w", pady=(0, 10))

        for lbl, val in [
            ("📈 Ortalama:", f"{avg:.1f} mg/dL"),
            ("⬇️ En Düşük:", f"{min_v:.1f} mg/dL"),
            ("⬆️ En Yüksek:", f"{max_v:.1f} mg/dL"),
            ("🔢 Toplam Ölçüm:", f"{len(readings)} adet"),
        ]:
            row = ttk.Frame(stats_fr)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=lbl, font=("Segoe UI", 11, "bold")).pack(side="left")
            ttk.Label(row, text=val, font=("Segoe UI", 11), bootstyle="primary").pack(
                side="right"
            )


        status_fr = ttk.Frame(self.summary_content_frame)
        status_fr.pack(fill="x", pady=(15, 0))
        ttk.Label(
            status_fr,
            text="🎯 Durum",
            font=("Segoe UI", 14, "bold"),
            bootstyle="success",
        ).pack(anchor="w", pady=(0, 10))

        if avg < 70:
            txt, st = "⚠️ Ortalama düşük!\nDoktorunuza danışın.", "warning"
        elif avg > 180:
            txt, st = "⚠️ Ortalama yüksek!\nDiyet planınızı kontrol edin.", "danger"
        else:
            txt, st = "✅ Ortalama normal!\nBöyle devam edin.", "success"
        ttk.Label(
            status_fr, text=txt, font=("Segoe UI", 11), bootstyle=st, justify="center"
        ).pack()


    def _show_history(self):
        from gui.glucose_history import GlucoseHistoryWindow
        GlucoseHistoryWindow(self, self.patient_id, self.patient_name)

    def _show_analysis(self):
        from gui.analysis import AnalysisWindow
        AnalysisWindow(self, self.patient_id, self.patient_name)

    def _change_password(self):
        from gui.change_password import ChangePasswordDialog
        ChangePasswordDialog(self, self.patient_id)

    def _end_day(self):

        try:
            sel_day = datetime.strptime(self.date_ent.get().strip(), "%d.%m.%Y").date()
        except ValueError:
            ttk.dialogs.Messagebox.show_error("Geçersiz tarih!", "Hata", parent=self)
            return

        self.closed_date = sel_day
        self.current_date = sel_day
        self._refresh_dashboard()

        ttk.dialogs.Messagebox.show_info(
            f"{sel_day.strftime('%d.%m.%Y')} için gün sonu tamamlandı.\n"
            "Bu tarih için yeni ölçüm girişi kapatıldı.",
            "Bilgi", parent=self
        )

    def _compute_slot_averages(self, readings):


        slot_values = {s: [] for s in SLOT_ORDER}
        for rec in readings:
            tm = rec["reading_dt"].time()
            for slot, (lo, hi) in SLOT_RANGES.items():
                if lo <= tm <= hi:
                    slot_values[slot].append(rec["value_mg_dl"])
                    break


        averages, cumulative = {}, []
        for slot in SLOT_ORDER:
            cumulative.extend(slot_values[slot])
            averages[slot] = (sum(cumulative) / len(cumulative)) \
                             if cumulative else None
        return averages, slot_values


    @staticmethod
    def _dose_for_avg(avg: float | None) -> str:

        if avg is None:
            return "—"
        if avg < 70:
            return "Yok"
        if avg <= 110:
            return "Yok"
        if avg <= 150:
            return "1 ml"
        if avg <= 200:
            return "2 ml"
        return "3 ml"

    def _show_insulin_suggestion(self):


        from services.glucose import list_for_date

        target_day = getattr(self, "closed_date", date.today())
        rows = list_for_date(self.patient_id, target_day)

        if not rows:
            ttk.dialogs.Messagebox.show_warning(
                "Seçilen gün için kayıtlı ölçüm bulunamadı.",
                "Veri Yok", parent=self
            )
            return


        slot_avgs, _ = self._compute_slot_averages(rows)


        def dose_for(avg_val: float | None) -> str:
            if avg_val is None:
                return "—"
            if avg_val < 70:
                return "Yok"
            if avg_val <= 110:
                return "Yok"
            if avg_val <= 150:
                return "1 ml"
            if avg_val <= 200:
                return "2 ml"
            return "3 ml"


        lines = [f"📅 Tarih: {target_day.strftime('%d.%m.%Y')}\n"]
        for slot in SLOT_ORDER:
            avg_val = slot_avgs[slot]
            dose = dose_for(avg_val)
            disp = f"{avg_val:.1f} mg/dL" if avg_val is not None else "—"
            lines.append(f"{slot.capitalize():<6}: {disp:<12} → Önerilen doz: {dose}")

        message = "\n".join(lines)

        ttk.dialogs.Messagebox.show_info(
            message, "💉 İnsülin Doz Önerileri", parent=self
        )

    def _update_symptom_info(self):

        try:
            symptoms = list_symptoms(self.patient_id)
            if symptoms:
                txt = "Hastadaki belirtiler: " + ", ".join(symptoms)
            else:
                txt = "Hastadaki belirtiler: —"
            self.symptom_lbl.config(text=txt, bootstyle="warning" if symptoms else "secondary")
        except Exception as err:

            self.symptom_lbl.config(text=f"Semptom okunamadı: {err}", bootstyle="danger")



    def _update_lifestyle_suggestion(self, day_avg: float | None):


        from services.symptom import list_symptoms
        syms = {s.lower() for s in list_symptoms(self.patient_id)}


        if day_avg is None:
            self.suggest_lbl.config(
                text="Bugünün ölçümleri yetersiz — öneri üretilemedi.",
                bootstyle="secondary"
            )
            return


        RULES = [
            (None, 70, {"nöropati", "polifaji", "yorgunluk"},
             "⚖️ Dengeli", "—"),
            (None, 70, {"yorgunluk", "kilo kaybı"},
             "🥦 Düşük Şeker", "🚶 Yürüyüş"),
            (70, 110, {"polifaji", "polidipsi"},
             "⚖️ Dengeli", "🚶 Yürüyüş"),
            (70, 110, {"bulanık görme", "nöropati"},
             "🥦 Düşük Şeker", "🏥 Klinik Egzersiz"),
            (110, 180, {"poliüri", "polidipsi"},
             "🚫 Şekersiz", "🏥 Klinik Egzersiz"),
            (110, 180, {"yorgunluk", "nöropati", "bulanık görme"},
             "🥦 Düşük Şeker", "🚶 Yürüyüş"),
            (180, None, {"yaraların yavaş iyileşmesi", "polifaji", "polidipsi"},
             "🚫 Şekersiz", "🏥 Klinik Egzersiz"),
            (180, None, {"yaraların yavaş iyileşmesi", "kilo kaybı"},
             "🚫 Şekersiz", "🚶 Yürüyüş"),
        ]

        diet = ex = None
        for lo, hi, trig_syms, d, e in RULES:
            in_range = (lo is None or day_avg >= lo) and (hi is None or day_avg < hi)
            if in_range and syms & trig_syms:
                diet, ex = d, e
                break


        txt = ("Hastadaki belirtiler yok." if not syms else
               f"Hastadaki belirtiler: {', '.join(sorted(syms))}")

        if diet:
            txt += (f"\n\n• Önerilen Diyet: {diet}"
                    f"\n• Önerilen Egzersiz: {ex}")
            style = "primary"
        else:
            txt += "\n\n• Henüz tabloya uyan bir öneri yok."
            style = "secondary"


        self.suggest_lbl.config(text=txt, bootstyle=style)



    def _show_plan_suggestion(self):



        todays = list_today(self.patient_id)
        if not todays:
            ttk.dialogs.Messagebox.show_warning(
                "Önce bugünün ölçümlerini kaydedin / yenileyin.",
                "Veri Yok", parent=self
            )
            return
        avg = sum(r["value_mg_dl"] for r in todays) / len(todays)


        with db_cursor() as cur:
            cur.execute(
                "SELECT description FROM symptoms "
                "WHERE patient_id=%s ORDER BY noted_at DESC",
                (self.patient_id,)
            )
            syms = {row["description"].lower() for row in cur.fetchall()}


        RULES = [
            ((0, 70), {"nöropati", "polifaji", "yorgunluk"},
             ("⚖️ Dengeli Beslenme", "—")),
            ((70, 110), {"yorgunluk", "kilo kaybı"},
             ("🥦 Az Şekerli Diyet", "🚶 Yürüyüş")),
            ((70, 110), {"polifaji", "polidipsi"},
             ("⚖️ Dengeli Beslenme", "🚶 Yürüyüş")),
            ((110, 180), {"bulanık görme", "nöropati"},
             ("🥦 Az Şekerli Diyet", "🏥 Klinik Egzersiz")),
            ((110, 180), {"poliüri", "polidipsi"},
             ("🚫 Şekersiz Diyet", "🏥 Klinik Egzersiz")),
            ((110, 180), {"yorgunluk", "nöropati", "bulanık görme"},
             ("🥦 Az Şekerli Diyet", "🚶 Yürüyüş")),
            ((180, 1e9), {"yaraların yavaş iyileşmesi", "polifaji", "polidipsi"},
             ("🚫 Şekersiz Diyet", "🏥 Klinik Egzersiz")),
            ((180, 1e9), {"yaraların yavaş iyileşmesi", "kilo kaybı"},
             ("🚫 Şekersiz Diyet", "🚶 Yürüyüş")),
        ]

        diet = ex = None
        for (lo, hi), trig_syms, (d, e) in RULES:
            if lo <= avg < hi and syms & trig_syms:
                diet, ex = d, e
                break


        if diet is None:
            ttk.dialogs.Messagebox.show_info(
                "Veriler mevcut kurallarla eşleşmedi.", "Öneri Yok", parent=self
            )
            return

        self.suggest_lbl.configure(
            text=f"Diyet Planı Önerisi: {diet}\nEgzersiz Önerisi: {ex}"
        )

    def _show_status(self):

        StatusWindow(self, self.patient_id, self.patient_name)


