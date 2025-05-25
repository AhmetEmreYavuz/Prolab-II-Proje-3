# gui/patient.py
import tkinter as tk
import ttkbootstrap as ttk
from datetime import date, datetime, time
from services.glucose import add_glucose, list_today, list_for_date

from services.symptom import list_symptoms  # 追加
from ttkbootstrap.scrolled import ScrolledFrame   # +++ EKLENDİ +++


import re     #  ← yeni



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
# Bu sıraya göre özet ve kümülatif ortalama hesaplanır
SLOT_ORDER = ["sabah", "ogle", "ikindi", "aksam", "gece"]



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
        """Hasta panelini kaydırılabilir hale getirir (sürümden bağımsız)."""

        # Önce eski widget'ları kaldır
        for w in self.winfo_children():
            w.destroy()

        # Kaydırılabilir çerçeve
        self.scroll_fr = ScrolledFrame(self, autohide=True)
        self.scroll_fr.pack(fill="both", expand=True)

        # < 1.10 sürümlerinde 'scrollable_frame' yok; kendisi iç çerçevedir.
        interior = getattr(self.scroll_fr, "scrollable_frame", self.scroll_fr)

        # Asıl içerik buraya
        main = ttk.Frame(interior, padding=20)
        main.pack(fill="both", expand=True)

        # Alt bileşenler
        self._create_header(main)
        self._create_dashboard_grid(main)
        self._create_footer(main)

        self._refresh_dashboard()
        self.scroll_fr.update_idletasks()

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

        # ---------- Üst giriş satırı
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

        # ---------- Buton satırı (Kaydet + Gün Sonu yan yana)
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

        # ---------- Özet & geçmiş bölümleri
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
        """
        Diyet, egzersiz ve öneri kutularını içeren kart.
        """
        lifestyle_card = ttk.LabelFrame(
            parent, text="🍎 Diyet ve Egzersiz",
            padding=20, bootstyle="warning"
        )
        lifestyle_card.grid(row=1, column=0, sticky="nsew",
                            padx=(0, 10), pady=(10, 0))

        # ────────────────── DİYET PLANı ────────────────── #
        diet_sec = ttk.LabelFrame(
            lifestyle_card, text="🥗 Diyet Planı",
            padding=15, bootstyle="info"
        )
        diet_sec.pack(fill="x", pady=(0, 15))

        ttk.Label(diet_sec, text="📋 Diyet Türü:",
                  font=("Segoe UI", 11, "bold")
                  ).pack(anchor="w", pady=(0, 5))

        row = ttk.Frame(diet_sec);
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

        # ────────────────── EGZERSİZ PLANı ────────────────── #
        ex_sec = ttk.LabelFrame(
            lifestyle_card, text="🏃 Egzersiz Planı",
            padding=15, bootstyle="secondary"
        )
        ex_sec.pack(fill="x", pady=(0, 15))

        ttk.Label(ex_sec, text="🎯 Egzersiz Türü:",
                  font=("Segoe UI", 11, "bold")
                  ).pack(anchor="w", pady=(0, 5))

        row2 = ttk.Frame(ex_sec);
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

        # Durum kaydet butonu
        ttk.Button(
            lifestyle_card, text="💾 Durum Kaydet",
            command=self._save_status, bootstyle="success", width=20
        ).pack(pady=(10, 0))

        # ─────────────── DİYET-EGZERSİZ ÖNERİSİ ─────────────── #
        suggest_fr = ttk.LabelFrame(
            lifestyle_card,
            text="📑 Diyet Planı ve Egzersiz Önerisi",
            padding=15, bootstyle="primary"
        )
        suggest_fr.pack(fill="x", pady=(15, 0))

        self.suggest_lbl = ttk.Label(
            suggest_fr, text="—",  # ilk başta boş
            font=("Segoe UI", 11),
            bootstyle="secondary",
            justify="left", wraplength=500
        )
        self.suggest_lbl.pack(anchor="w")

        # Öneriyi hesaplayan buton
        ttk.Button(
            suggest_fr,
            text="💡 Plan Önerisi",
            bootstyle="primary-outline",
            width=18,
            command=self._show_plan_suggestion  # ⇒ fonksiyonunuz
        ).pack(anchor="e", pady=(8, 0))


    # ==================== HIZLI İŞLEMLER KARTI ======================== #
    def _create_actions_card(self, parent):
        """
        Sağ üstteki “Hızlı İşlemler” kartını oluşturur.
        Yeni sırayla 2 × 3’lük grid:
            (0,0) Glukoz Geçmişi   | (0,1) Analiz Raporu
            (1,0) İnsülin Önerisi  | (1,1) Verileri Yenile
            (2,0) Şifre Değiştir   | — (boş)
        Altında ipucu-öneri metni.
        """
        card = ttk.LabelFrame(
            parent, text="⚡ Hızlı İşlemler", padding=20, bootstyle="primary"
        )
        card.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))

        # 2 sütunlu esnek grid
        for col in (0, 1):
            card.columnconfigure(col, weight=1)

        # --- İşlem butonları -------------------------------------------------
        actions = [
            ("📊 Glukoz Geçmişi", "info", self._show_history, 0, 0),
            ("📈 Analiz Raporu", "success", self._show_analysis, 0, 1),
            ("💉 İnsülin Önerisi", "warning", self._show_insulin_suggestion, 1, 0),
            ("🔄 Verileri Yenile", "secondary", self._refresh_dashboard, 1, 1),
            ("🔒 Şifre Değiştir", "danger", self._change_password, 2, 0),
        ]

        for text, style, cmd, r, c in actions:
            ttk.Button(
                card,
                text=text,
                bootstyle=f"{style}-outline",
                command=cmd,
                width=18,
            ).grid(row=r, column=c, padx=5, pady=5, sticky="ew")

        # --- İpucu - Öneriler alanı -----------------------------------------
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

        # ——----- BURASI YENİ ——-----
        self.symptom_lbl = ttk.Label(
            tips_frame,
            text="Hastadaki belirtiler: —",
            font=("Segoe UI", 10),
            bootstyle="secondary",
            justify="left"
        )
        self.symptom_lbl.pack(anchor="w", pady=(8, 0))

        # etiketi ilk kez doldur
        self._update_symptom_info()

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
        """
        Tarih alanındaki gün, daha önce _end_day ile kapatılmışsa ölçüm reddedilir;
        aksi hâlde normal akış devam eder.
        """
        try:
            # --- Tarih + saat  (önce alın ki kapalı-gün kontrolü yapılsın)
            dt_txt = f"{self.date_ent.get().strip()} {self.time_ent.get().strip()}"
            dt = datetime.strptime(dt_txt, "%d.%m.%Y %H:%M:%S")

            # --- Kapalı gün kontrolü
            if getattr(self, "closed_date", None) == dt.date():
                ttk.dialogs.Messagebox.show_warning(
                    "Bu gün için 'Gün Sonu' yapıldı; yeni ölçüm ekleyemezsiniz.",
                    "Gün Kapalı",
                    parent=self,
                )
                return

            # --- Glukoz değeri
            value = float(self.val_ent.get().strip().replace(",", "."))
            if value <= 0:
                raise ValueError("Pozitif değer giriniz.")

            # --- Vakit doğrulama
            slot = self.slot_var.get()  # sabah / öğle / … / extra
            if slot in SLOT_RANGES:
                lo, hi = SLOT_RANGES[slot]
                if not (lo <= dt.time() <= hi):
                    ttk.dialogs.Messagebox.show_error(
                        f"Seçilen vakit ({slot.capitalize()}) ile saat uyuşmuyor!",
                        "Zaman Uyumsuzluğu",
                        parent=self,
                    )
                    return
            else:  # extra
                ttk.dialogs.Messagebox.show_warning(
                    "Bu ölçüm izinli saat aralığının dışında.\n"
                    "Kaydedildi ama ortalamaya dahil edilmeyecek.",
                    "Uyarı",
                    parent=self,
                )

            # --- Veritabanına yaz
            add_glucose(self.patient_id, value, dt)
            self.val_ent.delete(0, tk.END)
            self._refresh_dashboard()

        except Exception as err:
            ttk.dialogs.Messagebox.show_error(
                f"Hata:\n{err}", "Kayıt Hatası", parent=self
            )

    # ================== DİYET & EGZERSİZ KAYDETME ===================== #
    def _save_status(self):
        try:
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
            diet_done = self.diet_chk.get()
            ex_done = self.ex_chk.get()
            
            # Veritabanına kaydet
            upsert_status(
                self.patient_id, diet_type, diet_done, ex_type, ex_done
            )
            
            # Başarı mesajı ve detaylı bilgi
            success_msg = (
                f"✅ Bugünün durumu kaydedildi!\n\n"
                f"🥗 Diyet: {self.diet_cmb.get()} ({'✅ Uygulandı' if diet_done else '❌ Uygulanmadı'})\n"
                f"🏃 Egzersiz: {self.ex_cmb.get()} ({'✅ Yapıldı' if ex_done else '❌ Yapılmadı'})\n\n"
                f"💡 Bu veriler doktor panelinde gerçek zamanlı olarak görülecektir."
            )
            
            ttk.dialogs.Messagebox.show_info(
                success_msg, "📊 Durum Kaydedildi", parent=self
            )
            
            print(f"DEBUG: Hasta {self.patient_id} için diyet/egzersiz durumu kaydedildi:")
            print(f"  - Diyet: {diet_type} (done: {diet_done})")
            print(f"  - Egzersiz: {ex_type} (done: {ex_done})")
            
        except Exception as err:
            ttk.dialogs.Messagebox.show_error(
                f"Durum kaydedilemedi:\n{str(err)}", 
                "❌ Hata", 
                parent=self
            )

    # ==================== DASHBOARD YENİLEME ========================== #
    def _refresh_dashboard(self):
        """
        Pencerenin sol alt ve sağ üst bölümlerini (geçmiş tablosu + özet kartı)
        günceller.  Ayrıca slot–bazlı kümülatif ortalamaları hesaplar, eksik /
        yetersiz veri uyarılarını gösterir ve rules.evaluate_day'i tetikler.
        """
        readings = list_today(self.patient_id) or []

        # --- Önce ekrandaki eski kayıtları temizle --------------------
        for item_id in self.history_tree.get_children():
            self.history_tree.delete(item_id)
        for w in self.summary_content_frame.winfo_children():
            w.destroy()

        # ───────────────────────────────────────────────────────────────
        #   Ölçüm hiç yoksa erken çık
        # ───────────────────────────────────────────────────────────────
        if not readings:
            ttk.Label(
                self.summary_content_frame,
                text="📝 Henüz ölçüm yok",
                font=("Segoe UI", 14, "bold"),
                bootstyle="warning",
            ).pack(pady=(20, 10))
            evaluate_day(self.patient_id, date.today())
            return

        # --- Beş vakte göre kümülatif ortalamalar ---------------------
        slot_avgs, slot_vals = self._compute_slot_averages(readings)

        # Eksik vakit uyarısı
        missing = [s.capitalize() for s, v in slot_vals.items() if not v]
        if missing:
            ttk.dialogs.Messagebox.show_warning(
                "Ölçüm eksik! " + ", ".join(missing) +
                " vakit(ler)inde ölçüm yok – ortalamaya katılmadı.",
                "Eksik Ölçüm", parent=self
            )

        # Az sayıda ölçüm uyarısı
        if len(readings) <= 3:
            ttk.dialogs.Messagebox.show_warning(
                "Yetersiz veri! Ortalama hesaplaması güvenilir değildir.",
                "Uyarı", parent=self
            )

        # --- Özet kartı ------------------------------------------------
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

        # --- Geçmiş tablosunu doldur ----------------------------------
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

        # 8) Günlük ortalama & etiket/öneri güncellemeleri
        day_avg = sum(r["value_mg_dl"] for r in readings) / len(readings)
        self._latest_avg = day_avg

        self._update_symptom_info()
        self._update_lifestyle_suggestion(day_avg)

        # 9) Kural tabanlı uyarılar
        evaluate_day(self.patient_id, date.today())

        # ★ Scroll bölgesini yeni boyuta uydur
        if hasattr(self, "scroll_fr"):
            self.scroll_fr.update_idletasks()

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

    def _end_day(self):
        """
        'Gün Sonu' – şu an tarih giriş kutusunda ne yazıyorsa o günü kapat
        ve özet kartını o günde kalan ölçümlerle yeniden oluştur.
        """
        try:
            sel_day = datetime.strptime(self.date_ent.get().strip(), "%d.%m.%Y").date()
        except ValueError:
            ttk.dialogs.Messagebox.show_error("Geçersiz tarih!", "Hata", parent=self)
            return

        self.closed_date = sel_day
        self._refresh_dashboard()  # sağ paneli tazele

        ttk.dialogs.Messagebox.show_info(
            f"{sel_day.strftime('%d.%m.%Y')} için gün sonu tamamlandı.\n"
            "Bu tarih için yeni ölçüm girişi kapatıldı.",
            "Bilgi", parent=self
        )

    def _compute_slot_averages(self, readings):
        """
        SLOT_ORDER = [sabah, öğle, ikindi, akşam, gece]
        * sabah ort.:   sadece sabah ölçümleri
        * öğle  ort.:   sabah + öğle
        * ikindi ort.:  sabah + öğle + ikindi
        ... vb.

        Dönüş:
            (averages_dict, values_dict)
            averages_dict -> {slot: ortalama veya None}
            values_dict   -> {slot: [değerler]}
        """
        # Ölçüm değerlerini slot‐lara dağıt
        slot_values = {s: [] for s in SLOT_ORDER}
        for rec in readings:
            tm = rec["reading_dt"].time()
            for slot, (lo, hi) in SLOT_RANGES.items():
                if lo <= tm <= hi:
                    slot_values[slot].append(rec["value_mg_dl"])
                    break  # eşleşen ilk slot yeterli

        # Kümülatif ortalamaları hesapla
        averages, cumulative = {}, []
        for slot in SLOT_ORDER:
            cumulative.extend(slot_values[slot])
            averages[slot] = (sum(cumulative) / len(cumulative)) \
                             if cumulative else None
        return averages, slot_values

