# app_gui.py
import tkinter as tk
import ttkbootstrap as ttk
from gui.login import LoginDialog
from gui.patient import PatientWindow
from gui.doctor import DoctorWindow


def main():
    root = ttk.Window(
        themename="superhero",
        title="💊 Diyabet Takip Sistemi",
        size=(1000, 700),
        position=(150, 100),
        minsize=(800, 600)
    )

    main_container = ttk.Frame(root, padding=40)
    main_container.pack(fill="both", expand=True)

    header_frame = ttk.Frame(main_container)
    header_frame.pack(fill="x", pady=(0, 40))

    title_label = ttk.Label(
        header_frame,
        text="💊 Diyabet Takip Sistemi",
        font=("Segoe UI", 28, "bold"),
        bootstyle="primary"
    )
    title_label.pack()

    subtitle_label = ttk.Label(
        header_frame,
        text="Sağlıklı yaşam için akıllı dijital çözüm",
        font=("Segoe UI", 14),
        bootstyle="secondary"
    )
    subtitle_label.pack(pady=(10, 0))

    features_frame = ttk.Frame(main_container)
    features_frame.pack(fill="x", pady=(0, 40))

    for i in range(3):
        features_frame.columnconfigure(i, weight=1)

    features = [
        ("📊", "Glukoz Takibi", "Kan şekeri değerlerinizi kaydedin ve analiz edin"),
        ("🍎", "Diyet Planı", "Kişiselleştirilmiş beslenme önerileri alın"),
        ("🏃", "Egzersiz Takibi", "Aktivitelerinizi planlayın ve takip edin")
    ]

    for i, (icon, title, desc) in enumerate(features):
        card_frame = ttk.LabelFrame(
            features_frame,
            text=f"{icon} {title}",
            padding=20,
            bootstyle="info"
        )
        card_frame.grid(row=0, column=i, padx=10, sticky="ew")

        ttk.Label(
            card_frame,
            text=desc,
            font=("Segoe UI", 10),
            wraplength=200,
            justify="center"
        ).pack()

    button_frame = ttk.Frame(main_container)
    button_frame.pack(expand=True)

    login_btn = ttk.Button(
        button_frame,
        text="🔓 Sisteme Giriş Yap",
        command=lambda: show_login(root),
        bootstyle="success-outline",
        width=25
    )
    login_btn.pack(pady=10)

    exit_btn = ttk.Button(
        button_frame,
        text="❌ Çıkış",
        command=root.destroy,
        bootstyle="danger-outline",
        width=25
    )
    exit_btn.pack(pady=10)

    footer_frame = ttk.Frame(main_container)
    footer_frame.pack(side="bottom", fill="x")

    ttk.Label(
        footer_frame,
        text="© 2025 Diyabet Takip Sistemi - Tüm Hakları Saklıdır",
        font=("Segoe UI", 9),
        bootstyle="secondary",
        anchor="center"
    ).pack()

    root.bind("<Return>", lambda event: show_login(root))

    root.mainloop()


def show_login(root):
    try:
        dlg = LoginDialog(root)
        root.wait_window(dlg)

        if not dlg.result:
            return

        uid, role = dlg.result["user_id"], dlg.result["role"]
        open_user_panel(root, uid, role)

    except Exception as e:
        print(f"Login error: {str(e)}")
        ttk.dialogs.Messagebox.show_error(
            "Giriş işlemi sırasında hata oluştu.",
            "Hata",
            parent=root
        )


def open_user_panel(root, uid, role):
    try:
        root.withdraw()  # Ana pencereyi gizle

        def on_panel_close(panel):
            panel.destroy()
            root.deiconify()  # Ana pencereyi göster

        if role == "patient":
            patient_window = PatientWindow(root, uid)
            patient_window.protocol("WM_DELETE_WINDOW", lambda: on_panel_close(patient_window))
        elif role == "doctor":
            doctor_window = DoctorWindow(root, uid)
            doctor_window.protocol("WM_DELETE_WINDOW", lambda: on_panel_close(doctor_window))

    except Exception as e:
        print(f"Panel error: {str(e)}")
        root.deiconify()
        ttk.dialogs.Messagebox.show_error(
            f"Panel açılamadı: {str(e)}",
            "Hata",
            parent=root
        )


if __name__ == "__main__":
    main()
