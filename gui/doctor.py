# gui/doctor.py
import tkinter as tk
import ttkbootstrap as ttk
from utils.db import db_cursor
from gui.add_patient import AddPatientWindow
from gui.patient import PatientWindow  # Hasta paneli
from gui.status import StatusWindow  # Günlük diyet/egzersiz
from gui.email_settings import EmailSettingsDialog  # E-posta ayarları
from gui.add_symptom import AddSymptomDialog    #  <<<  EKLEYİN



class DoctorWindow(tk.Toplevel):
    """Doktorun hasta listesini görüntülediği ve yönetebildiği pencere."""

    def __init__(self, master, doctor_id: int):
        super().__init__(master)
        self.title("💊 Doktor Paneli")
        self.geometry("1200x800")
        self.configure(bg="#2b3e50")

        # Pencere merkezde açılsın
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        self.doctor_id = doctor_id
        self.master_window = master

        # Doktor bilgisini getir
        with db_cursor() as cur:
            cur.execute("SELECT full_name FROM users WHERE id=%s", (doctor_id,))
            user_data = cur.fetchone()
            self.doctor_name = user_data["full_name"] if user_data else "Doktor"

        # Navigation state
        self.current_view = "main"

        self._create_main_view()

    def _create_main_view(self):
        """Ana doktor paneli görünümü."""
        # Tüm widget'ları temizle
        for widget in self.winfo_children():
            widget.destroy()

        self.current_view = "main"

        # Ana container
        main_container = ttk.Frame(self, padding=20)
        main_container.pack(fill="both", expand=True)

        # Header
        self._create_header(main_container)

        # Patient list and controls
        self._create_patient_section(main_container)

        # Action buttons
        self._create_action_buttons(main_container)

        # Footer
        self._create_footer(main_container)

        self._refresh()

    def _create_header(self, parent):
        """Header bölümü."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill="x", pady=(0, 20))

        # Title with modern styling
        title_label = ttk.Label(
            header_frame,
            text=f"👨‍⚕️ Doktor Paneli - Dr. {self.doctor_name}",
            font=("Segoe UI", 20, "bold"),
            bootstyle="primary"
        )
        title_label.pack()

        # Subtitle
        subtitle_label = ttk.Label(
            header_frame,
            text="Hasta yönetimi ve takip sistemi",
            font=("Segoe UI", 12),
            bootstyle="secondary"
        )
        subtitle_label.pack(pady=(5, 0))

    def _create_patient_section(self, parent):
        """Hasta listesi bölümü."""
        # Patient section frame
        patient_frame = ttk.LabelFrame(
            parent,
            text="👥 Hasta Listesi",
            padding=20,
            bootstyle="info"
        )
        patient_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Search section
        search_frame = ttk.Frame(patient_frame)
        search_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            search_frame,
            text="🔍 Hasta Ara:",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=(0, 10))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_frame,
            width=30,
            font=("Segoe UI", 11),
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Button(
            search_frame,
            text="🔍 Ara",
            bootstyle="info-outline",
            command=self._filter_patients,
            width=12
        ).pack(side="right")

        # Patient count info
        self.patient_count_lbl = ttk.Label(
            patient_frame,
            text="",
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        self.patient_count_lbl.pack(anchor="w", pady=(0, 10))

        # Treeview frame
        tree_frame = ttk.Frame(patient_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Treeview with modern styling
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("tc", "name"),
            show="headings",
            height=12,
            bootstyle="info"
        )
        self.tree.heading("tc", text="📋 TC No")
        self.tree.heading("name", text="👤 Hasta Adı")
        self.tree.column("tc", width=200, minwidth=150, anchor="center")
        self.tree.column("name", width=400, minwidth=300, anchor="w")

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._open_patient)
        self.tree.bind("<<TreeviewSelect>>", self._update_selection_label)

        # Selected patient info
        self.selected_lbl = ttk.Label(
            patient_frame,
            text="Seçili hasta: Yok",
            font=("Segoe UI", 11, "bold"),
            bootstyle="secondary"
        )
        self.selected_lbl.pack(anchor="w")

    def _create_action_buttons(self, parent):
        """Action-buttons bölümü (doktor paneli)."""
        action_frame = ttk.LabelFrame(
            parent, text="⚡ Hızlı İşlemler",
            padding=15, bootstyle="success"
        )
        action_frame.pack(fill="x", pady=(0, 20))

        # ——— her satır 3 sütun genişler ———#
        action_frame.columnconfigure((0, 1, 2), weight=1)

        # ───────────── 1. SATIR ───────────── #
        row1 = ttk.Frame(action_frame)
        row1.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        row1.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(
            row1, text="➕ Yeni Hasta Ekle",
            bootstyle="success",
            command=self._show_add_patient,
            width=20
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ttk.Button(
            row1, text="👤 Hasta Paneli",
            bootstyle="primary",
            command=self._open_patient,
            width=20
        ).grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Button(
            row1, text="📊 Günlük Durum",
            bootstyle="warning",
            command=self._show_status,
            width=20
        ).grid(row=0, column=2, padx=(5, 0), sticky="ew")

        # ───────────── 2. SATIR ───────────── #
        row2 = ttk.Frame(action_frame)
        row2.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        row2.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(
            row2, text="🩺 Belirti Ekle",
            bootstyle="warning",  # ← isteğe göre ‘warning’/‘info’
            command=self._add_symptom,
            width=20
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ttk.Button(
            row2, text="📈 Glukoz Geçmişi",
            bootstyle="secondary",
            command=self._show_history,
            width=20
        ).grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Button(
            row2, text="🔬 Analiz",
            bootstyle="info",
            command=self._show_analysis,
            width=20
        ).grid(row=0, column=2, padx=(5, 0), sticky="ew")

        # ───────────── 3. SATIR ───────────── #
        row3 = ttk.Frame(action_frame)
        row3.grid(row=2, column=0, columnspan=3, sticky="ew")
        row3.columnconfigure((0, 1), weight=1)

        ttk.Button(
            row3, text="📧 E-posta Ayarları",
            bootstyle="warning-outline",
            command=self._open_email_settings,
            width=20
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ttk.Button(
            row3, text="🔄 Yenile",
            bootstyle="secondary-outline",
            command=self._refresh,
            width=20
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _create_footer(self, parent):
        """Footer bölümü."""
        footer_frame = ttk.Frame(parent)
        footer_frame.pack(fill="x")

        ttk.Label(
            footer_frame,
            text="© 2025 Diyabet Takip Sistemi - Doktor Arayüzü",
            font=("Segoe UI", 9),
            bootstyle="secondary"
        ).pack(side="left")

        ttk.Button(
            footer_frame,
            text="❌ Kapat",
            bootstyle="danger-outline",
            width=15,
            command=self.destroy
        ).pack(side="right")

    def _show_add_patient(self):
        """Navigate to add patient page."""
        self.current_view = "add_patient"
        AddPatientWindow(
            self,
            self.doctor_id,
            self._refresh,
            self._create_main_view
        )

    def _msg(self, kind: str, message: str, title: str):
        import tkinter.messagebox as mbox
        if kind == 'info':
            mbox.showinfo(title, message, parent=self)
        elif kind == 'warning':
            mbox.showwarning(title, message, parent=self)
        else:
            mbox.showerror(title, message, parent=self)

    def _refresh(self):
        """Hasta listesini yeniler."""
        if self.current_view != "main":
            return

        self.tree.delete(*self.tree.get_children())

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.tc_no, u.full_name
                FROM patients p
                JOIN users    u ON p.id = u.id
                WHERE p.doctor_id = %s AND u.role='patient' AND u.id <> %s
                ORDER BY u.full_name
                """,
                (self.doctor_id, self.doctor_id)
            )
            rows = cur.fetchall()

        for row in rows:
            self.tree.insert(
                "", tk.END,
                iid=row["id"],
                values=(row["tc_no"], row["full_name"])
            )

        # Update patient count
        patient_count = len(rows)
        if patient_count > 0:
            self.patient_count_lbl.config(
                text=f"📊 Toplam {patient_count} hasta bulundu.",
                bootstyle="info"
            )
        else:
            self.patient_count_lbl.config(
                text="⚠️ Bu doktora bağlı hasta yok.",
                bootstyle="warning"
            )

    def _filter_patients(self, *args):
        """Arama kutusuna göre hasta listesini filtreler."""
        search_term = self.search_var.get().lower().strip()

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT u.id, u.tc_no, u.full_name
                FROM patients p
                JOIN users u ON p.id = u.id
                WHERE p.doctor_id = %s AND u.role='patient' AND u.id <> %s
                """,
                (self.doctor_id, self.doctor_id)
            )
            all_patients = cur.fetchall()

        self.tree.delete(*self.tree.get_children())

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

        count = len(filtered_patients)
        if search_term:
            self.patient_count_lbl.config(
                text=f"🔍 '{search_term}' için {count} hasta bulundu.",
                bootstyle="info" if count > 0 else "warning"
            )
        else:
            self.patient_count_lbl.config(
                text=f"📊 Toplam {count} hasta bulundu.",
                bootstyle="info" if count > 0 else "warning"
            )

    def _open_patient(self, event=None):
        """Seçili hastayı Hasta Paneli olarak aç."""
        sel = self.tree.selection()
        if not sel:
            self._msg('warning', "Lütfen bir hasta seçin.", "Uyarı")
            return
        patient_id = int(sel[0])
        PatientWindow(self, patient_id, skip_password_change=True)

    def _update_selection_label(self, event=None):
        """Seçili hasta etiketini günceller."""
        sel = self.tree.selection()
        if sel:
            patient_name = self.tree.item(sel[0], "values")[1]
            self.selected_lbl.config(
                text=f"✅ Seçili hasta: {patient_name}",
                bootstyle="primary"
            )
        else:
            self.selected_lbl.config(
                text="⭕ Seçili hasta: Yok",
                bootstyle="secondary"
            )

    def _show_status(self):
        """Seçili hastanın diyet / egzersiz geçmişini gösterir."""
        sel = self.tree.selection()
        if not sel:
            self._msg('warning', "Lütfen bir hasta seçin.", "Uyarı")
            return
        patient_id = int(sel[0])
        full_name = self.tree.item(sel[0], "values")[1]
        StatusWindow(self, patient_id, full_name)

    def _open_email_settings(self):
        """E-posta ayarları penceresini açar."""
        EmailSettingsDialog(self)

    def _show_history(self):
        sel = self.tree.selection()
        if not sel:
            self._msg('warning', "Lütfen bir hasta seçin.", "Uyarı")
            return
        patient_id = int(sel[0])
        full_name = self.tree.item(sel[0], "values")[1]
        from gui.glucose_history import GlucoseHistoryWindow
        GlucoseHistoryWindow(self, patient_id, full_name)

    def _show_analysis(self):
        sel = self.tree.selection()
        if not sel:
            self._msg('warning', "Lütfen bir hasta seçin.", "Uyarı")
            return
        patient_id = int(sel[0])
        full_name = self.tree.item(sel[0], "values")[1]
        from gui.analysis import AnalysisWindow
        AnalysisWindow(self, patient_id, full_name)

    def _add_symptom(self):
        """Seçilen hasta için çoklu ‘Belirti Ekle’ diyalogunu açar."""
        sel = self.tree.selection()
        if not sel:
            self._msg('warning', "Lütfen bir hasta seçin.", "Uyarı")
            return

        patient_id   = int(sel[0])
        patient_name = self.tree.item(sel[0], "values")[1]

        def _on_added():
            self._msg('info', f"{patient_name} hastası için belirtiler kaydedildi.", "Bilgi")
            self._refresh()  # <- opsiyonel: paneli yenile

        AddSymptomDialog(self, patient_id, on_added=_on_added)
