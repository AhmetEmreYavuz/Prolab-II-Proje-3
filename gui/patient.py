# gui/patient.py
import tkinter as tk
import ttkbootstrap as ttk
from datetime import date
from services.glucose import add_glucose, list_today
from services.daily import upsert_status
from services.rules import evaluate_day
from services.patient import get_profile_image
from utils.db import db_cursor
from PIL import Image, ImageTk
import io


class PatientWindow(tk.Toplevel):
    """Modern hasta paneli - dashboard ve navigation sistemi."""

    def __init__(self, master, patient_id: int, skip_password_change: bool = False):
        super().__init__(master)
        self.patient_id = patient_id
        self.master_window = master
        self.title("💊 Hasta Paneli")
        self.geometry("1400x900")
        self.configure(bg="#2b3e50")
        
        # Pencere merkezde açılsın
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Hasta bilgilerini getir
        self._load_patient_info(skip_password_change)
        
        # Navigation state
        self.current_view = "dashboard"
        
        self._create_dashboard()

    def _load_patient_info(self, skip_password_change):
        """Hasta bilgilerini yükle."""
        try:
            with db_cursor() as cur:
                cur.execute("SELECT full_name FROM users WHERE id=%s", (self.patient_id,))
                user_data = cur.fetchone()
                self.patient_name = user_data["full_name"] if user_data else "Hasta"
                
                # Şifre değişikliği kontrolü
                if not skip_password_change:
                    try:
                        cur.execute("SELECT password_change_needed FROM users WHERE id=%s", (self.patient_id,))
                        result = cur.fetchone()
                        password_change_needed = result.get("password_change_needed", 0) if result else 0
                        
                        if password_change_needed:
                            from gui.change_password import ChangePasswordDialog
                            self.after(100, lambda: ChangePasswordDialog(self, self.patient_id, is_first_login=True))
                            
                            with db_cursor() as update_cur:
                                update_cur.execute(
                                    "UPDATE users SET password_change_needed = 0 WHERE id=%s",
                                    (self.patient_id,)
                                )
                    except Exception as e:
                        print(f"Şifre değişikliği kontrolü yapılamadı: {str(e)}")
        except Exception as e:
            print(f"Hasta bilgileri yüklenirken hata: {str(e)}")
            self.patient_name = "Hasta"

    def _create_dashboard(self):
        """Modern dashboard görünümü."""
        # Tüm widget'ları temizle
        for widget in self.winfo_children():
            widget.destroy()
        
        self.current_view = "dashboard"
        
        # Ana container
        main_container = ttk.Frame(self, padding=20)
        main_container.pack(fill="both", expand=True)
        
        # Header
        self._create_header(main_container)
        
        # Dashboard grid
        self._create_dashboard_grid(main_container)
        
        # Footer
        self._create_footer(main_container)
        
        # Verileri yükle
        self._refresh_dashboard()

    def _create_header(self, parent):
        """Modern header tasarımı."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 25))
        
        # Profile section
        profile_section = ttk.Frame(header_frame)
        profile_section.pack(fill="x")
        
        # Profile image container
        self.profile_frame = ttk.Frame(profile_section, width=100, height=100)
        self.profile_frame.pack(side="left", padx=(0, 20))
        self.profile_frame.pack_propagate(False)
        
        self.profile_image_lbl = ttk.Label(self.profile_frame)
        self.profile_image_lbl.pack(fill="both", expand=True)
        self._load_profile_image()
        
        # Title and welcome section
        title_section = ttk.Frame(profile_section)
        title_section.pack(side="left", fill="x", expand=True)
        
        # Main title
        title_label = ttk.Label(
            title_section,
            text=f"🏥 Hasta Dashboard - {self.patient_name}",
            font=("Segoe UI", 22, "bold"),
            bootstyle="primary"
        )
        title_label.pack(anchor="w")
        
        # Subtitle with current date
        from datetime import datetime
        current_date = datetime.now().strftime("%d %B %Y")
        subtitle_label = ttk.Label(
            title_section,
            text=f"📅 Bugün: {current_date} | Sağlık takip ve yönetim sistemi",
            font=("Segoe UI", 12),
            bootstyle="secondary"
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

    def _create_dashboard_grid(self, parent):
        """Dashboard kartları grid sistemi."""
        dashboard_frame = ttk.Frame(parent)
        dashboard_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Configure responsive grid
        dashboard_frame.columnconfigure(0, weight=1)
        dashboard_frame.columnconfigure(1, weight=1)
        dashboard_frame.rowconfigure(0, weight=1)
        dashboard_frame.rowconfigure(1, weight=1)
        
        # Sol üst - Glukoz Ölçüm Kartı
        self._create_glucose_card(dashboard_frame)
        
        # Sağ üst - Günlük Özet Kartı
        self._create_summary_card(dashboard_frame)
        
        # Sol alt - Diyet ve Egzersiz Kartı
        self._create_lifestyle_card(dashboard_frame)
        
        # Sağ alt - Hızlı İşlemler Kartı
        self._create_actions_card(dashboard_frame)

    def _create_glucose_card(self, parent):
        """Glukoz ölçüm kartı."""
        glucose_card = ttk.LabelFrame(
            parent,
            text="📊 Kan Şekeri Takibi",
            padding=20,
            bootstyle="info"
        )
        glucose_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        
        # Yeni ölçüm bölümü
        new_measurement_frame = ttk.Frame(glucose_card)
        new_measurement_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(
            new_measurement_frame,
            text="🩸 Yeni Ölçüm Ekle",
            font=("Segoe UI", 14, "bold"),
            bootstyle="primary"
        ).pack(anchor="w", pady=(0, 10))
        
        input_frame = ttk.Frame(new_measurement_frame)
        input_frame.pack(fill="x")
        
        ttk.Label(
            input_frame,
            text="💉 Değer (mg/dL):",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        entry_frame = ttk.Frame(input_frame)
        entry_frame.pack(fill="x", pady=(0, 10))
        
        self.val_ent = ttk.Entry(
            entry_frame,
            font=("Segoe UI", 12),
            width=15
        )
        self.val_ent.pack(side="left", padx=(0, 10))
        
        ttk.Button(
            entry_frame,
            text="💾 Kaydet",
            command=self._save_glucose,
            bootstyle="success",
            width=12
        ).pack(side="left")
        
        # Günlük özet
        self.glucose_summary_frame = ttk.Frame(glucose_card)
        self.glucose_summary_frame.pack(fill="x", pady=(0, 15))
        
        # Ölçüm geçmişi
        history_frame = ttk.Frame(glucose_card)
        history_frame.pack(fill="both", expand=True)
        
        ttk.Label(
            history_frame,
            text="📈 Bugünkü Ölçümler",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Treeview
        columns = ("time", "value", "status")
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",
            height=8,
            bootstyle="info"
        )
        
        self.history_tree.heading("time", text="⏰ Saat")
        self.history_tree.heading("value", text="📊 Değer")
        self.history_tree.heading("status", text="🎯 Durum")
        
        self.history_tree.column("time", width=80, anchor="center")
        self.history_tree.column("value", width=100, anchor="center")
        self.history_tree.column("status", width=120, anchor="center")
        
        scrollbar = ttk.Scrollbar(
            history_frame,
            orient="vertical",
            command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_summary_card(self, parent):
        """Günlük özet kartı."""
        summary_card = ttk.LabelFrame(
            parent,
            text="📋 Günlük Özet",
            padding=20,
            bootstyle="success"
        )
        summary_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 10))
        
        # Özet bilgileri
        self.summary_content_frame = ttk.Frame(summary_card)
        self.summary_content_frame.pack(fill="both", expand=True)
        
        # Placeholder content - will be filled by _refresh_dashboard
        ttk.Label(
            self.summary_content_frame,
            text="📊 Veriler yükleniyor...",
            font=("Segoe UI", 12),
            bootstyle="secondary"
        ).pack(pady=20)

    def _create_lifestyle_card(self, parent):
        """Diyet ve egzersiz kartı."""
        lifestyle_card = ttk.LabelFrame(
            parent,
            text="🍎 Diyet ve Egzersiz",
            padding=20,
            bootstyle="warning"
        )
        lifestyle_card.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(10, 0))
        
        # Diyet bölümü
        diet_section = ttk.LabelFrame(
            lifestyle_card,
            text="🥗 Diyet Planı",
            padding=15,
            bootstyle="info"
        )
        diet_section.pack(fill="x", pady=(0, 15))
        
        diet_controls = ttk.Frame(diet_section)
        diet_controls.pack(fill="x")
        
        ttk.Label(
            diet_controls,
            text="📋 Diyet Türü:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        diet_select_frame = ttk.Frame(diet_controls)
        diet_select_frame.pack(fill="x", pady=(0, 10))
        
        self.diet_cmb = ttk.Combobox(
            diet_select_frame,
            width=20,
            state="readonly",
            font=("Segoe UI", 11),
            values=("🚫 Şekersiz", "⚖️ Dengeli", "🥦 Düşük Şeker")
        )
        self.diet_cmb.current(0)
        self.diet_cmb.pack(side="left", padx=(0, 10))
        
        self.diet_chk = tk.BooleanVar()
        ttk.Checkbutton(
            diet_select_frame,
            text="✅ Uygulandı",
            variable=self.diet_chk,
            bootstyle="round-toggle"
        ).pack(side="left")
        
        # Egzersiz bölümü
        exercise_section = ttk.LabelFrame(
            lifestyle_card,
            text="🏃 Egzersiz Planı",
            padding=15,
            bootstyle="secondary"
        )
        exercise_section.pack(fill="x", pady=(0, 15))
        
        exercise_controls = ttk.Frame(exercise_section)
        exercise_controls.pack(fill="x")
        
        ttk.Label(
            exercise_controls,
            text="🎯 Egzersiz Türü:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        exercise_select_frame = ttk.Frame(exercise_controls)
        exercise_select_frame.pack(fill="x", pady=(0, 10))
        
        self.ex_cmb = ttk.Combobox(
            exercise_select_frame,
            width=20,
            state="readonly",
            font=("Segoe UI", 11),
            values=("🚶 Yürüyüş", "🚴 Bisiklet", "🏥 Klinik Egzersiz")
        )
        self.ex_cmb.current(0)
        self.ex_cmb.pack(side="left", padx=(0, 10))
        
        self.ex_chk = tk.BooleanVar()
        ttk.Checkbutton(
            exercise_select_frame,
            text="✅ Yapıldı",
            variable=self.ex_chk,
            bootstyle="round-toggle"
        ).pack(side="left")
        
        # Kaydet butonu
        ttk.Button(
            lifestyle_card,
            text="💾 Durum Kaydet",
            command=self._save_status,
            bootstyle="success",
            width=20
        ).pack(pady=(10, 0))

    def _create_actions_card(self, parent):
        """Hızlı işlemler kartı."""
        actions_card = ttk.LabelFrame(
            parent,
            text="⚡ Hızlı İşlemler",
            padding=20,
            bootstyle="primary"
        )
        actions_card.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))
        
        # Grid layout for buttons
        actions_card.columnconfigure(0, weight=1)
        actions_card.columnconfigure(1, weight=1)
        
        # Buttons
        buttons_data = [
            ("📊 Glukoz Geçmişi", "info", self._show_history, 0, 0),
            ("📈 Analiz Raporu", "success", self._show_analysis, 0, 1),
            ("🔒 Şifre Değiştir", "warning", self._change_password, 1, 0),
            ("🔄 Verileri Yenile", "secondary", self._refresh_dashboard, 1, 1),
        ]
        
        for text, style, command, row, col in buttons_data:
            ttk.Button(
                actions_card,
                text=text,
                bootstyle=f"{style}-outline",
                command=command,
                width=18
            ).grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Status section
        status_frame = ttk.Frame(actions_card)
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        
        ttk.Label(
            status_frame,
            text="💡 İpuci ve Öneriler",
            font=("Segoe UI", 12, "bold"),
            bootstyle="primary"
        ).pack(anchor="w", pady=(0, 10))
        
        self.tips_label = ttk.Label(
            status_frame,
            text="• Günde en az 3 kez ölçüm yapın\n• Diyet planınıza sadık kalın\n• Düzenli egzersiz yapmayı unutmayın",
            font=("Segoe UI", 10),
            bootstyle="secondary",
            justify="left"
        )
        self.tips_label.pack(anchor="w")

    def _create_footer(self, parent):
        """Footer bölümü."""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill="x")
        
        ttk.Label(
            footer_frame,
            text="© 2025 Diyabet Takip Sistemi - Hasta Paneli",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(side="left")
        
        ttk.Button(
            footer_frame,
            text="❌ Çıkış",
            bootstyle="danger-outline",
            width=15,
            command=self.destroy
        ).pack(side="right")

    def _load_profile_image(self):
        """Profil resmini yükler."""
        image_data = get_profile_image(self.patient_id)
        
        try:
            if image_data:
                img = Image.open(io.BytesIO(image_data))
                img.thumbnail((90, 90))
                
                photo = ImageTk.PhotoImage(img)
                self.profile_image_lbl.config(image=photo)
                self.profile_image_lbl.image = photo
            else:
                self.profile_image_lbl.config(
                    text="👤",
                    font=("Segoe UI", 40),
                    foreground="white"
                )
        except Exception as e:
            print(f"Profil resmi yüklenirken hata: {str(e)}")
            self.profile_image_lbl.config(
                text="👤",
                font=("Segoe UI", 40),
                foreground="white"
            )

    def _save_glucose(self):
        """Yeni ölçümü kaydeder."""
        try:
            value = float(self.val_ent.get().strip().replace(',', '.'))
            if value <= 0:
                raise ValueError("Pozitif değer giriniz.")
            
            add_glucose(self.patient_id, value)
            self.val_ent.delete(0, tk.END)
            self._refresh_dashboard()
            
            # Success message
            ttk.dialogs.Messagebox.show_info(
                f"✅ Ölçüm Kaydedildi!\n\n📊 Değer: {value:.1f} mg/dL\n⏰ Saat: {date.today().strftime('%H:%M')}",
                "🎉 Başarılı",
                parent=self
            )
            
        except ValueError as e:
            ttk.dialogs.Messagebox.show_error(
                f"❌ Geçersiz Değer\n\n{str(e)}",
                "⚠️ Hata",
                parent=self
            )

    def _save_status(self):
        """Diyet ve egzersiz durumunu kaydeder."""
        diet_type_map = {"🚫 Şekersiz": "sugar_free", "⚖️ Dengeli": "balanced", "🥦 Düşük Şeker": "low_sugar"}
        exercise_type_map = {"🚶 Yürüyüş": "walk", "🚴 Bisiklet": "bike", "🏥 Klinik Egzersiz": "clinic"}
        
        diet_type = diet_type_map.get(self.diet_cmb.get(), "balanced")
        diet_done = self.diet_chk.get()
        
        ex_type = exercise_type_map.get(self.ex_cmb.get(), "walk")
        ex_done = self.ex_chk.get()
        
        upsert_status(self.patient_id, diet_type, diet_done, ex_type, ex_done)
        
        ttk.dialogs.Messagebox.show_info(
            f"✅ Durum Kaydedildi!\n\n🥗 Diyet: {self.diet_cmb.get()} {'✅' if diet_done else '❌'}\n🏃 Egzersiz: {self.ex_cmb.get()} {'✅' if ex_done else '❌'}",
            "🎉 Başarılı",
            parent=self
        )

    def _refresh_dashboard(self):
        """Dashboard verilerini yeniler."""
        readings = list_today(self.patient_id)
        
        # Glukoz geçmişi tablosunu güncelle
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Özet bilgilerini temizle
        for widget in self.summary_content_frame.winfo_children():
            widget.destroy()
        
        if readings:
            # Glukoz özeti
            avg = sum(r["value_mg_dl"] for r in readings) / len(readings)
            min_val = min(r["value_mg_dl"] for r in readings)
            max_val = max(r["value_mg_dl"] for r in readings)
            
            # Glukoz summary
            summary_frame = ttk.Frame(self.glucose_summary_frame)
            summary_frame.pack(fill="x", pady=(0, 10))
            
            ttk.Label(
                summary_frame,
                text=f"📊 Günlük Özet: {len(readings)} ölçüm",
                font=("Segoe UI", 12, "bold"),
                bootstyle="info"
            ).pack(anchor="w", pady=(0, 5))
            
            ttk.Label(
                summary_frame,
                text=f"📈 Ortalama: {avg:.1f} mg/dL",
                font=("Segoe UI", 11),
                bootstyle="primary"
            ).pack(anchor="w")
            
            # Özet kartı güncelle
            self._update_summary_card(readings, avg, min_val, max_val)
            
            # Tabloyu doldur
            for r in readings:
                time_str = r["reading_dt"].strftime("%H:%M")
                value = r["value_mg_dl"]
                
                if value < 70:
                    status = "🔴 Düşük"
                    status_style = "danger"
                elif value > 180:
                    status = "🔴 Yüksek"
                    status_style = "danger"
                else:
                    status = "🟢 Normal"
                    status_style = "success"
                
                self.history_tree.insert(
                    "",
                    tk.END,
                    values=(time_str, f"{value:.1f}", status),
                    tags=(status_style,)
                )
            
            self.history_tree.tag_configure("danger", background="#f8d7da")
            self.history_tree.tag_configure("success", background="#d4edda")
        else:
            # Veri yoksa
            ttk.Label(
                self.summary_content_frame,
                text="📝 Henüz ölçüm yok",
                font=("Segoe UI", 14, "bold"),
                bootstyle="warning"
            ).pack(pady=(20, 10))
            
            ttk.Label(
                self.summary_content_frame,
                text="İlk ölçümünüzü yapmak için\nsol taraftaki formu kullanın.",
                font=("Segoe UI", 11),
                bootstyle="secondary",
                justify="center"
            ).pack()

        # Doz ve uyarı hesapla
        evaluate_day(self.patient_id, date.today())

    def _update_summary_card(self, readings, avg, min_val, max_val):
        """Özet kartını güncelle."""
        # Stats
        stats_frame = ttk.Frame(self.summary_content_frame)
        stats_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            stats_frame,
            text="📊 İstatistikler",
            font=("Segoe UI", 14, "bold"),
            bootstyle="success"
        ).pack(anchor="w", pady=(0, 10))
        
        stats_data = [
            ("📈 Ortalama:", f"{avg:.1f} mg/dL"),
            ("⬇️ En Düşük:", f"{min_val:.1f} mg/dL"),
            ("⬆️ En Yüksek:", f"{max_val:.1f} mg/dL"),
            ("🔢 Toplam Ölçüm:", f"{len(readings)} adet")
        ]
        
        for label, value in stats_data:
            row_frame = ttk.Frame(stats_frame)
            row_frame.pack(fill="x", pady=2)
            
            ttk.Label(
                row_frame,
                text=label,
                font=("Segoe UI", 11, "bold")
            ).pack(side="left")
            
            ttk.Label(
                row_frame,
                text=value,
                font=("Segoe UI", 11),
                bootstyle="primary"
            ).pack(side="right")
        
        # Status
        status_frame = ttk.Frame(self.summary_content_frame)
        status_frame.pack(fill="x", pady=(15, 0))
        
        ttk.Label(
            status_frame,
            text="🎯 Durum",
            font=("Segoe UI", 14, "bold"),
            bootstyle="success"
        ).pack(anchor="w", pady=(0, 10))
        
        if avg < 70:
            status_text = "⚠️ Ortalama düşük!\nDoktorunuza danışın."
            status_style = "warning"
        elif avg > 180:
            status_text = "⚠️ Ortalama yüksek!\nDiyet planınızı kontrol edin."
            status_style = "danger"
        else:
            status_text = "✅ Ortalama normal!\nBöyle devam edin."
            status_style = "success"
        
        ttk.Label(
            status_frame,
            text=status_text,
            font=("Segoe UI", 11),
            bootstyle=status_style,
            justify="center"
        ).pack()

    def _show_history(self):
        """Glukoz geçmişini göster."""
        from gui.glucose_history import GlucoseHistoryWindow
        GlucoseHistoryWindow(self, self.patient_id, self.patient_name)

    def _show_analysis(self):
        """Analiz raporunu göster."""
        from gui.analysis import AnalysisWindow
        AnalysisWindow(self, self.patient_id, self.patient_name)

    def _change_password(self):
        """Şifre değiştirme penceresini aç."""
        from gui.change_password import ChangePasswordDialog
        ChangePasswordDialog(self, self.patient_id)
