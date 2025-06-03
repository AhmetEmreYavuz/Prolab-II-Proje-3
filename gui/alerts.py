import tkinter as tk
import ttkbootstrap as ttk
from utils.db import db_cursor


ALERT_MAP: dict[str, tuple[str, str, str]] = {
    "hypo": (
        "Hipoglisemi Riski",
        "Acil Uyarı",
        "Hastanın kan şekeri seviyesi 70 mg/dL’nin altına düştü. "
        "Hipoglisemi riski! Hızlı müdahale gerekebilir."
    ),
    "normal": (
        "Normal Seviye",
        "Uyarı Yok",
        "Kan şekeri seviyesi normal aralıkta. Hiçbir işlem gerekmez."
    ),
    "mid_high": (
        "Orta Yüksek Seviye",
        "Takip Uyarısı",
        "Hastanın kan şekeri 111–150 mg/dL arasında. Durum izlenmeli."
    ),
    "high": (
        "Yüksek Seviye",
        "İzleme Uyarısı",
        "Hastanın kan şekeri 151–200 mg/dL arasında. Diyabet kontrolü gereklidir."
    ),
    "very_high": (
        "Çok Yüksek Seviye (Hiperglisemi)",
        "Acil Müdahale Uyarısı",
        "Hastanın kan şekeri 200 mg/dL’nin üzerinde. Hiperglisemi durumu. "
        "Acil müdahale gerekebilir."
    ),
    "missing_all": (
        "Ölçüm Eksikliği (Hiç Giriş Yok)",
        "Ölçüm Eksik Uyarısı",
        "Hasta gün boyunca kan şekeri ölçümü yapmamıştır. Acil takip önerilir."
    ),
    "missing_few": (
        "Ölçüm Eksikliği (3’ten Az Giriş)",
        "Ölçüm Yetersiz Uyarısı",
        "Hastanın günlük kan şekeri ölçüm sayısı yetersiz (<3). Durum izlenmelidir."
    ),
    "info": (
        "Bilgilendirme",
        "Bilgi",
        ""  # Burası boş, çünkü DB’den gelen message zaten gösterilecek.
    ),
}

class AlertsWindow(tk.Toplevel):

    def __init__(self, master, doctor_id: int):
        super().__init__(master)
        self.title("🔔 Hasta Uyarıları")
        self.geometry("1100x400")
        self.configure(bg="#2b3e50")

        tree = ttk.Treeview(
            self, columns=("day","patient","status","type","msg"),
            show="headings", bootstyle="info"
        )
        for col, text, w in [
            ("day",     "Tarih",          90),
            ("patient", "Hasta",         200),
            ("status",  "Durum",         210),
            ("type",    "Uyarı Tipi",    150),
            ("msg",     "Mesaj",         430),
        ]:
            tree.heading(col, text=text)
            tree.column(col, width=w, anchor="w")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        self._fill(tree, doctor_id)

    def _fill(self, tree: ttk.Treeview, doc_id: int):
        with db_cursor() as cur:
            cur.execute(
                """
                SELECT a.day,
                       u.full_name   AS patient,
                       a.alert_type  AS code,
                       a.message
                  FROM alerts a
                  JOIN patients p   ON p.id = a.patient_id
                  JOIN users    u   ON u.id = p.id
                 WHERE p.doctor_id = %s
                 ORDER BY a.created_dt DESC
                """,
                (doc_id,)
            )
            rows = cur.fetchall()

        for r in rows:

            status, nice_type, default_msg = ALERT_MAP.get(
                r["code"], ("Bilinmeyen", r["code"], "")
            )
            msg = r["message"] or default_msg
            date_str = r["day"].strftime("%d.%m.%Y") if r["day"] else "-"
            tree.insert(
                "", "end",
                values=(date_str, r["patient"], status, nice_type, msg)
            )
