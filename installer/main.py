import os
import sys
import subprocess
import shutil
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import requests
import zipfile
import io
import webbrowser

GITHUB_REPO = "https://github.com/ilylbgg/cdi-logger/archive/refs/heads/main.zip"
INSTALL_DIR = os.path.expanduser(r"~/Documents/IlyLogiciels/cdiGraph/app")
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
SHORTCUT_PATH = os.path.join(DESKTOP, "CDIGraph.lnk")
MAIN_PY_PATH = os.path.join(INSTALL_DIR, "main.py")
REQ_PATH = os.path.join(INSTALL_DIR, "requirements.txt")
PYTHON_URL = "https://www.python.org/downloads/"

def python_installed():
    # Try the current interpreter first
    try:
        subprocess.check_output([sys.executable, "--version"], stderr=subprocess.STDOUT)
        return True
    except Exception:
        pass

    # Fall back to common commands on PATH (python, py)
    for cmd in ("python", "py"):
        path = shutil.which(cmd)
        if not path:
            continue
        try:
            subprocess.check_output([cmd, "--version"], stderr=subprocess.STDOUT)
            return True
        except Exception:
            continue

    return False

def download_and_extract():
    try:
        resp = requests.get(GITHUB_REPO, verify=False)
        resp.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        names = z.namelist()

        # Find the path inside the zip that corresponds to the 'app/' folder.
        app_folder = None
        for name in names:
            if '/app/' in name:
                # keep the prefix up to and including 'app/'
                app_folder = name.split('/app/')[0] + '/app/'
                break
            if name.endswith('app/'):
                app_folder = name
                break

        if not app_folder:
            raise Exception("Dossier 'app' introuvable dans le dépôt")

        # Remove existing install dir then recreate it
        if os.path.exists(INSTALL_DIR):
            shutil.rmtree(INSTALL_DIR)

        os.makedirs(INSTALL_DIR, exist_ok=True)

        # Extract only files under the discovered app_folder, protecting against zip-slip
        for name in names:
            if not name.startswith(app_folder):
                continue
            rel = name[len(app_folder):]
            if not rel:
                continue

            # Normalize destination path and ensure it stays inside INSTALL_DIR
            dest = os.path.normpath(os.path.join(INSTALL_DIR, rel))
            if not dest.startswith(os.path.normpath(INSTALL_DIR)):
                # suspicious path, skip
                continue

            if name.endswith('/'):
                os.makedirs(dest, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with z.open(name) as src, open(dest, 'wb') as dst:
                    dst.write(src.read())
    except Exception as e:
        raise Exception(f"Erreur lors du téléchargement ou de l'extraction : {str(e)}")

def install_requirements():
    if os.path.exists(REQ_PATH):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", REQ_PATH])

def create_shortcut():
    try:
        ps_script = f'''
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("{SHORTCUT_PATH}")
        $Shortcut.TargetPath = "{sys.executable}"
        $Shortcut.Arguments = "{MAIN_PY_PATH}"
        $Shortcut.IconLocation = "{MAIN_PY_PATH},0"
        $Shortcut.Save()
        '''
        subprocess.run(["powershell", "-Command", ps_script], check=True)
    except Exception as e:
        raise Exception(f"Erreur lors de la création du raccourci : {str(e)}")

def run_install(progress_callback):
    try:
        progress_callback("Vérification de Python...")
        if not python_installed():
            response = messagebox.askyesno(
                "Python requis",
                "Python n'est pas installé. Souhaitez-vous être redirigé vers le site officiel pour l'installer ?"
            )
            if response:
                webbrowser.open(PYTHON_URL)
            return False, "Python n'est pas installé. Veuillez l'installer avant de continuer."

        progress_callback("Téléchargement du code source...")
        download_and_extract()

        progress_callback("Installation des dépendances...")
        install_requirements()

        progress_callback("Création du raccourci sur le bureau...")
        create_shortcut()

        progress_callback("Installation terminée !")
        return True, "Installation réussie ! Vous pouvez maintenant lancer CDIGraph depuis le raccourci sur votre bureau."
    except Exception as e:
        return False, f"Erreur lors de l'installation : {str(e)}"

class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Installateur CDIGraph")
        self.geometry("450x300")
        self.resizable(False, False)
        self.configure(bg="#232946")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#232946", foreground="#eebbc3", font=("Segoe UI", 12))
        self.style.configure("TButton", background="#eebbc3", foreground="#232946", font=("Segoe UI", 12, "bold"))
        self.style.configure("TProgressbar", background="#eebbc3", troughcolor="#232946")

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(
            self,
            text="Installateur CDIGraph",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=20)

        self.progress = ttk.Progressbar(self, length=350, mode="determinate")
        self.progress.pack(pady=10)

        self.status = ttk.Label(self, text="Prêt à installer.")
        self.status.pack(pady=10)

        self.install_btn = ttk.Button(self, text="Installer", command=self.start_install)
        self.install_btn.pack(pady=20)

    def update_status(self, msg):
        self.status.config(text=msg)
        self.update_idletasks()

    def start_install(self):
        self.install_btn.config(state="disabled")
        self.progress["value"] = 0

        def task():
            steps = [
                "Vérification de Python...",
                "Téléchargement du code source...",
                "Installation des dépendances...",
                "Création du raccourci sur le bureau...",
                "Installation terminée !"
            ]

            def progress_callback(msg):
                idx = steps.index(msg) if msg in steps else len(steps)-1
                self.progress["value"] = (idx+1)*100//len(steps)
                self.update_status(msg)

            ok, msg = run_install(progress_callback)
            self.progress["value"] = 100
            self.update_status(msg)

            if ok:
                messagebox.showinfo("Succès", msg)
            else:
                messagebox.showerror("Erreur", msg)

            self.install_btn.config(state="normal")

        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    InstallerApp().mainloop()
