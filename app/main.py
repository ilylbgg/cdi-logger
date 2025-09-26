import tkinter as tk
from tkinter import messagebox
from src.database import init_db, authenticate, add_attendance
from src.statistics import stats_today, average_per_hour, peak_hours, repartition_par_classe
from src.utils import round_hour, today_str
from datetime import datetime
import configparser
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

BG_COLOR = "#f5f6fa"
FG_COLOR = "#273c75"
BTN_COLOR = "#40739e"
BTN_FG = "#fff"
FONT = ("Segoe UI", 12)
TITLE_FONT = ("Segoe UI", 16, "bold")

# Read theme from settings.cfg
config = configparser.ConfigParser()
config.read('./app/settings.cfg', encoding='utf-8')
theme = config.get('UI', 'Theme', fallback='light').lower()
if theme == "dark":
    matplotlib.style.use('dark_background')
else:
    matplotlib.style.use('default')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CDI Logger")
        self.geometry("400x350")
        self.configure(bg=BG_COLOR)
        init_db()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.show_login()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def center_frame(self):
        frame = tk.Frame(self, bg=BG_COLOR)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        return frame

    def styled_label(self, parent, text, font=FONT, pady=5):
        return tk.Label(parent, text=text, font=font, bg=BG_COLOR, fg=FG_COLOR, pady=pady)

    def styled_button(self, parent, text, command, width=20, pady=5):
        return tk.Button(parent, text=text, command=command, width=width, bg=BTN_COLOR, fg=BTN_FG, font=FONT, relief="flat", pady=pady, activebackground="#487eb0", activeforeground="#fff")

    def show_login(self):
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Connexion", TITLE_FONT, pady=10).pack()
        self.styled_label(frame, "Nom d'utilisateur:").pack()
        username_entry = tk.Entry(frame, textvariable=self.username_var, font=FONT, justify="center")
        username_entry.pack(pady=2)
        self.styled_label(frame, "Mot de passe:").pack()
        password_entry = tk.Entry(frame, textvariable=self.password_var, show="*", font=FONT, justify="center")
        password_entry.pack(pady=2)
        self.styled_button(frame, "Se connecter", self.login_action, width=20, pady=10).pack()
        self.bind('<Return>', lambda event: self.login_action())

    def login_action(self):
        username = self.username_var.get()
        password = self.password_var.get()
        if authenticate(username, password):
            self.username_var.set("")
            self.password_var.set("")
            self.show_menu()
        else:
            messagebox.showerror("Erreur", "Nom d'utilisateur ou mot de passe incorrect.")

    def show_menu(self):
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Menu principal", TITLE_FONT, pady=10).pack()
        self.styled_button(frame, "Nouvelle Heure", self.show_new_entry).pack(pady=5)
        self.styled_button(frame, "Statistiques", self.show_statistics).pack(pady=5)
        self.styled_button(frame, "Déconnexion", self.logout).pack(pady=5)

    def show_new_entry(self):
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Nouvelle Entrée", TITLE_FONT, pady=10).pack()
        # Choix de l'heure
        hours = [f"{h:02d}:00" for h in range(8, 18)]
        self.heure_var = tk.StringVar(value=hours[0])
        hour_frame = tk.Frame(frame, bg=BG_COLOR)
        hour_frame.pack(pady=2)
        self.styled_label(hour_frame, "Heure :", pady=0).pack(side=tk.LEFT)
        tk.OptionMenu(hour_frame, self.heure_var, *hours).pack(side=tk.LEFT, padx=5)
        # Champs pour les classes
        self.sixieme_var = tk.IntVar()
        self.cinquieme_var = tk.IntVar()
        self.quatrieme_var = tk.IntVar()
        self.troisieme_var = tk.IntVar()
        for label, var in [("6ème", self.sixieme_var), ("5ème", self.cinquieme_var),
                           ("4ème", self.quatrieme_var), ("3ème", self.troisieme_var)]:
            subframe = tk.Frame(frame, bg=BG_COLOR)
            subframe.pack(pady=2)
            self.styled_label(subframe, f"Nombre d'élèves {label}:", pady=0).pack(side=tk.LEFT)
            tk.Entry(subframe, textvariable=var, width=5, font=FONT, justify="center").pack(side=tk.LEFT, padx=5)
        self.styled_button(frame, "Enregistrer", self.save_entry).pack(pady=10)
        self.styled_button(frame, "Retour", self.show_menu).pack()

    def save_entry(self):
        try:
            heure = self.heure_var.get()
            sixieme = self.sixieme_var.get()
            cinquieme = self.cinquieme_var.get()
            quatrieme = self.quatrieme_var.get()
            troisieme = self.troisieme_var.get()
            total = sixieme + cinquieme + quatrieme + troisieme
            date = today_str()
            add_attendance(heure, sixieme, cinquieme, quatrieme, troisieme, total, date)
            messagebox.showinfo("Succès", "Entrée enregistrée.")
            self.show_menu()
        except Exception as e:
            messagebox.showerror("Erreur", f"Entrée invalide: {e}")

    def show_statistics(self):
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Statistiques", TITLE_FONT, pady=10).pack()
        total_today = stats_today()
        avg_per_hour = average_per_hour()
        peaks = peak_hours()
        repartition = repartition_par_classe()
        self.styled_label(frame, f"Total élèves aujourd'hui: {total_today}").pack()
        self.styled_label(frame, "Moyenne par heure:").pack()
        for h, avg in avg_per_hour.items():
            self.styled_label(frame, f"{h}: {avg:.2f}").pack()
        self.styled_label(frame, f"Heures de pointe: {', '.join(peaks) if peaks else 'Aucune'}").pack()
        self.styled_label(frame, "Répartition par classe:").pack()
        for classe, nb in repartition.items():
            self.styled_label(frame, f"{classe}: {nb}").pack()

        # --- Graphique 1 : Nombre d'élèves par heure ---
        fig1 = plt.Figure(figsize=(3.5, 2), dpi=80)
        ax1 = fig1.add_subplot(111)
        heures = list(avg_per_hour.keys())
        moyennes = list(avg_per_hour.values())
        ax1.bar(heures, moyennes, color="#487eb0")
        ax1.set_title("Moyenne d'élèves par heure")
        ax1.set_xlabel("Heure")
        ax1.set_ylabel("Moyenne")
        fig1.tight_layout()
        canvas1 = FigureCanvasTkAgg(fig1, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(pady=5)

        # --- Graphique 2 : Nombre d'élèves par classe ---
        fig2 = plt.Figure(figsize=(3.5, 2), dpi=80)
        ax2 = fig2.add_subplot(111)
        classes = list(repartition.keys())
        effectifs = list(repartition.values())
        ax2.bar(classes, effectifs, color="#44bd32")
        ax2.set_title("Répartition par classe")
        ax2.set_xlabel("Classe")
        ax2.set_ylabel("Total")
        fig2.tight_layout()
        canvas2 = FigureCanvasTkAgg(fig2, master=frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(pady=5)

        self.styled_button(frame, "Retour", self.show_menu).pack(pady=10)

    def logout(self):
        self.show_login()

if __name__ == "__main__":
    app = App()
    app.mainloop()
