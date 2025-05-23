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
        
        # Clear the master window
        for widget in master.winfo_children():
            widget.destroy()
        
        self._create_patient_form()

    def _create_patient_form(self):
        """Create modern patient registration form."""
        # Main container with padding
        main_container = ttk.Frame(self.master, padding=20)
        main_container.pack(fill="both", expand=True)
        
        # Header with back button and title
        self._create_header(main_container)
        
        # Scrollable content
        canvas = tk.Canvas(main_container, bg='#2B3E50')
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Form content
        form_container = ttk.Frame(scrollable_frame, padding=20)
        form_container.pack(fill="both", expand=True)
        
        # Configure responsive layout
        form_container.columnconfigure(0, weight=2)
        form_container.columnconfigure(1, weight=1)
        
        # Left side - Form fields
        self._create_form_fields(form_container)
        
        # Right side - Profile image
        self._create_image_section(form_container)
        
        # Info section
        self._create_info_section(form_container)
        
        # Action buttons
        self._create_action_buttons(form_container)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_header(self, parent):
        """Create header with back button and title."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Back button
        back_btn = ttk.Button(
            header_frame,
            text="◀ Geri",
            command=self.on_back,
            bootstyle="secondary-outline",
            width=15
        )
        back_btn.pack(side="left")
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="➕ Yeni Hasta Ekle",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side="left", padx=(20, 0))
    
    def _create_form_fields(self, parent):
        """Create form input fields."""
        form_card = ttk.LabelFrame(
            parent, 
            text="👤 Hasta Bilgileri", 
            padding=25,
            bootstyle="info"
        )
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Form fields data
        fields = [
            ("🆔 TC Kimlik No:", "tc", "11 haneli TC kimlik numarası"),
            ("👤 Ad Soyad:", "name", "Hastanın tam adı"),
            ("📧 E-posta:", "mail", "Şifre bu adrese gönderilecek"),
            ("📅 Doğum Tarihi:", "dob", "YYYY-MM-DD formatında (opsiyonel)")
        ]
        
        self.entries = {}
        for i, (label, key, placeholder) in enumerate(fields):
            # Field container
            field_frame = ttk.Frame(form_card)
            field_frame.pack(fill="x", pady=(0, 15))
            
            # Label
            ttk.Label(
                field_frame,
                text=label,
                font=("Segoe UI", 11, "bold")
            ).pack(anchor="w", pady=(0, 5))
            
            # Entry
            entry = ttk.Entry(
                field_frame,
                font=("Segoe UI", 11),
                width=40
            )
            entry.pack(fill="x")
            
            # Placeholder hint
            hint_label = ttk.Label(
                field_frame,
                text=placeholder,
                font=("Segoe UI", 9),
                bootstyle="secondary"
            )
            hint_label.pack(anchor="w", pady=(2, 0))
            
            self.entries[key] = entry
        
        # Gender selection
        self._create_gender_selection(form_card)
    
    def _create_gender_selection(self, parent):
        """Create gender selection."""
        gender_frame = ttk.Frame(parent)
        gender_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            gender_frame,
            text="⚧ Cinsiyet:",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 8))
        
        # Gender radio buttons
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
        """Create profile image section."""
        image_card = ttk.LabelFrame(
            parent, 
            text="📷 Profil Resmi", 
            padding=20,
            bootstyle="success"
        )
        image_card.grid(row=0, column=1, sticky="nsew")
        
        # Image preview container
        self.image_container = ttk.Frame(image_card, width=200, height=200)
        self.image_container.pack(pady=(0, 15))
        self.image_container.pack_propagate(False)
        
        # Default image placeholder
        self.img_label = ttk.Label(
            self.image_container,
            text="🖼️\nResim Seçilmedi",
            font=("Segoe UI", 12),
            justify="center",
            bootstyle="secondary"
        )
        self.img_label.pack(fill="both", expand=True)
        
        # Image selection button
        ttk.Button(
            image_card,
            text="📁 Resim Seç",
            command=self._select_image,
            bootstyle="primary-outline",
            width=20
        ).pack(fill="x", pady=(0, 10))
        
        # Info text
        ttk.Label(
            image_card,
            text="• En fazla 2MB\n• JPG veya PNG formatı\n• Kare/portre önerilir",
            font=("Segoe UI", 9),
            bootstyle="secondary",
            justify="left"
        ).pack(anchor="w")
    
    def _create_info_section(self, parent):
        """Create info section."""
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
        """Create action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        
        # Save button
        ttk.Button(
            button_frame,
            text="💾 Hasta Ekle",
            command=self._save_patient,
            bootstyle="success",
            width=20
        ).pack(side="left", padx=(0, 10))
        
        # Clear button
        ttk.Button(
            button_frame,
            text="🗑️ Temizle",
            command=self._clear_form,
            bootstyle="warning-outline",
            width=20
        ).pack(side="left", padx=(0, 10))
        
        # Cancel button
        ttk.Button(
            button_frame,
            text="❌ İptal",
            command=self.on_back,
            bootstyle="danger-outline",
            width=20
        ).pack(side="right")

    def _clear_form(self):
        """Clear all form fields."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.gender.set("F")
        self.profile_image = None
        self.img_label.config(text="🖼️\nResim Seçilmedi")
        if hasattr(self.img_label, 'image'):
            self.img_label.image = None

    def _select_image(self):
        """Handle image selection."""
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
            # Load and process image
            with Image.open(file_path) as img:
                # Create thumbnail
                img.thumbnail((180, 180))
                
                # Show preview
                photo_image = ImageTk.PhotoImage(img)
                self.img_label.config(text="")
                self.img_label.configure(image=photo_image)
                self.img_label.image = photo_image
                
                # Store image data
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
        """Save patient with validation."""
        # Get form data
        tc = self.entries["tc"].get().strip()
        name = self.entries["name"].get().strip()
        email = self.entries["mail"].get().strip()
        dob = self.entries["dob"].get().strip()
        
        # Validate required fields
        if not tc or not name or not email:
            ttk.dialogs.Messagebox.show_error(
                "⚠️ Zorunlu Alanlar\n\nTC No, Ad Soyad ve E-posta alanları doldurulmalıdır!",
                "Eksik Bilgi",
                parent=self.master
            )
            return
        
        # Validate TC number
        if not tc.isdigit() or len(tc) != 11:
            ttk.dialogs.Messagebox.show_error(
                "⚠️ Geçersiz TC No\n\nTC kimlik numarası 11 haneli rakamlardan oluşmalıdır!",
                "Doğrulama Hatası",
                parent=self.master
            )
            return
        
        # Validate email
        if "@" not in email or "." not in email:
            ttk.dialogs.Messagebox.show_error(
                "⚠️ Geçersiz E-posta\n\nLütfen geçerli bir e-posta adresi giriniz!",
                "Doğrulama Hatası",
                parent=self.master
            )
            return
        
        # Save patient
        try:
            uid, pw = register_patient(
                tc, name, email,
                dob or None,
                self.gender.get(),
                self.doctor_id,
                self.profile_image
            )
            
            # Show success message
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
            
            # Go back and refresh
            self.on_added()
            self.on_back()
            
        except Exception as e:
            ttk.dialogs.Messagebox.show_error(
                f"❌ Hasta Kaydedilemedi\n\n{str(e)}",
                "Hata",
                parent=self.master
            )
