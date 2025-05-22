# gui/add_patient.py
import tkinter as tk
import ttkbootstrap as ttk
from services.patient import register_patient
from tkinter import filedialog
from PIL import Image, ImageTk
import io
import base64


class AddPatientDialog(tk.Toplevel):
    def __init__(self, master, doctor_id: int, on_added):
        super().__init__(master)
        self.title("Yeni Hasta")
        self.resizable(False, False)
        self.doctor_id = doctor_id
        self.on_added = on_added   # callback tabloyu yenilemek için
        self.profile_image = None  # Seçilen resim verisini saklar
        self.image_path = None     # Seçilen dosya yolunu saklar

        # Ana frame
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(expand=True, fill="both")
        
        # Başlık
        ttk.Label(
            main_frame,
            text="Yeni Hasta Kaydı",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(0, 15))

        # İki sütunlu layout
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Sol sütun - Form alanları
        form_frame = ttk.Frame(content_frame)
        form_frame.pack(side="left", fill="x", pady=5, padx=(0, 10))
        
        fields = [
            ("TC No:", "tc"),
            ("Ad Soyad:", "name"),
            ("E-posta:", "mail"),
            ("Doğum Tarihi  (YYYY-MM-DD):", "dob"),
        ]
        
        self.entries = {}
        for r, (lbl, key) in enumerate(fields):
            ttk.Label(
                form_frame,
                text=lbl,
                font=("Segoe UI", 11)
            ).grid(row=r, column=0, sticky="e", padx=6, pady=6)
            
            ent = ttk.Entry(form_frame, width=25, font=("Segoe UI", 11))
            ent.grid(row=r, column=1, padx=6, pady=6)
            self.entries[key] = ent

        # Cinsiyet seçeneği
        ttk.Label(
            form_frame,
            text="Cinsiyet:",
            font=("Segoe UI", 11)
        ).grid(row=len(fields), column=0, sticky="e", padx=6, pady=6)
        
        self.gender = tk.StringVar(value="F")
        gender_combo = ttk.Combobox(
            form_frame,
            textvariable=self.gender,
            values=("F", "M", "O"),
            width=5,
            font=("Segoe UI", 11),
            state="readonly"
        )
        gender_combo.grid(row=len(fields), column=1, sticky="w", padx=6, pady=6)
        
        # Sağ sütun - Profil resmi
        image_frame = ttk.LabelFrame(content_frame, text="Profil Resmi", padding=10)
        image_frame.pack(side="right", fill="both", pady=5)
        
        # Varsayılan resim placeholder
        self.img_label = ttk.Label(
            image_frame, 
            text="Resim Seçilmedi",
            width=20,
            height=10
        )
        self.img_label.pack(padx=10, pady=10)
        
        # Resim seçme butonu
        ttk.Button(
            image_frame,
            text="Resim Seç",
            command=self._select_image
        ).pack(fill="x", padx=10, pady=(0, 10))
        
        # Bilgi metni
        ttk.Label(
            image_frame,
            text="En fazla 2MB boyutunda\n.jpg veya .png formatında\nkare/portre resim önerilir",
            font=("Segoe UI", 9),
            justify="left",
            bootstyle="secondary"
        ).pack(padx=10)
        
        # Bilgi etiketi
        self.info_label = ttk.Label(
            main_frame,
            text="Hasta kaydının ardından otomatik oluşturulan şifre e-posta adresine gönderilecektir.",
            wraplength=450,
            justify="left",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        )
        self.info_label.pack(pady=10, fill="x")

        # Butonlar
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Button(
            btn_frame,
            text="Kaydet",
            command=self._save,
            bootstyle="success",
            width=15
        ).pack(side="left", padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="İptal",
            command=self.destroy,
            bootstyle="danger",
            width=15
        ).pack(side="right", padx=(5, 0))

    # ---------------------------------
    def _select_image(self):
        """Profil resmi seçme işlemi"""
        file_types = [
            ("Resim Dosyaları", "*.jpg *.jpeg *.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("Tüm Dosyalar", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Profil Resmi Seç",
            filetypes=file_types
        )
        
        if not file_path:
            return  # Kullanıcı iptal etti
        
        try:
            # Resmi aç ve küçültülmüş thumbnail oluştur
            with Image.open(file_path) as img:
                # Resmi makul bir boyuta küçült
                img.thumbnail((200, 200))
                
                # Resmi önizleme için göster
                photo_image = ImageTk.PhotoImage(img)
                self.img_label.config(image=photo_image, text="")
                self.img_label.image = photo_image  # Referans tutmak için
                
                # Resmi binary olarak sakla
                with io.BytesIO() as buffer:
                    if file_path.lower().endswith(".png"):
                        img.save(buffer, format="PNG")
                    else:
                        img.save(buffer, format="JPEG", quality=80)
                    
                    self.profile_image = buffer.getvalue()
                
                self.image_path = file_path
                
        except Exception as e:
            ttk.dialogs.Messagebox.show_error(
                f"Resim yüklenemedi: {str(e)}",
                "Resim Hatası"
            )

    # ---------------------------------
    def _save(self):
        # Alanları kontrol et
        tc = self.entries["tc"].get().strip()
        name = self.entries["name"].get().strip()
        email = self.entries["mail"].get().strip()
        dob = self.entries["dob"].get().strip()
        
        # Zorunlu alanları kontrol et
        if not tc or not name or not email:
            ttk.dialogs.Messagebox.show_error(
                "TC No, Ad Soyad ve E-posta alanları zorunludur!",
                "Eksik Bilgi"
            )
            return
        
        # Kaydet
        try:
            print(f"Trying to register patient: {name}")
            uid, pw = register_patient(
                tc,
                name,
                email,
                dob or None,
                self.gender.get(),
                self.doctor_id,
                self.profile_image
            )
            print(f"Patient registered successfully with ID: {uid}")
            
            # E-posta gönderimi hakkında bilgi
            from utils.emailer import USE_SMTP
            
            if USE_SMTP:
                message = (
                    f"Hasta başarıyla eklendi (ID: {uid}).\n\n"
                    f"Otomatik oluşturulan şifre e-posta ile gönderildi:\n"
                    f"E-posta: {email}"
                )
            else:
                message = (
                    f"Hasta başarıyla eklendi (ID: {uid}).\n\n"
                    f"Otomatik oluşturulan şifre:\n"
                    f"TC No: {tc}\n"
                    f"Şifre: {pw}\n\n"
                    "E-posta ayarları yapılandırılmadığı için e-posta gönderilmedi."
                )
            
            # Callback'i ve mesajı sakla çünkü destroy'dan sonra self erişilemez olacak
            refresh_callback = self.on_added
            success_message = message
            master = self.master
            
            # Dialog'u hemen kapat
            self.destroy()
            
            # Pencere kapandıktan sonra bilgi mesajını göster ve ana pencereyi yenile
            master.after(100, lambda: (
                ttk.dialogs.Messagebox.show_info(
                    success_message,
                    "Kayıt Başarılı"
                ),
                refresh_callback()
            ))
            
        except Exception as e:
            error_message = f"Hasta eklenemedi:\n{str(e)}"
            print(f"Error registering patient: {error_message}")
            ttk.dialogs.Messagebox.show_error(
                error_message,
                "Hata"
            )
            return
