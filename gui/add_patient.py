# gui/add_patient.py
import tkinter as tk
import ttkbootstrap as ttk
from services.patient import register_patient
from tkinter import filedialog
from PIL import Image, ImageTk
import io
import base64
from gui.styles import ModernDialog, ModernButton, ModernCard, ICONS, ModernStyles


class AddPatientWindow:
    def __init__(self, master, doctor_id: int, on_added, on_back):
        self.master = master
        self.doctor_id = doctor_id
        self.on_added = on_added
        self.on_back = on_back
        self.profile_image = None
        self.image_path = None


        for widget in master.winfo_children():
            widget.destroy()

        self._create_patient_form()

    def _create_patient_form(self):

        main_container = ttk.Frame(self.master, padding=20)
        main_container.pack(fill="both", expand=True)


        self._create_header(main_container)


        canvas = tk.Canvas(main_container, bg='#2B3E50')
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)


        form_container = ttk.Frame(scrollable_frame, padding=20)
        form_container.pack(fill="both", expand=True)


        form_container.columnconfigure(0, weight=2)
        form_container.columnconfigure(1, weight=1)


        self._create_form_fields(form_container)


        self._create_image_section(form_container)


        self._create_info_section(form_container)


        self._create_action_buttons(form_container)


        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_header(self, parent):

        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 20))


        back_btn = ttk.Button(
            header_frame,
            text="◀ Geri",
            command=self.on_back,
            bootstyle="secondary-outline",
            width=15
        )
        back_btn.pack(side="left")


        title_label = ttk.Label(
            header_frame,
            text="➕ Yeni Hasta Ekle",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side="left", padx=(20, 0))

    def _create_form_fields(self, parent):

        form_card = ttk.LabelFrame(
            parent,
            text="👤 Hasta Bilgileri",
            padding=25,
            bootstyle="info"
        )
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))


        fields = [
            ("🆔 TC Kimlik No:", "tc", "11 haneli TC kimlik numarası"),
            ("👤 Ad Soyad:", "name", "Hastanın tam adı"),
            ("📧 E-posta:", "mail", "Şifre bu adrese gönderilecek"),
            ("📅 Doğum Tarihi:", "dob", "GG.AA.YYYY formatında (opsiyonel)")
        ]

        self.entries = {}
        for i, (label, key, placeholder) in enumerate(fields):

            field_frame = ttk.Frame(form_card)
            field_frame.pack(fill="x", pady=(0, 15))


            ttk.Label(
                field_frame,
                text=label,
                font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=(0, 5))


            entry = ttk.Entry(
                field_frame,
                font=("Segoe UI", 11),
                width=40
            )
            entry.pack(fill="x")


            hint_label = ttk.Label(
                field_frame,
                text=placeholder,
                font=("Segoe UI", 9),
                bootstyle="secondary"
            )
            hint_label.pack(anchor="w", pady=(2, 0))

            self.entries[key] = entry


        self._create_gender_selection(form_card)

    def _create_gender_selection(self, parent):

        gender_frame = ttk.Frame(parent)
        gender_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            gender_frame,
            text="⚧ Cinsiyet:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))


        self.gender = tk.StringVar(value="F")
        gender_options = [
            ("👩 Kadın", "F"),
            ("👨 Erkek", "M"),
            ("🧑 Diğer", "O")
        ]

        radio_frame = ttk.Frame(gender_frame)
        radio_frame.pack(anchor="w")

        for text, value in gender_options:
            ttk.Radiobutton(
                radio_frame,
                text=text,
                variable=self.gender,
                value=value,
                bootstyle="info"
            ).pack(side="left", padx=(0, 20))

    def _create_image_section(self, parent):

        image_card = ttk.LabelFrame(
            parent,
            text="📷 Profil Resmi",
            padding=20,
            bootstyle="success"
        )
        image_card.grid(row=0, column=1, sticky="nsew")


        self.image_container = ttk.Frame(image_card, width=200, height=200)
        self.image_container.pack(pady=(0, 15))
        self.image_container.pack_propagate(False)


        self.img_label = ttk.Label(
            self.image_container,
            text="🖼️\nResim Seçilmedi",
            font=("Segoe UI", 12),
            justify="center",
            bootstyle="secondary"
        )
        self.img_label.pack(fill="both", expand=True)


        ttk.Button(
            image_card,
            text="📁 Resim Seç",
            command=self._select_image,
            bootstyle="primary-outline",
            width=20
        ).pack(fill="x", pady=(0, 10))


        ttk.Label(
            image_card,
            text="• En fazla 2MB\n• JPG veya PNG formatı\n• Kare/portre önerilir",
            font=("Segoe UI", 9),
            bootstyle="secondary",
            justify="left"
        ).pack(anchor="w")

    def _create_info_section(self, parent):

        info_card = ttk.LabelFrame(
            parent,
            text="ℹ️ Bilgilendirme",
            padding=15,
            bootstyle="warning"
        )
        info_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(15, 0))

        ttk.Label(
            info_card,
            text="Hasta kaydının ardından otomatik oluşturulan şifre e-posta adresine gönderilecektir.",
            font=("Segoe UI", 10),
            wraplength=600,
            justify="left"
        ).pack(fill="x")

    def _create_action_buttons(self, parent):

        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))


        ttk.Button(
            button_frame,
            text="💾 Hasta Ekle",
            command=self._save_patient,
            bootstyle="success",
            width=20
        ).pack(side="left", padx=(0, 10))


        ttk.Button(
            button_frame,
            text="🗑️ Temizle",
            command=self._clear_form,
            bootstyle="warning-outline",
            width=20
        ).pack(side="left", padx=(0, 10))


        ttk.Button(
            button_frame,
            text="❌ İptal",
            command=self.on_back,
            bootstyle="danger-outline",
            width=20
        ).pack(side="right")

    def _clear_form(self):

        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.gender.set("F")
        self.profile_image = None
        self.img_label.config(text="🖼️\nResim Seçilmedi")
        if hasattr(self.img_label, 'image'):
            self.img_label.image = None

    def _select_image(self):

        file_types = [
            ("Resim Dosyaları", "*.jpg *.jpeg *.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("Tüm Dosyalar", "*.*")
        ]

        file_path = filedialog.askopenfilename(
            title="Profil Resmi Seç",
            filetypes=file_types,
            parent=self.master
        )

        if not file_path:
            return

        try:

            with Image.open(file_path) as img:

                img.thumbnail((180, 180))


                photo_image = ImageTk.PhotoImage(img)
                self.img_label.config(text="")
                self.img_label.configure(image=photo_image)
                self.img_label.image = photo_image


                with io.BytesIO() as buffer:
                    if file_path.lower().endswith(".png"):
                        img.save(buffer, format="PNG")
                    else:
                        img.save(buffer, format="JPEG", quality=85)

                    self.profile_image = buffer.getvalue()

                self.image_path = file_path

        except Exception as e:
            ttk.dialogs.Messagebox.show_error(
                f"Resim yüklenemedi:\n{str(e)}",
                "Resim Hatası",
                parent=self.master
            )

    def _save_patient(self):


        tc = self.entries["tc"].get().strip()
        name = self.entries["name"].get().strip()
        email = self.entries["mail"].get().strip()
        dob = self.entries["dob"].get().strip()

        from datetime import datetime

        if dob:
            try:
                dob_date = datetime.strptime(dob, "%d.%m.%Y").date()
            except ValueError:
                ttk.dialogs.Messagebox.show_error(
                    "⚠️ Doğum Tarihi Hatası\n\n"
                    "Doğum tarihi GG.AA.YYYY formatında olmalıdır!",
                    "Doğrulama Hatası",
                    parent=self.master
                )
                return
        else:
            dob_date = None


        if not tc or not name or not email:
            ttk.dialogs.Messagebox.show_error(
                "⚠️ Zorunlu Alanlar\n\nTC No, Ad Soyad ve E-posta alanları doldurulmalıdır!",
                "Eksik Bilgi",
                parent=self.master
            )
            return


        if not tc.isdigit() or len(tc) != 11:
            ttk.dialogs.Messagebox.show_error(
                "⚠️ Geçersiz TC No\n\nTC kimlik numarası 11 haneli rakamlardan oluşmalıdır!",
                "Doğrulama Hatası",
                parent=self.master
            )
            return


        if "@" not in email or "." not in email:
            ttk.dialogs.Messagebox.show_error(
                "⚠️ Geçersiz E-posta\n\nLütfen geçerli bir e-posta adresi giriniz!",
                "Doğrulama Hatası",
                parent=self.master
            )
            return


        try:
            uid, pw = register_patient(
                tc, name, email,
                dob_date,
                self.gender.get(),
                self.doctor_id,
                self.profile_image
            )


            from utils.emailer import USE_SMTP

            if USE_SMTP:
                message = (
                    f"✅ Hasta Başarıyla Eklendi!\n\n"
                    f"👤 Ad: {name}\n"
                    f"🆔 ID: {uid}\n"
                    f"📧 Şifre e-posta ile gönderildi: {email}"
                )
            else:
                message = (
                    f"✅ Hasta Başarıyla Eklendi!\n\n"
                    f"👤 Ad: {name}\n"
                    f"🆔 ID: {uid}\n"
                    f"🔑 Şifre: {pw}\n\n"
                    f"⚠️ E-posta ayarları yapılandırılmadığı için\ne-posta gönderilmedi."
                )

            ttk.dialogs.Messagebox.show_info(
                message,
                "🎉 Kayıt Başarılı",
                parent=self.master
            )


            self.on_added()
            self.on_back()

        except Exception as e:
            ttk.dialogs.Messagebox.show_error(
                f"❌ Hasta Kaydedilemedi\n\n{str(e)}",
                "Hata",
                parent=self.master
            )