# gui/add_patient.py
import tkinter as tk
import ttkbootstrap as ttk
from services.patient import register_patient


class AddPatientDialog(tk.Toplevel):
    def __init__(self, master, doctor_id: int, on_added):
        super().__init__(master)
        self.title("Yeni Hasta")
        self.resizable(False, False)
        self.doctor_id = doctor_id
        self.on_added = on_added   # callback tabloyu yenilemek için

        # Ana frame
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(expand=True, fill="both")
        
        # Başlık
        ttk.Label(
            main_frame,
            text="Yeni Hasta Kaydı",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(0, 15))

        # Form alanları
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="x", pady=5)
        
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
        
        # Bilgi etiketi
        self.info_label = ttk.Label(
            main_frame,
            text="Hasta kaydının ardından otomatik oluşturulan şifre e-posta adresine gönderilecektir.",
            wraplength=350,
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
