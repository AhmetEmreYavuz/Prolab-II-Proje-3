# gui/change_password.py
import tkinter as tk
import ttkbootstrap as ttk
from services.user import update_password


class ChangePasswordDialog(tk.Toplevel):
    """Kullanıcının şifresini değiştirmek için kullanılan dialog."""
    
    def __init__(self, master, user_id: int, is_first_login=False):
        super().__init__(master)
        self.title("Şifre Değiştir")
        self.resizable(False, False)
        self.user_id = user_id
        self.is_first_login = is_first_login
        
        # Bu bir ilk giriş ise pencere kapanmasın
        if is_first_login:
            self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Ana frame
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(expand=True, fill="both")
        
        # Başlık
        title = "Şifrenizi Değiştirin" if not is_first_login else "Hoş Geldiniz! İlk Girişte Şifrenizi Değiştirmelisiniz"
        ttk.Label(
            main_frame,
            text=title,
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(0, 15))
        
        if is_first_login:
            ttk.Label(
                main_frame,
                text="Güvenliğiniz için, otomatik oluşturulan şifrenizi değiştirmeniz gerekmektedir.",
                wraplength=350,
                justify="left"
            ).pack(pady=(0, 15))
        
        # Form alanları
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill="x", pady=5)
        
        # Mevcut şifre
        ttk.Label(
            form_frame,
            text="Mevcut Şifre:",
            font=("Segoe UI", 11)
        ).grid(row=0, column=0, sticky="e", padx=6, pady=6)
        
        self.current_password = ttk.Entry(form_frame, width=25, font=("Segoe UI", 11), show="●")
        self.current_password.grid(row=0, column=1, padx=6, pady=6)
        self.current_password.focus()
        
        # Yeni şifre
        ttk.Label(
            form_frame,
            text="Yeni Şifre:",
            font=("Segoe UI", 11)
        ).grid(row=1, column=0, sticky="e", padx=6, pady=6)
        
        self.new_password = ttk.Entry(form_frame, width=25, font=("Segoe UI", 11), show="●")
        self.new_password.grid(row=1, column=1, padx=6, pady=6)
        
        # Yeni şifre tekrar
        ttk.Label(
            form_frame,
            text="Yeni Şifre Tekrar:",
            font=("Segoe UI", 11)
        ).grid(row=2, column=0, sticky="e", padx=6, pady=6)
        
        self.confirm_password = ttk.Entry(form_frame, width=25, font=("Segoe UI", 11), show="●")
        self.confirm_password.grid(row=2, column=1, padx=6, pady=6)
        
        # Durum mesajı
        self.status_label = ttk.Label(
            main_frame,
            text="",
            wraplength=350,
            justify="left",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=(10, 0), fill="x")
        
        # Butonlar
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(15, 0))
        
        ttk.Button(
            btn_frame,
            text="Şifreyi Değiştir",
            command=self._change_password,
            bootstyle="success",
            width=15
        ).pack(side="left", padx=(0, 5))
        
        if not is_first_login:
            ttk.Button(
                btn_frame,
                text="İptal",
                command=self.destroy,
                bootstyle="danger",
                width=15
            ).pack(side="right", padx=(5, 0))
        
        # Enter tuşu ile işlemi başlat
        self.bind("<Return>", lambda event: self._change_password())
        
    def _change_password(self):
        """Şifre değiştirme işlemini gerçekleştirir."""
        current_pw = self.current_password.get().strip()
        new_pw = self.new_password.get().strip()
        confirm_pw = self.confirm_password.get().strip()
        
        # Formun doğrulaması
        if not current_pw or not new_pw or not confirm_pw:
            self.status_label.config(
                text="Tüm alanlar doldurulmalıdır!",
                bootstyle="danger"
            )
            return
        
        if new_pw != confirm_pw:
            self.status_label.config(
                text="Yeni şifreler eşleşmiyor!",
                bootstyle="danger"
            )
            return
        
        if len(new_pw) < 6:
            self.status_label.config(
                text="Yeni şifre en az 6 karakter uzunluğunda olmalıdır!",
                bootstyle="danger"
            )
            return
            
        # Şifre değiştirme
        success = update_password(self.user_id, current_pw, new_pw)
        if success:
            self.status_label.config(
                text="Şifreniz başarıyla değiştirildi!",
                bootstyle="success"
            )
            # Başarılı işlemden sonra 1.5 saniye sonra pencereyi kapat
            self.after(1500, self.destroy)
        else:
            self.status_label.config(
                text="Mevcut şifreniz yanlış! Lütfen tekrar deneyin.",
                bootstyle="danger"
            ) 