# ---------------------------------------------------------------
#   İNSÜLİN ÖNERİSİ
 # ---------------------------------------------------------------
    @staticmethod
    def _dose_for_avg(avg: float | None) -> str:
        """Tablodaki aralıklara göre dozu döndürür."""
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
        """
        Hem günün genel (gece) ortalamasını hem de SLOT_ORDER dizisindeki
        *her öğün* için kümülatif ortalamayı hesaplar ve tablodaki sınırlar
        doğrultusunda doz önerilerini listeler.

        ─ Kapanan bir gün varsa self.closed_date kullanılır,
          yoksa bugün (date.today()) baz alınır.
        ─ Ölçüm yoksa / eksikse uyarı verilir.
        """

        from services.glucose import list_for_date  # yardımcı sorgu

        target_day = getattr(self, "closed_date", date.today())
        rows = list_for_date(self.patient_id, target_day)

        if not rows:
            ttk.dialogs.Messagebox.show_warning(
                "Seçilen gün için kayıtlı ölçüm bulunamadı.",
                "Veri Yok", parent=self
            )
            return

        # ► Öğün bazlı ortalamalar (kümülatif kural)
        slot_avgs, _ = self._compute_slot_averages(rows)

        # ► Doz eşik tablosu ------------------------------------------------
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

        # ► Mesaj gövdesi  --------------------------------------------------
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
        """Veritabanından semptomları çekip etiketi günceller."""
        try:
            symptoms = list_symptoms(self.patient_id)
            if symptoms:
                txt = "Hastadaki belirtiler: " + ", ".join(symptoms)
            else:
                txt = "Hastadaki belirtiler: —"
            self.symptom_lbl.config(text=txt, bootstyle="warning" if symptoms else "secondary")
        except Exception as err:
            # sessiz hata; etiketi kırmızı yap
            self.symptom_lbl.config(text=f"Semptom okunamadı: {err}", bootstyle="danger")

