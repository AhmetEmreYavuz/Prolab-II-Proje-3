# gui/patient.py
import tkinter as tk
import ttkbootstrap as ttk
from datetime import date, datetime, time
from services.glucose import add_glucose, list_today
from services.daily import upsert_status
from services.rules import evaluate_day
from services.patient import get_profile_image
from utils.db import db_cursor
from PIL import Image, ImageTk
import io

# -----------------------------------------------------------------------------#
#  Slot aralıkları: vakit -> (başlangıç, bitiş) 24 saat formatında
# -----------------------------------------------------------------------------#
SLOT_RANGES = {
    "sabah":  (time(7, 0),  time(8, 0)),
    "ogle":   (time(12, 0), time(13, 0)),
    "ikindi": (time(15, 0), time(16, 0)),
    "aksam":  (time(18, 0), time(19, 0)),
    "gece":   (time(22, 0), time(23, 0)),
}


class PatientWindow(tk.Toplevel):
    """Modern hasta paneli – dashboard ve navigation sistemi."""

    # ------------------------------------------------------------------ #
    #   KURULUM
    # ------------------------------------------------------------------ #
    def __init__(self, master, patient_id: int, skip_password_change: bool = False):
        super().__init__(master)
        self.patient_id = patient_id
        self.master_window = master
        self.title("💊 Hasta Paneli")
        self.geometry("1400x900")
        self.configure(bg="#2b3e50")

        # Ekranın ortasına yerleştir
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Hastaya ait temel verileri getir
        self._load_patient_info(skip_password_change)

        # Dashboard oluştur
        self._create_dashboard()

    # ------------------------------------------------------------------ #
    #   HASTA ADI & İLK ŞİFRE KONTROLÜ
    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    #   DASHBOARD BİRLEŞTİRME
    # ------------------------------------------------------------------ #
    def _create_dashboard(self):
        for w in self.winfo_children():
            w.destroy()

        main = ttk.Frame(self, padding=20)
        main.pack(fill="both", expand=True)

        self._create_header(main)
        self._create_dashboard_grid(main)
        self._create_footer(main)

        self._refresh_dashboard()

    # ============================== HEADER ============================= #
    def _create_header(self, parent):
        hdr = ttk.Frame(parent)
        hdr.pack(fill="x", pady=(0, 25))

        # --- Profil resmi
        wrapper = ttk.Frame(hdr, width=100, height=100)
        wrapper.pack(side="left", padx=(0, 20))
        wrapper.pack_propagate(False)
        self.profile_lbl = ttk.Label(wrapper)
        self.profile_lbl.pack(fill="both", expand=True)
        self._load_profile_image()

        # --- Başlık
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

    # =============================  GRID  ============================== #
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

    # ===================== GLUKOZ ÖLÇÜM KARTI ========================= #
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

        # Değer
        ttk.Label(inp, text="💉 Değer (mg/dL):", font=("Segoe UI", 11, "bold")).pack(
            side="left"
        )
        self.val_ent = ttk.Entry(inp, font=("Segoe UI", 12), width=8)
        self.val_ent.pack(side="left", padx=(5, 15))

        # Tarih
        ttk.Label(inp, text="📅 Tarih (GG.AA.YYYY):", font=("Segoe UI", 11)).pack(
            side="left"
        )
        self.date_ent = ttk.Entry(inp, width=12, font=("Segoe UI", 11))
        self.date_ent.insert(0, date.today().strftime("%d.%m.%Y"))
        self.date_ent.pack(side="left", padx=(5, 15))

        # Saat
        ttk.Label(inp, text="⏰ Saat (HH:MM:SS):", font=("Segoe UI", 11)).pack(
            side="left"
        )
        self.time_ent = ttk.Entry(inp, width=9, font=("Segoe UI", 11))
        self.time_ent.insert(0, datetime.now().strftime("%H:%M:%S"))
        self.time_ent.pack(side="left", padx=(5, 15))

        # Vakit seçimi
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
            ("Ayrı", "extra"),  # <-- YENİ
        ]:
            ttk.Radiobutton(
                slot_fr,
                text=txt,
                variable=self.slot_var,
                value=val,
                bootstyle="info",
            ).pack(side="left", padx=2)

        # Kaydet düğmesi
        ttk.Button(
            card, text="💾 Kaydet", bootstyle="success", width=18, command=self._save_glucose
        ).pack(anchor="w", pady=(5, 15))

        # Özet & geçmiş
        self.glucose_summary_frame = ttk.Frame(card)
        self.glucose_summary_frame.pack(fill="x", pady=(0, 10))
        self._build_today_history(card)

    # ---------- Bugünkü ölçümler tablosu
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

    # ===================== GÜNLÜK ÖZET KARTI ========================== #
    def _create_summary_card(self, parent):
        card = ttk.LabelFrame(
            parent, text="📋 Günlük Özet", padding=20, bootstyle="success"
        )
        card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))
        self.summary_content_frame = ttk.Frame(card)
        self.summary_content_frame.pack(fill="both", expand=True)

    # ================ DİYET & EGZERSİZ KARTI ========================= #
    #  (fonksiyon gövdesi orijinal hâliyle bırakıldı)
    def _create_lifestyle_card(self, parent):
        # ... (içerik orijinal kodunuzla aynı – kısaltıldı)
        lifestyle_card = ttk.LabelFrame(
            parent, text="🍎 Diyet ve Egzersiz", padding=20, bootstyle="warning"
        )
        lifestyle_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 0))

        # --- Diyet
        diet_sec = ttk.LabelFrame(
            lifestyle_card, text="🥗 Diyet Planı", padding=15, bootstyle="info"
        )
        diet_sec.pack(fill="x", pady=(0, 15))
        ttk.Label(diet_sec, text="📋 Diyet Türü:", font=("Segoe UI", 11, "bold")).pack(
            anchor="w", pady=(0, 5)
        )
        row = ttk.Frame(diet_sec)
        row.pack(fill="x", pady=(0, 10))
        self.diet_cmb = ttk.Combobox(
            row,
            state="readonly",
            font=("Segoe UI", 11),
            values=("🚫 Şekersiz", "⚖️ Dengeli", "🥦 Düşük Şeker"),
        )
        self.diet_cmb.current(0)
        self.diet_cmb.pack(side="left", padx=(0, 10))
        self.diet_chk = tk.BooleanVar()
        ttk.Checkbutton(
            row, text="✅ Uygulandı", variable=self.diet_chk, bootstyle="round-toggle"
        ).pack(side="left")

        # --- Egzersiz
        ex_sec = ttk.LabelFrame(
            lifestyle_card, text="🏃 Egzersiz Planı", padding=15, bootstyle="secondary"
        )
        ex_sec.pack(fill="x", pady=(0, 15))
        ttk.Label(
            ex_sec, text="🎯 Egzersiz Türü:", font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))
        row2 = ttk.Frame(ex_sec)
        row2.pack(fill="x", pady=(0, 10))
        self.ex_cmb = ttk.Combobox(
            row2,
            state="readonly",
            font=("Segoe UI", 11),
            values=("🚶 Yürüyüş", "🚴 Bisiklet", "🏥 Klinik Egzersiz"),
        )
        self.ex_cmb.current(0)
        self.ex_cmb.pack(side="left", padx=(0, 10))
        self.ex_chk = tk.BooleanVar()
        ttk.Checkbutton(
            row2, text="✅ Yapıldı", variable=self.ex_chk, bootstyle="round-toggle"
        ).pack(side="left")

        ttk.Button(
            lifestyle_card,
            text="💾 Durum Kaydet",
            command=self._save_status,
            bootstyle="success",
            width=20,
        ).pack(pady=(10, 0))

    # ==================== HIZLI İŞLEMLER KARTI ======================== #
    def _create_actions_card(self, parent):
        # (orijinal buton listesi korunarak)
        card = ttk.LabelFrame(
            parent, text="⚡ Hızlı İşlemler", padding=20, bootstyle="primary"
        )
        card.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        btns = [
            ("📊 Glukoz Geçmişi", "info", self._show_history, 0, 0),
            ("📈 Analiz Raporu", "success", self._show_analysis, 0, 1),
            ("🔒 Şifre Değiştir", "warning", self._change_password, 1, 0),
            ("🔄 Verileri Yenile", "secondary", self._refresh_dashboard, 1, 1),
        ]
        for text, stl, cmd, r, c in btns:
            ttk.Button(
                card, text=text, bootstyle=f"{stl}-outline", command=cmd, width=18
            ).grid(row=r, column=c, padx=5, pady=5, sticky="ew")

        stat = ttk.Frame(card)
        stat.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        ttk.Label(
            stat, text="💡 İpucu ve Öneriler", font=("Segoe UI", 12, "bold"),
            bootstyle="primary",
        ).pack(anchor="w", pady=(0, 10))
        self.tips_label = ttk.Label(
            stat,
            text="• Günde en az 3 kez ölçüm yapın\n"
                 "• Diyet planınıza sadık kalın\n"
                 "• Düzenli egzersiz yapmayı unutmayın",
            font=("Segoe UI", 10),
            bootstyle="secondary",
            justify="left",
        )
        self.tips_label.pack(anchor="w")

    # =============================== FOOTER =========================== #
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

    # ==================== PROFİL RESMİ YÜKLEME ======================== #
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

    # ====================== ÖLÇÜM KAYDETME ============================ #
    def _save_glucose(self):
        try:
            # Değer
            value = float(self.val_ent.get().strip().replace(",", "."))
            if value <= 0:
                raise ValueError("Pozitif değer giriniz.")

            # Tarih + saat
            dt_txt = f"{self.date_ent.get().strip()} {self.time_ent.get().strip()}"
            dt = datetime.strptime(dt_txt, "%d.%m.%Y %H:%M:%S")

            # Vakit seçimi & doğrulama
            slot = self.slot_var.get()
            if slot in SLOT_RANGES:  # sabah–gece için aralık denetimi
                lo, hi = SLOT_RANGES[slot]
                if not (lo <= dt.time() <= hi):
                    ttk.dialogs.Messagebox.show_error(
                        f"Seçilen vakit ({slot.capitalize()}) ile girilen saat uyuşmuyor!",
                        "Zaman Uyumsuzluğu",
                        parent=self,
                    )
                    return
            # slot == "extra": her saati kabul et — ortalama dışında kalacak

            # Kayıt
            add_glucose(self.patient_id, value, dt)
            self.val_ent.delete(0, tk.END)
            self._refresh_dashboard()

            ttk.dialogs.Messagebox.show_info(
                f"✅ Ölçüm Kaydedildi!\n\n📊 {value:.1f} mg/dL\n⏰ {dt.strftime('%d.%m.%Y %H:%M:%S')}",
                "Başarılı",
                parent=self,
            )

        except Exception as err:
            ttk.dialogs.Messagebox.show_error(f"Hata:\n{err}", "Kayıt Hatası", parent=self)

    # ================== DİYET & EGZERSİZ KAYDETME ===================== #
    def _save_status(self):
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
        ex_type = ex_map.get(self.ex_cmb.get(), "walk")
        upsert_status(
            self.patient_id, diet_type, self.diet_chk.get(), ex_type, self.ex_chk.get()
        )
        ttk.dialogs.Messagebox.show_info(
            "Durum kaydedildi.", "Başarılı", parent=self
        )

    # ==================== DASHBOARD YENİLEME ========================== #
    def _refresh_dashboard(self):
        readings = list_today(self.patient_id)

        # Geçmiş tablosunu temizle
        for itm in self.history_tree.get_children():
            self.history_tree.delete(itm)

        # Özet alanını temizle
        for w in self.summary_content_frame.winfo_children():
            w.destroy()

        # ----------------- VERİ YOK
        if not readings:
            ttk.Label(
                self.summary_content_frame,
                text="📝 Henüz ölçüm yok",
                font=("Segoe UI", 14, "bold"),
                bootstyle="warning",
            ).pack(pady=(20, 10))
            ttk.Label(
                self.summary_content_frame,
                text="İlk ölçümünüzü yapmak için\nsol taraftaki formu kullanın.",
                font=("Segoe UI", 11),
                bootstyle="secondary",
                justify="center",
            ).pack()
            evaluate_day(self.patient_id, date.today())
            return

        # ----------------- İSTATİSTİK
        avg = sum(r["value_mg_dl"] for r in readings) / len(readings)
        min_v = min(r["value_mg_dl"] for r in readings)
        max_v = max(r["value_mg_dl"] for r in readings)

        sum_fr = ttk.Frame(self.glucose_summary_frame)
        sum_fr.pack(fill="x", pady=(0, 10))
        ttk.Label(
            sum_fr,
            text=f"📊 Günlük Özet: {len(readings)} ölçüm",
            font=("Segoe UI", 12, "bold"),
            bootstyle="info",
        ).pack(anchor="w", pady=(0, 5))
        ttk.Label(
            sum_fr,
            text=f"📈 Ortalama: {avg:.1f} mg/dL",
            font=("Segoe UI", 11),
            bootstyle="primary",
        ).pack(anchor="w")

        # Detaylı özet
        self._update_summary_card(readings, avg, min_v, max_v)

        # ----------------- TABLO DOLDUR
        for r in readings:
            t_str = r["reading_dt"].strftime("%H:%M")
            val = r["value_mg_dl"]
            if val < 70:
                stat, tag = "🔴 Düşük", "danger"
            elif val > 180:
                stat, tag = "🔴 Yüksek", "danger"
            else:
                stat, tag = "🟢 Normal", "success"
            self.history_tree.insert("", "end", values=(t_str, f"{val:.1f}", stat), tags=(tag,))
        self.history_tree.tag_configure("danger", background="#f8d7da")
        self.history_tree.tag_configure("success", background="#d4edda")

        # Doz ve alert hesapla
        evaluate_day(self.patient_id, date.today())

    # -------------------- Özet kartı güncelle
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

        # Durum mesajı
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

    # ==================== YAN PENCERELER ============================== #
    def _show_history(self):
        from gui.glucose_history import GlucoseHistoryWindow
        GlucoseHistoryWindow(self, self.patient_id, self.patient_name)

    def _show_analysis(self):
        from gui.analysis import AnalysisWindow
        AnalysisWindow(self, self.patient_id, self.patient_name)

    def _change_password(self):
        from gui.change_password import ChangePasswordDialog
        ChangePasswordDialog(self, self.patient_id)
