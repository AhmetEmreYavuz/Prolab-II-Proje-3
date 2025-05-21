# gui/patient.py
import tkinter as tk
import ttkbootstrap as ttk
from datetime import date
from services.glucose import add_glucose, list_today
from services.daily import upsert_status
from services.rules import evaluate_day
from utils.db import db_cursor


class PatientWindow(tk.Toplevel):
    """Hastanın ölçüm, diyet ve egzersiz girebildiği pencere."""

    def __init__(self, master, patient_id: int):
        super().__init__(master)
        self.patient_id = patient_id
        self.title("Hasta Paneli")
        self.geometry("800x600")
        self.configure(bg="#2b3e50")  # Superhero temasına uygun arka plan
        
        # Hasta bilgisini getir
        with db_cursor() as cur:
            cur.execute("SELECT full_name FROM users WHERE id=%s", (patient_id,))
            user_data = cur.fetchone()
            self.patient_name = user_data["full_name"] if user_data else "Hasta"
        
        # Ana başlık
        header_frame = ttk.Frame(self, bootstyle="dark")
        header_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            header_frame,
            text=f"Hoş Geldiniz, {self.patient_name}",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-light",
            padding=10
        ).pack(fill="x")
        
        # Ana içerik container
        content_frame = ttk.Frame(self)
        content_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Sol panel - Ölçümler
        left_frame = ttk.LabelFrame(
            content_frame, 
            text="Kan Şekeri Takibi",
            padding=15,
            bootstyle="info"
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # ---------- Yeni Ölçüm ----------
        meas_frm = ttk.Frame(left_frame)
        meas_frm.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            meas_frm, 
            text="Yeni Ölçüm Ekle",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))

        input_frame = ttk.Frame(meas_frm)
        input_frame.pack(fill="x")
        
        ttk.Label(
            input_frame, 
            text="Değer (mg/dL):",
            font=("Segoe UI", 11)
        ).pack(side="left", padx=(0, 10))
        
        self.val_ent = ttk.Entry(input_frame, width=10, font=("Segoe UI", 11))
        self.val_ent.pack(side="left", padx=(0, 10))

        ttk.Button(
            input_frame, 
            text="Kaydet", 
            command=self._save_glucose,
            bootstyle="success",
            width=10
        ).pack(side="left")
        
        # Günlük özet
        sum_frame = ttk.Frame(left_frame)
        sum_frame.pack(fill="x", pady=10)
        
        ttk.Label(
            sum_frame,
            text="Günlük Özet:",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.sum_lbl = ttk.Label(
            sum_frame, 
            text="", 
            font=("Segoe UI", 11),
            bootstyle="info"
        )
        self.sum_lbl.pack(anchor="w", pady=5)
        
        # Ölçüm geçmişi
        history_frame = ttk.Frame(left_frame)
        history_frame.pack(fill="both", expand=True, pady=10)
        
        ttk.Label(
            history_frame,
            text="Bugünkü Ölçümler:",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        # Tablo oluştur
        columns = ("time", "value", "status")
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",
            height=6,
            bootstyle="info"
        )
        
        # Sütun başlıkları
        self.history_tree.heading("time", text="Saat")
        self.history_tree.heading("value", text="Değer (mg/dL)")
        self.history_tree.heading("status", text="Durum")
        
        # Sütun genişlikleri
        self.history_tree.column("time", width=80, anchor="center")
        self.history_tree.column("value", width=100, anchor="center")
        self.history_tree.column("status", width=120, anchor="center")
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(
            history_frame, 
            orient="vertical", 
            command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Yerleştir
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sağ panel - Diyet ve Egzersiz
        right_frame = ttk.LabelFrame(
            content_frame, 
            text="Diyet ve Egzersiz",
            padding=15,
            bootstyle="warning"
        )
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # ---------- Diyet ----------
        diet_frame = ttk.Frame(right_frame)
        diet_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            diet_frame,
            text="Diyet Planı",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        diet_input_frame = ttk.Frame(diet_frame)
        diet_input_frame.pack(fill="x")
        
        ttk.Label(
            diet_input_frame, 
            text="Diyet Türü:",
            font=("Segoe UI", 11)
        ).pack(side="left", padx=(0, 10))
        
        self.diet_cmb = ttk.Combobox(
            diet_input_frame, 
            width=15, 
            state="readonly",
            font=("Segoe UI", 11),
            values=("low_sugar", "sugar_free", "balanced")
        )
        self.diet_cmb.current(0)
        self.diet_cmb.pack(side="left", padx=(0, 10))
        
        self.diet_chk = tk.BooleanVar()
        ttk.Checkbutton(
            diet_input_frame, 
            text="Uygulandı", 
            variable=self.diet_chk,
            bootstyle="round-toggle"
        ).pack(side="left")
        
        # ---------- Egzersiz ----------
        exercise_frame = ttk.Frame(right_frame)
        exercise_frame.pack(fill="x", pady=15)
        
        ttk.Label(
            exercise_frame,
            text="Egzersiz Planı",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        ex_input_frame = ttk.Frame(exercise_frame)
        ex_input_frame.pack(fill="x")
        
        ttk.Label(
            ex_input_frame, 
            text="Egzersiz Türü:",
            font=("Segoe UI", 11)
        ).pack(side="left", padx=(0, 10))
        
        self.ex_cmb = ttk.Combobox(
            ex_input_frame, 
            width=15, 
            state="readonly",
            font=("Segoe UI", 11),
            values=("walk", "bike", "clinic")
        )
        self.ex_cmb.current(0)
        self.ex_cmb.pack(side="left", padx=(0, 10))
        
        self.ex_chk = tk.BooleanVar()
        ttk.Checkbutton(
            ex_input_frame, 
            text="Yapıldı", 
            variable=self.ex_chk,
            bootstyle="round-toggle"
        ).pack(side="left")
        
        # Kaydet butonu
        save_frame = ttk.Frame(right_frame)
        save_frame.pack(fill="x", pady=15)
        
        ttk.Button(
            save_frame, 
            text="Günlük Durumu Kaydet", 
            command=self._save_status,
            bootstyle="warning",
            width=25
        ).pack(anchor="center")
        
        # ---------- Uyarılar ----------
        alerts_frame = ttk.LabelFrame(
            right_frame, 
            text="Uyarılar ve Öneriler",
            padding=10,
            bootstyle="danger"
        )
        alerts_frame.pack(fill="both", expand=True, pady=(15, 0))
        
        self.alert_box = tk.Text(
            alerts_frame, 
            height=6, 
            state="disabled",
            font=("Segoe UI", 10),
            bg="#3e5368",  # Koyu tema uyumlu
            fg="#ffffff"   # Beyaz yazı
        )
        
        # Scrollbar ekle
        alert_scrollbar = ttk.Scrollbar(
            alerts_frame, 
            orient="vertical", 
            command=self.alert_box.yview
        )
        self.alert_box.configure(yscrollcommand=alert_scrollbar.set)
        
        # Yerleştir
        self.alert_box.pack(side="left", fill="both", expand=True)
        alert_scrollbar.pack(side="right", fill="y")
        
        # Alt panel - Butonlar
        footer_frame = ttk.Frame(self)
        footer_frame.pack(fill="x", padx=20, pady=15)
        
        ttk.Button(
            footer_frame, 
            text="Yenile", 
            command=self._refresh,
            bootstyle="secondary",
            width=15
        ).pack(side="left")
        
        ttk.Button(
            footer_frame, 
            text="Kapat", 
            command=self.destroy,
            bootstyle="danger",
            width=15
        ).pack(side="right")
        
        self._refresh()

    # ------------------------------------------------------------------
    def _save_glucose(self):
        """Kan şekeri ölçümünü kaydeder."""
        try:
            value = float(self.val_ent.get())
        except ValueError:
            ttk.dialogs.Messagebox.show_error(
                "Geçersiz sayı girdiniz.",
                "Hata"
            )
            return

        add_glucose(self.patient_id, value)
        self.val_ent.delete(0, tk.END)
        self._refresh()

    # ------------------------------------------------------------------
    def _save_status(self):
        """Günlük diyet & egzersiz durumunu kaydeder."""
        upsert_status(
            self.patient_id,
            self.diet_cmb.get(),  self.diet_chk.get(),
            self.ex_cmb.get(),    self.ex_chk.get()
        )
        ttk.dialogs.Messagebox.show_info(
            "Günlük durum başarıyla kaydedildi.",
            "Bilgi"
        )

    # ------------------------------------------------------------------
    def _refresh(self):
        """Ölçüm özetini ve uyarıları yeniler."""
        readings = list_today(self.patient_id)
        
        # Tablo içeriğini temizle
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Yeni verileri ekle
        if readings:
            avg = sum(r["value_mg_dl"] for r in readings) / len(readings)
            self.sum_lbl.config(
                text=f"{len(readings)} ölçüm  •  Ortalama {avg:.1f} mg/dL",
                bootstyle="info"
            )
            
            # Tabloyu doldur
            for r in readings:
                time_str = r["reading_dt"].strftime("%H:%M")
                value = r["value_mg_dl"]
                
                # Değere göre durum belirleme
                if value < 70:
                    status = "Düşük"
                    status_style = "danger"
                elif value > 180:
                    status = "Yüksek"
                    status_style = "danger"
                else:
                    status = "Normal"
                    status_style = "success"
                
                self.history_tree.insert(
                    "", 
                    tk.END, 
                    values=(time_str, f"{value:.1f}", status),
                    tags=(status_style,)
                )
                
            # Durum renklerini ayarla
            self.history_tree.tag_configure("danger", background="#f8d7da")
            self.history_tree.tag_configure("success", background="#d4edda")
                
        else:
            self.sum_lbl.config(
                text="Bugün henüz ölçüm yapılmamış.",
                bootstyle="secondary"
            )

        # Doz & uyarı hesapla
        evaluate_day(self.patient_id, date.today())

        # Son 5 uyarıyı getir
        with db_cursor() as cur:
            cur.execute(
                "SELECT created_dt, message FROM alerts "
                "WHERE patient_id=%s ORDER BY created_dt DESC LIMIT 5",
                (self.patient_id,),
            )
            alerts = cur.fetchall()

        self.alert_box.configure(state="normal")
        self.alert_box.delete("1.0", tk.END)
        for a in alerts:
            t = a["created_dt"].strftime("%H:%M")
            self.alert_box.insert(tk.END, f"{t}  {a['message']}\n")
        self.alert_box.configure(state="disabled")
