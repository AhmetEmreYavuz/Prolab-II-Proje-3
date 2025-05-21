# gui/add_patient.py
import tkinter as tk
from tkinter import ttk, messagebox
from services.patient import register_patient


class AddPatientDialog(tk.Toplevel):
    def __init__(self, master, doctor_id: int, on_added):
        super().__init__(master)
        self.title("Yeni Hasta")
        self.resizable(False, False)
        self.doctor_id = doctor_id
        self.on_added = on_added   # callback tabloyu yenilemek için

        fields = [
            ("TC No", "tc"),
            ("Ad Soyad", "name"),
            ("E-posta", "mail"),
            ("Doğum Tarihi  (YYYY-MM-DD)", "dob"),
        ]
        self.entries = {}
        for r, (lbl, key) in enumerate(fields):
            ttk.Label(self, text=lbl).grid(row=r, column=0, sticky="e", padx=6, pady=4)
            ent = ttk.Entry(self, width=25)
            ent.grid(row=r, column=1, padx=6, pady=4)
            self.entries[key] = ent

        ttk.Label(self, text="Cinsiyet").grid(row=4, column=0, sticky="e", padx=6, pady=4)
        self.gender = tk.StringVar(value="F")
        ttk.Combobox(self, textvariable=self.gender, values=("F", "M", "O"),
                     width=3, state="readonly").grid(row=4, column=1, sticky="w", padx=6, pady=4)

        ttk.Button(self, text="Kaydet", command=self._save).grid(row=5, columnspan=2, pady=10)

    # ---------------------------------
    def _save(self):
        try:
            uid, pw = register_patient(
                self.entries["tc"].get().strip(),
                self.entries["name"].get().strip(),
                self.entries["mail"].get().strip(),
                self.entries["dob"].get().strip() or None,
                self.gender.get(),
                self.doctor_id,
            )
        except Exception as e:
            messagebox.showerror("Hata", f"Hasta eklenemedi:\n{e}")
            return

        messagebox.showinfo("Başarılı",
                            f"Hasta eklendi (id={uid}).\n"
                            f"Parola e-postaya gönderildi.")
        self.on_added()
        self.destroy()