# kartın en altına ekleyin
    # ------------------------------------------------------------
    #   DİYET – EGZERSİZ ÖNERİSİNİ HESAPLA ve EKRANA YAZ
    # ------------------------------------------------------------
    def _update_lifestyle_suggestion(self, day_avg: float | None):
        """
        Günlük ort. glukoz (day_avg) + hastanın belirtileri
        → tablo-tabanlı diyet & egzersiz önerisi üretir ve
        self.suggest_lbl etiketini günceller.
        """

        # 1) Hastanın son semptom listesi  (tamamı küçük-harf)
        from services.symptom import list_symptoms
        syms = {s.lower() for s in list_symptoms(self.patient_id)}

        # Ölçüm yoksa / ort. belirsizse
        if day_avg is None:
            self.suggest_lbl.config(
                text="Bugünün ölçümleri yetersiz — öneri üretilemedi.",
                bootstyle="secondary"
            )
            return

        # 2) Kural tablosu  (alt, üst, belirtiler, diyet, egzersiz)
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

        # 3) Metni oluştur
        txt = ("Hastadaki belirtiler yok." if not syms else
               f"Hastadaki belirtiler: {', '.join(sorted(syms))}")

        if diet:
            txt += (f"\n\n• Önerilen Diyet: {diet}"
                    f"\n• Önerilen Egzersiz: {ex}")
            style = "primary"
        else:
            txt += "\n\n• Henüz tabloya uyan bir öneri yok."
            style = "secondary"

        # 4) Ekrana yaz
        self.suggest_lbl.config(text=txt, bootstyle=style)


    # ==================== PLAN ÖNERİSİ ==================== #
    def _show_plan_suggestion(self):
        """
        Günlük ort. glukoz + hastanın kayıtlı belirtilerine göre
        tablo-temelli diyet / egzersiz önerisini hesaplar ve
        self.suggest_lbl etiketine yazar.
        """

        # ---- 1) Bugünün ortalama glukozu -------------------------------
        todays = list_today(self.patient_id)
        if not todays:
            ttk.dialogs.Messagebox.show_warning(
                "Önce bugünün ölçümlerini kaydedin / yenileyin.",
                "Veri Yok", parent=self
            )
            return
        avg = sum(r["value_mg_dl"] for r in todays) / len(todays)

        # ---- 2) Hastanın aktif belirtileri (tamamı küçük-harf) ----------
        with db_cursor() as cur:
            cur.execute(
                "SELECT description FROM symptoms "
                "WHERE patient_id=%s ORDER BY noted_at DESC",
                (self.patient_id,)
            )
            syms = {row["description"].lower() for row in cur.fetchall()}

        # ---- 3) Kural tablosu -------------------------------------------
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
            if lo <= avg < hi and syms & trig_syms:  # aralık + kesişim
                diet, ex = d, e
                break

        # ---- 4) Sonucu göster ------------------------------------------
        if diet is None:
            ttk.dialogs.Messagebox.show_info(
                "Veriler mevcut kurallarla eşleşmedi.", "Öneri Yok", parent=self
            )
            return

        self.suggest_lbl.configure(
            text=f"Diyet Planı Önerisi: {diet}\nEgzersiz Önerisi: {ex}"
        )



