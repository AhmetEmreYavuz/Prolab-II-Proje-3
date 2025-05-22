# gui/add_symptom.py
import tkinter as tk
import ttkbootstrap as ttk
from services.symptom import add_symptom

class AddSymptomDialog(tk.Toplevel):
    """Doktorun hastaya ait semptom ekleyebileceği pencere."""

    def __init__(self, master, patient_id: int, on_added=None):
        super().__init__(master)
        self.title("Belirti Ekle")
        self.resizable(False, False)
        self.patient_id = patient_id
        self.on_added = on_added or (lambda: None)

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(expand=True, fill="both")

        ttk.Label(main_frame, text="Belirti Açıklaması", font=("Segoe UI", 11)).pack(anchor="w")
        self.desc_txt = tk.Text(main_frame, height=4, width=40, font=("Segoe UI", 11))
        self.desc_txt.pack(fill="x", pady=5)

        ttk.Label(main_frame, text="Şiddet (opsiyonel)", font=("Segoe UI", 11)).pack(anchor="w", pady=(10,0))
        self.severity_var = tk.StringVar()
        ttk.Combobox(main_frame, textvariable=self.severity_var,
                     values=("hafif", "orta", "şiddetli"), width=15,
                     state="readonly").pack(anchor="w", pady=5)

        status_lbl = ttk.Label(main_frame, text="", font=("Segoe UI", 10))
        status_lbl.pack(fill="x", pady=(10,0))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(15,0))

        def _save():
            desc = self.desc_txt.get("1.0", tk.END).strip()
            severity = self.severity_var.get() or None
            if not desc:
                status_lbl.config(text="Açıklama boş olamaz!", bootstyle="danger")
                return
            add_symptom(self.patient_id, desc, severity)
            status_lbl.config(text="Belirti kaydedildi.", bootstyle="success")
            self.after(800, lambda: (self.destroy(), self.on_added()))

        ttk.Button(btn_frame, text="Kaydet", bootstyle="success", command=_save, width=12).pack(side="left", padx=(0,5))
        ttk.Button(btn_frame, text="İptal", bootstyle="secondary", command=self.destroy, width=12).pack(side="right", padx=(5,0)) 