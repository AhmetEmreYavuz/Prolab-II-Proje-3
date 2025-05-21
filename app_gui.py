# app_gui.py
import tkinter as tk
from gui.login import LoginDialog
from gui.patient import PatientWindow
from gui.doctor import DoctorWindow


def main():
    root = tk.Tk()
    root.withdraw()          # ana pencere gizli

    dlg = LoginDialog(root)
    root.wait_window(dlg)

    if not dlg.result:
        return           # giriş başarısız veya iptal

    uid, role = dlg.result["user_id"], dlg.result["role"]

    if role == "patient":
        PatientWindow(root, uid)
    elif role == "doctor":
        DoctorWindow(root, uid)

    root.mainloop()


if __name__ == "__main__":
    main()
