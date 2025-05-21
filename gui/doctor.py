# gui/doctor.py
import tkinter as tk
import ttkbootstrap as ttk
from utils.db import db_cursor
from gui.add_patient import AddPatientDialog
from gui.patient import PatientWindow          # Hasta paneli
from gui.status import StatusWindow            # Günlük diyet/egzersiz

class DoctorWindow(tk.Toplevel):
    """Doktorun hasta listesini görüntülediği ve yönetebildiği pencere."""

    def __init__(self, master, doctor_id: int):
        super().__init__(master)
        self.title("Doktor Paneli")
        self.geometry("1000x700")  # Daha büyük başlangıç boyutu
        self.configure(bg="#2b3e50")  # Superhero temasına uygun arka plan
        
        # Pencere merkezde açılsın
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        self.doctor_id = doctor_id   # giriş yapan doktorun id'si
        
        # Doktor bilgisini getir
        with db_cursor() as cur:
            cur.execute("SELECT full_name FROM users WHERE id=%s", (doctor_id,))
            user_data = cur.fetchone()
            self.doctor_name = user_data["full_name"] if user_data else "Doktor"
        
        # Ana başlık
        header_frame = ttk.Frame(self, bootstyle="dark")
        header_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(
            header_frame,
            text=f"Doktor Paneli - {self.doctor_name}",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-light",
            padding=10
        ).pack(fill="x")
        
        # Ana içerik container
        content_frame = ttk.Frame(self)
        content_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Hasta listesi başlığı
        ttk.Label(
            content_frame,
            text="Hasta Listesi",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Arama çubuğu
        search_frame = ttk.Frame(content_frame)
        search_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(
            search_frame,
            text="Hasta Ara:",
            font=("Segoe UI", 11)
        ).pack(side="left", padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_frame, 
            width=30,
            font=("Segoe UI", 11),
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        
        # Arama butonu
        ttk.Button(
            search_frame,
            text="Ara",
            bootstyle="info",
            command=self._filter_patients
        ).pack(side="right", padx=(10, 0))
        
        # Hasta sayısı bilgisi
        self.patient_count_lbl = ttk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        self.patient_count_lbl.pack(anchor="w", pady=(0, 5))
        
        # ---------- Hasta listesi ----------
        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_frame, 
            columns=("tc", "name"), 
            show="headings", 
            height=15,
            bootstyle="info"
        )
        self.tree.heading("tc", text="TC No")
        self.tree.heading("name", text="Hasta Adı")
        # Responsive sütun boyutları 
        self.tree.column("tc", width=200, minwidth=150, anchor="center")
        self.tree.column("name", width=400, minwidth=300, anchor="w")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Yerleştirme
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._open_patient)   # çift tıkla aç
        
        # Seçili hasta bilgisi
        self.selected_lbl = ttk.Label(
            content_frame,
            text="Seçili hasta: Yok",
            font=("Segoe UI", 11),
            bootstyle="secondary"
        )
        self.selected_lbl.pack(anchor="w", pady=(5, 10))
        
        # Seçim değişince etiketi güncelle
        self.tree.bind("<<TreeviewSelect>>", self._update_selection_label)

        # ---------- Buton Frame ----------
        btn_frm = ttk.Frame(content_frame)
        btn_frm.pack(fill="x", pady=(0, 15))
        
        # Buton satırları - 2 satıra böl
        btn_row1 = ttk.Frame(btn_frm)
        btn_row1.pack(fill="x", pady=(0, 10))
        
        btn_row2 = ttk.Frame(btn_frm)
        btn_row2.pack(fill="x")

        # Responsive butonlar - İlk satır
        btn1 = ttk.Button(
            btn_row1, 
            text="Yeni Hasta Ekle",
            bootstyle="success",
            command=lambda: AddPatientDialog(self, doctor_id, self._refresh)
        )
        btn1.pack(side="left", padx=(0, 10), fill="x", expand=True)

        btn2 = ttk.Button(
            btn_row1, 
            text="Hasta Panelini Aç",
            bootstyle="primary",
            command=self._open_patient
        )
        btn2.pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        # Responsive butonlar - İkinci satır
        btn3 = ttk.Button(                                   
            btn_row2, 
            text="Günlük Durum Göster",
            bootstyle="warning",
            command=self._show_status
        )
        btn3.pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        btn4 = ttk.Button(
            btn_row2,
            text="Yenile",
            bootstyle="secondary",
            command=self._refresh
        )
        btn4.pack(side="right", padx=(10, 0), fill="x", expand=True)
        
        # Footer
        footer_frame = ttk.Frame(self)
        footer_frame.pack(fill="x", padx=20, pady=15)
        
        ttk.Label(
            footer_frame,
            text="© 2023 Diyabet Takip Sistemi - Doktor Arayüzü",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(side="left")
        
        ttk.Button(
            footer_frame,
            text="Kapat",
            bootstyle="danger",
            width=15,
            command=self.destroy
        ).pack(side="right")

        self._refresh()   # ilk tablo yüklemesi
        
        # Arama çubuğu değişikliklerini dinle
        self.search_var.trace("w", lambda name, index, mode: self._filter_patients())

    # ------------------------------------------------------------
    def _refresh(self):
        """Hasta listesini yeniler."""
        self.tree.delete(*self.tree.get_children())

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.tc_no, u.full_name
                FROM patients p
                JOIN users    u ON p.id = u.id
                WHERE p.doctor_id = %s
                ORDER BY u.full_name
                """,
                (self.doctor_id,)
            )
            rows = cur.fetchall()

        for row in rows:
            # item kimliğinde hasta id'sini saklıyoruz
            self.tree.insert(
                "", tk.END,
                iid=row["id"],
                values=(row["tc_no"], row["full_name"])
            )
            
        # Hasta sayısını güncelle
        patient_count = len(rows)
        if patient_count > 0:
            self.patient_count_lbl.config(
                text=f"Toplam {patient_count} hasta bulundu.",
                bootstyle="info"
            )
        else:
            self.patient_count_lbl.config(
                text="Bu doktora bağlı hasta yok.",
                bootstyle="warning"
            )
            ttk.dialogs.Messagebox.show_info(
                "Bu doktora bağlı hasta bulunmamaktadır.",
                "Bilgi"
            )
    
    # ------------------------------------------------------------
    def _filter_patients(self, *args):
        """Arama kutusuna göre hasta listesini filtreler."""
        search_term = self.search_var.get().lower().strip()
        
        # Tüm hastaları getir
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.tc_no, u.full_name
                FROM patients p
                JOIN users u ON p.id = u.id
                WHERE p.doctor_id = %s
                """,
                (self.doctor_id,)
            )
            all_patients = cur.fetchall()
        
        # Tabloyu temizle
        self.tree.delete(*self.tree.get_children())
        
        # Filtreleme yap
        filtered_patients = []
        for patient in all_patients:
            if (search_term in patient["full_name"].lower() or 
                search_term in patient["tc_no"].lower()):
                filtered_patients.append(patient)
                self.tree.insert(
                    "", tk.END,
                    iid=patient["id"],
                    values=(patient["tc_no"], patient["full_name"])
                )
        
        # Hasta sayısını güncelle
        count = len(filtered_patients)
        if search_term:
            self.patient_count_lbl.config(
                text=f"'{search_term}' için {count} hasta bulundu.",
                bootstyle="info" if count > 0 else "warning"
            )
        else:
            self.patient_count_lbl.config(
                text=f"Toplam {count} hasta bulundu.",
                bootstyle="info" if count > 0 else "warning"
            )

    # ------------------------------------------------------------
    def _open_patient(self, event=None):
        """Seçili hastayı Hasta Paneli olarak aç."""
        sel = self.tree.selection()
        if not sel:
            ttk.dialogs.Messagebox.show_warning(
                "Lütfen bir hasta seçin.",
                "Uyarı"
            )
            return
        patient_id = int(sel[0])          # item id = hasta id
        PatientWindow(self, patient_id)
    
    # ------------------------------------------------------------
    def _update_selection_label(self, event=None):
        """Seçili hasta etiketini günceller."""
        sel = self.tree.selection()
        if sel:
            patient_name = self.tree.item(sel[0], "values")[1]
            self.selected_lbl.config(
                text=f"Seçili hasta: {patient_name}",
                bootstyle="primary"
            )
        else:
            self.selected_lbl.config(
                text="Seçili hasta: Yok",
                bootstyle="secondary"
            )

    # ------------------------------------------------------------
    def _show_status(self):
        """Seçili hastanın diyet / egzersiz geçmişini gösterir."""
        sel = self.tree.selection()
        if not sel:
            ttk.dialogs.Messagebox.show_warning(
                "Lütfen bir hasta seçin.",
                "Uyarı"
            )
            return
        patient_id = int(sel[0])
        full_name  = self.tree.item(sel[0], "values")[1]
        StatusWindow(self, patient_id, full_name)
