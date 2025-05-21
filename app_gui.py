# app_gui.py
import tkinter as tk
import ttkbootstrap as ttk
from gui.login import LoginDialog
from gui.patient import PatientWindow
from gui.doctor import DoctorWindow


def main():
    # Modern bootstrap temalı ana pencere
    root = ttk.Window(
        themename="superhero",  # Modern koyu tema
        title="Diyabet Takip Sistemi",
        size=(1024, 768),
        position=(100, 50),
        minsize=(800, 600)
    )
    
    # Ana pencere içeriği (logo veya başlık gösterilebilir)
    main_frame = ttk.Frame(root)
    main_frame.pack(expand=True, fill="both", padx=20, pady=20)
    
    # Başlık ve açıklama
    ttk.Label(
        main_frame, 
        text="Diyabet Takip Sistemi", 
        font=("Segoe UI", 24, "bold")
    ).pack(pady=(100, 10))
    
    ttk.Label(
        main_frame,
        text="Sağlıklı yaşam için dijital çözüm",
        font=("Segoe UI", 14)
    ).pack(pady=(0, 50))
    
    # Giriş butonunu göster
    login_button = ttk.Button(
        main_frame,
        text="Giriş Yap",
        style="primary.TButton",
        width=20,
        command=lambda: show_login(root)
    )
    login_button.pack(pady=20)
    
    # Çıkış butonu
    exit_button = ttk.Button(
        main_frame,
        text="Çıkış",
        style="danger.TButton",
        width=20,
        command=root.destroy
    )
    exit_button.pack(pady=10)
    
    # Footer bilgisi
    ttk.Label(
        main_frame,
        text="© 2023 Diyabet Takip Sistemi - Tüm Hakları Saklıdır",
        font=("Segoe UI", 9)
    ).pack(side="bottom", pady=20)
    
    # Enter tuşu ile giriş yapma
    root.bind("<Return>", lambda event: show_login(root))
    
    root.mainloop()


def show_login(root):
    """Login penceresini gösterir ve sonucu işler"""
    dlg = LoginDialog(root)
    root.wait_window(dlg)

    if not dlg.result:
        return           # giriş başarısız veya iptal

    uid, role = dlg.result["user_id"], dlg.result["role"]

    # Ana pencereyi gizle (kapat değil)
    root.withdraw()

    if role == "patient":
        # Hasta penceresini aç
        patient_window = PatientWindow(root, uid)
        # Hasta penceresi kapanınca ana pencereyi tekrar göster
        patient_window.protocol("WM_DELETE_WINDOW", 
                            lambda: (patient_window.destroy(), root.deiconify()))
    elif role == "doctor":
        # Doktor penceresini aç
        doctor_window = DoctorWindow(root, uid)
        # Doktor penceresi kapanınca ana pencereyi tekrar göster
        doctor_window.protocol("WM_DELETE_WINDOW", 
                           lambda: (doctor_window.destroy(), root.deiconify()))


if __name__ == "__main__":
    main()
