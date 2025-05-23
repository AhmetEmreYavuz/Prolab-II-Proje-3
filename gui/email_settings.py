# gui/email_settings.py
import tkinter as tk
import ttkbootstrap as ttk
from utils.emailer import save_smtp_settings, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SENDER, USE_SMTP


class EmailSettingsDialog(tk.Toplevel):
    """E-posta gönderimi için SMTP ayarlarını yapılandırma ekranı."""

    def __init__(self, master):
        super().__init__(master)
        self.title("E-posta Ayarları")
        self.geometry("650x600")

        # Pencereyi modal yap (arkadaki pencereye tıklanamaz)
        self.transient(master)
        self.grab_set()
        self.focus_set()

        # Minimum boyut
        self.minsize(600, 500)

        # --------------------------------------------------------------
        # SABIT ALT PANEL (BUTONLAR) - HER ZAMAN GÖRÜNÜR OLACAK
        # --------------------------------------------------------------
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side="bottom", fill="x")

        # Ayırıcı çizgi
        ttk.Separator(bottom_frame, orient="horizontal").pack(fill="x")

        # Buton çerçevesi
        button_frame = ttk.Frame(bottom_frame, padding=10)
        button_frame.pack(fill="x")

        # KAYDET BUTONU - BÜYÜK VE NET
        save_button = ttk.Button(
            button_frame,
            text="KAYDET",
            bootstyle="success",
            command=self._save_settings,
            width=30
        )
        save_button.pack(side="left", padx=10, pady=10)

        # Test butonu
        test_button = ttk.Button(
            button_frame,
            text="Ayarları Test Et",
            bootstyle="info",
            command=self._test_settings,
            width=20
        )
        test_button.pack(side="left", padx=10, pady=10)

        # Çıkış butonu
        exit_button = ttk.Button(
            button_frame,
            text="Kapat",
            bootstyle="secondary",
            command=self.destroy,
            width=15
        )
        exit_button.pack(side="right", padx=10, pady=10)

        # Durum mesajı
        status_frame = ttk.Frame(bottom_frame, padding=5)
        status_frame.pack(fill="x")

        self.status_label = ttk.Label(
            status_frame,
            text="",
            font=("Segoe UI", 12, "bold"),
            anchor="center"
        )
        self.status_label.pack(fill="x", padx=10, pady=5)

        # --------------------------------------------------------------
        # ÜST İÇERİK PANEL - SCROLLABLE
        # --------------------------------------------------------------
        # Ana içerik alanı - kaydırma çubuğu ile
        main_canvas = tk.Canvas(self)
        main_canvas.pack(side="top", fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(main_canvas, orient="vertical", command=main_canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # Canvas'ı scrollbar'a bağla
        main_canvas.configure(yscrollcommand=scrollbar.set)

        # İçerik çerçevesi
        content_frame = ttk.Frame(main_canvas)
        content_window = main_canvas.create_window((0, 0), window=content_frame, anchor="nw", tags="content")

        # Canvas yeniden boyutlandırıldığında içeriği güncelle
        def _configure_content(event):
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            main_canvas.itemconfig(content_window, width=event.width)

        main_canvas.bind("<Configure>", _configure_content)
        content_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))

        # Başlık
        ttk.Label(
            content_frame,
            text="E-posta Ayarları",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=(20, 0), padx=20)

        # Açıklama
        ttk.Label(
            content_frame,
            text="Bu ayarlar yeni hasta kaydında otomatik şifre gönderimi için kullanılacaktır.",
            font=("Segoe UI", 11),
            wraplength=500
        ).pack(pady=10, padx=20)

        # Form çerçevesi
        form_frame = ttk.LabelFrame(content_frame, text="SMTP Sunucu Bilgileri", padding=15)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # SMTP aktifleştirme seçeneği
        self.use_smtp_var = tk.BooleanVar(value=USE_SMTP)
        ttk.Checkbutton(
            form_frame,
            text="E-posta gönderimini etkinleştir (SMTP kullan)",
            variable=self.use_smtp_var,
            bootstyle="round-toggle",
            style="success.Toolbutton"
        ).pack(anchor="w", pady=(5, 15))

        # Form alanları - Grid layout
        form_grid = ttk.Frame(form_frame)
        form_grid.pack(fill="x", padx=10)

        fields = [
            ("SMTP Sunucu:", "host", SMTP_HOST),
            ("Port:", "port", str(SMTP_PORT)),
            ("E-posta Kullanıcı Adı:", "user", SMTP_USER),
            ("E-posta Şifre:", "password", SMTP_PASS),
            ("Gönderen E-posta:", "sender", SENDER)
        ]

        self.entries = {}
        for i, (label_text, key, default) in enumerate(fields):
            ttk.Label(
                form_grid,
                text=label_text,
                font=("Segoe UI", 11)
            ).grid(row=i, column=0, sticky="w", padx=5, pady=12)

            # Password alanı için gizli giriş
            show_char = "*" if key == "password" else None

            entry = ttk.Entry(
                form_grid,
                font=("Segoe UI", 11),
                width=40,
                show=show_char
            )
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky="ew", padx=15, pady=12)

            self.entries[key] = entry

        # Sütun ayarları
        form_grid.grid_columnconfigure(1, weight=1)

        # Gmail bilgi kutusu
        info_frame = ttk.Frame(content_frame, padding=10)
        info_frame.pack(fill="x", padx=20, pady=(0, 20))

        info_text = (
            "💡 Gmail kullanıcıları için:\n"
            "  • SMTP Sunucu: smtp.gmail.com\n"
            "  • Port: 587\n"
            "  • Normal Gmail şifreniz değil, 'Uygulama Şifresi' oluşturmanız gerekir.\n"
            "  • Uygulama şifresi almak için: Google Hesap → Güvenlik → İki Adımlı Doğrulama → Uygulama Şifreleri"
        )

        ttk.Label(
            info_frame,
            text=info_text,
            font=("Segoe UI", 9),
            bootstyle="secondary",
            justify="left",
            wraplength=550
        ).pack(fill="x")

        # Pencereyi ekranın ortasına konumlandır
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # İlk alana odaklan
        self.entries["host"].focus_set()

    def _save_settings(self):
        """Ayarları kaydet"""
        host = self.entries["host"].get().strip()
        port = self.entries["port"].get().strip()
        user = self.entries["user"].get().strip()
        password = self.entries["password"].get().strip()
        sender = self.entries["sender"].get().strip() or user
        use_smtp = self.use_smtp_var.get()

        # Port doğrulaması
        try:
            port = int(port)
        except ValueError:
            self.status_label.configure(
                text="⛔ Port numarası geçerli bir sayı olmalıdır!",
                bootstyle="danger"
            )
            return

        # E-posta kullanımı aktifse alan doğrulaması
        if use_smtp and not all([host, port, user, password]):
            self.status_label.configure(
                text="⛔ E-posta gönderimi için tüm alanlar doldurulmalıdır!",
                bootstyle="danger"
            )
            return

        # Ayarları kaydet
        save_smtp_settings(host, port, user, password, sender, use_smtp)

        self.status_label.configure(
            text="✅ Ayarlar başarıyla kaydedildi!",
            bootstyle="success"
        )

        # 2 saniye bekleyip pencereyi kapat
        self.after(1500, self.destroy)

    def _test_settings(self):
        """Geçerli ayarlarla e-posta gönderimi test et"""
        from utils.emailer import send_mail

        # Önce geçici olarak ayarları güncelle
        host = self.entries["host"].get().strip()
        port = self.entries["port"].get().strip()
        user = self.entries["user"].get().strip()
        password = self.entries["password"].get().strip()
        sender = self.entries["sender"].get().strip() or user
        use_smtp = self.use_smtp_var.get()

        if not use_smtp:
            self.status_label.configure(
                text="⚠️ E-posta gönderimi pasif durumda! Önce etkinleştirin.",
                bootstyle="warning"
            )
            return

        # Port doğrulaması
        try:
            port = int(port)
        except ValueError:
            self.status_label.configure(
                text="⛔ Port numarası geçerli bir sayı olmalıdır!",
                bootstyle="danger"
            )
            return

        # Alan doğrulaması
        if not all([host, port, user, password]):
            self.status_label.configure(
                text="⛔ Test için tüm alanlar doldurulmalıdır!",
                bootstyle="danger"
            )
            return

        # Geçici ayarları kaydet
        save_smtp_settings(host, port, user, password, sender, use_smtp)

        # Test e-postası göndermeyi dene
        self.status_label.configure(
            text="🔄 E-posta gönderiliyor... Lütfen bekleyin.",
            bootstyle="info"
        )
        self.update_idletasks()

        # Test e-postasını aynı adrese gönder
        success = send_mail(
            user,
            "Diyabet Takip Sistemi - E-posta Test",
            f"Bu bir test e-postasıdır.\n\nSMTP ayarlarınız başarıyla çalışıyor! Hasta şifreleri {user} adresine gönderilecektir."
        )

        if success:
            self.status_label.configure(
                text=f"✅ Test e-postası başarıyla gönderildi: {user}",
                bootstyle="success"
            )
        else:
            self.status_label.configure(
                text="⛔ E-posta gönderimi başarısız! Ayarları kontrol edin.",
                bootstyle="danger"
            ) 