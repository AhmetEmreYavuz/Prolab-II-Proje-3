import tkinter as tk
import ttkbootstrap as ttk
from services.symptom import add_symptom, remove_symptom, list_symptoms
import re


def _canon(text: str) -> str:
    """' Poliüri (sık idrara çıkma)  ' → 'poliüri'"""
    return re.sub(r"\s*\([^)]*\)", "", text).strip().lower()


SYMPTOM_CHOICES: list[str] = [
    "poliüri",
    "polifaji",
    "polidipsi",
    "nöropati",
    "kilo kaybı",
    "yorgunluk",
    "yaraların yavaş iyileşmesi",
    "bulanık görme",
]


class AddSymptomDialog(tk.Toplevel):


    # ------------------------------------------------------------------ #
    def __init__(self, master, patient_id: int, on_added=None):
        super().__init__(master)
        self.title("Belirti Ekle / Kaldır")
        self.resizable(False, False)
        self.patient_id = patient_id
        self.on_added = on_added or (lambda: None)


        self.current_set: set[str] = {_canon(s) for s in list_symptoms(self.patient_id)}


        main = ttk.Frame(self, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Belirtileri işaretleyin", bootstyle="primary",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

        list_fr = ttk.Frame(main)
        list_fr.pack(fill="x")


        self.vars: dict[str, tk.BooleanVar] = {}
        for sym in SYMPTOM_CHOICES:
            var = tk.BooleanVar(value=(_canon(sym) in self.current_set))
            ttk.Checkbutton(
                list_fr, text=sym, variable=var, bootstyle="round-toggle"
            ).pack(anchor="w", pady=2)
            self.vars[sym] = var

        ttk.Separator(main, orient="horizontal").pack(fill="x", pady=10)


        ttk.Label(main, text="Diğer / özel belirti (opsiyonel)",
                  font=("Segoe UI", 10)).pack(anchor="w")
        self.extra_txt = tk.Text(main, height=3, width=40, font=("Segoe UI", 10))
        self.extra_txt.pack(fill="x", pady=(4, 0))


        self.status_lbl = ttk.Label(main, text="", font=("Segoe UI", 10))
        self.status_lbl.pack(fill="x", pady=(8, 0))


        btn_fr = ttk.Frame(main)
        btn_fr.pack(pady=(15, 0), fill="x")
        ttk.Button(btn_fr, text="Kaydet", width=14, bootstyle="success",
                   command=self._save).pack(side="left", padx=(0, 6))
        ttk.Button(btn_fr, text="İptal", width=14, bootstyle="secondary",
                   command=self.destroy).pack(side="right", padx=(6, 0))


        self.bind("<Return>", lambda *_: self._save())
        self.bind("<Escape>", lambda *_: self.destroy())

    # ------------------------------------------------------------------ #
    def _save(self):



        chosen = {_canon(sym) for sym, var in self.vars.items() if var.get()}


        extra_raw = self.extra_txt.get("1.0", tk.END).strip()
        if extra_raw:
            chosen.add(_canon(extra_raw))


        if not chosen:
            self.status_lbl.config(text="Lütfen en az bir belirti seçin veya yazın.",
                                   bootstyle="danger")
            return

        try:

            to_add = chosen - self.current_set
            to_del = self.current_set - chosen

            for sym in to_add:
                add_symptom(self.patient_id, sym, None)
            for sym in to_del:
                remove_symptom(self.patient_id, sym)

            self.status_lbl.config(text="Belirtiler güncellendi.", bootstyle="success")
            self.after(700, lambda: (self.destroy(), self.on_added()))

        except Exception as err:
            self.status_lbl.config(text=f"Hata: {err}", bootstyle="danger")
