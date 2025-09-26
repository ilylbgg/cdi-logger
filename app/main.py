import configparser
from datetime import datetime
import os
import tkinter as tk
from tkinter import messagebox

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from src.database import add_attendance, authenticate, init_db
from src.statistics import (
    average_per_hour,
    average_per_hour_week,
    peak_hours,
    repartition_par_classe,
    stats_semaine,
    stats_today,
)
from src.utils import round_hour, today_str

# Lecture du thème depuis settings.cfg
config = configparser.ConfigParser()
script_dir = os.path.dirname(os.path.abspath(__file__))
print(__file__)
config_path = os.path.join(script_dir, 'config.cfg')  
config.read(config_path, encoding='utf-8')
theme = config.get('UI', 'Theme', fallback='light').lower()

# Couleurs dynamiques
BG_COLOR = "#222934" if theme == "dark" else "#f5f6fa"
FG_COLOR = "#f5f6fa" if theme == "dark" else "#273c75"
BTN_COLOR = "#40739e" if theme == "light" else "#444c5e"
BTN_FG = "#fff"
FONT = ("Segoe UI", 13)
TITLE_FONT = ("Segoe UI", 18, "bold")

# Style matplotlib
matplotlib.style.use('dark_background' if theme == "dark" else 'default')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        Base = config.get('General', 'Base', fallback='ERREUR')
        CDI_Name = config.get("General","CDI_Name",fallback='AUCUN NOM')
        self.title(f"CDIStats - Base : {Base} | {CDI_Name}")
        self.geometry("800x600")
        self.configure(bg=BG_COLOR)
        self.theme_var = tk.StringVar(value=theme)
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
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            bg=BTN_COLOR,
            fg=BTN_FG,
            font=FONT,
            relief="flat",
            pady=pady,
            padx=10,
            bd=0,
            highlightthickness=0,
            activebackground="#487eb0",
            activeforeground="#fff",
            highlightbackground=BG_COLOR
        )

    def update_theme(self):
        global BG_COLOR, FG_COLOR, BTN_COLOR, theme
        theme = self.theme_var.get()
        config.set('UI', 'Theme', theme)
        with open('./app/settings.cfg', 'w', encoding='utf-8') as f:
            config.write(f)
        BG_COLOR = "#222934" if theme == "dark" else "#f5f6fa"
        FG_COLOR = "#f5f6fa" if theme == "dark" else "#273c75"
        BTN_COLOR = "#40739e" if theme == "light" else "#444c5e"
        matplotlib.style.use('dark_background' if theme == "dark" else 'default')
        self.configure(bg=BG_COLOR)
        self.show_menu()

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
        self.styled_label(frame, "Menu principal", TITLE_FONT, pady=18).pack()
        self.styled_button(frame, "Nouvelle Heure", self.show_new_entry).pack(pady=10)
        self.styled_button(frame, "Statistiques", self.show_statistics).pack(pady=10)
        self.styled_button(frame, "Paramètres", self.show_settings).pack(pady=10)
        self.styled_button(frame, "Déconnexion", self.logout).pack(pady=10)

    def show_new_entry(self):
        self.clear_window()
        self.entry_data = {}
        self.show_entry_jour_heure()

    def show_entry_jour_heure(self):
        frame = self.center_frame()
        self.styled_label(frame, "Nouvelle Entrée - Jour & Heure", TITLE_FONT, pady=10).pack()
        hours = [f"{h:02d}:00" for h in range(8, 18) if h not in (12, 17)]
        self.heure_var = tk.StringVar(value=hours[0])
        hour_frame = tk.Frame(frame, bg=BG_COLOR)
        hour_frame.pack(pady=2)
        self.styled_label(hour_frame, "Heure :", pady=0).pack(side=tk.LEFT)
        tk.OptionMenu(hour_frame, self.heure_var, *hours).pack(side=tk.LEFT, padx=5)
        self.styled_button(frame, "Suivant", self.show_entry_3e).pack(pady=10)
        self.styled_button(frame, "Retour", self.show_menu).pack()

    def show_entry_3e(self):
        self.entry_data['heure'] = self.heure_var.get()
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Entrée - Nombre 3°", TITLE_FONT, pady=10).pack()
        self.troisieme_var = tk.IntVar()
        subframe = tk.Frame(frame, bg=BG_COLOR)
        subframe.pack(pady=2)
        self.styled_label(subframe, "Nombre d'élèves 3° :", pady=0).pack(side=tk.LEFT)
        tk.Entry(subframe, textvariable=self.troisieme_var, width=5, font=FONT, justify="center").pack(side=tk.LEFT, padx=5)
        self.styled_button(frame, "Suivant", self.show_entry_4e).pack(pady=10)
        self.styled_button(frame, "Retour", self.show_entry_jour_heure).pack()

    def show_entry_4e(self):
        self.entry_data['troisieme'] = self.troisieme_var.get()
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Entrée - Nombre 4°", TITLE_FONT, pady=10).pack()
        self.quatrieme_var = tk.IntVar()
        subframe = tk.Frame(frame, bg=BG_COLOR)
        subframe.pack(pady=2)
        self.styled_label(subframe, "Nombre d'élèves 4° :", pady=0).pack(side=tk.LEFT)
        tk.Entry(subframe, textvariable=self.quatrieme_var, width=5, font=FONT, justify="center").pack(side=tk.LEFT, padx=5)
        self.styled_button(frame, "Suivant", self.show_entry_5e).pack(pady=10)
        self.styled_button(frame, "Retour", self.show_entry_3e).pack()

    def show_entry_5e(self):
        self.entry_data['quatrieme'] = self.quatrieme_var.get()
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Entrée - Nombre 5°", TITLE_FONT, pady=10).pack()
        self.cinquieme_var = tk.IntVar()
        subframe = tk.Frame(frame, bg=BG_COLOR)
        subframe.pack(pady=2)
        self.styled_label(subframe, "Nombre d'élèves 5° :", pady=0).pack(side=tk.LEFT)
        tk.Entry(subframe, textvariable=self.cinquieme_var, width=5, font=FONT, justify="center").pack(side=tk.LEFT, padx=5)
        self.styled_button(frame, "Suivant", self.show_entry_6e).pack(pady=10)
        self.styled_button(frame, "Retour", self.show_entry_4e).pack()

    def show_entry_6e(self):
        self.entry_data['cinquieme'] = self.cinquieme_var.get()
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Entrée - Nombre 6°", TITLE_FONT, pady=10).pack()
        self.sixieme_var = tk.IntVar()
        subframe = tk.Frame(frame, bg=BG_COLOR)
        subframe.pack(pady=2)
        self.styled_label(subframe, "Nombre d'élèves 6° :", pady=0).pack(side=tk.LEFT)
        tk.Entry(subframe, textvariable=self.sixieme_var, width=5, font=FONT, justify="center").pack(side=tk.LEFT, padx=5)
        self.styled_button(frame, "Enregistrer", self.save_entry_multi).pack(pady=10)
        self.styled_button(frame, "Retour", self.show_entry_5e).pack()

    def save_entry_multi(self):
        try:
            self.entry_data['sixieme'] = self.sixieme_var.get()
            heure = self.entry_data['heure']
            sixieme = self.entry_data['sixieme']
            cinquieme = self.entry_data['cinquieme']
            quatrieme = self.entry_data['quatrieme']
            troisieme = self.entry_data['troisieme']
            total = sixieme + cinquieme + quatrieme + troisieme
            date = today_str()
            add_attendance(heure, sixieme, cinquieme, quatrieme, troisieme, total, date)
            messagebox.showinfo("Succès", "Entrée enregistrée.")
            self.show_menu()
        except Exception as e:
            messagebox.showerror("Erreur", f"Entrée invalide: {e}")

    def show_statistics(self, mode="semaine"):
        self.clear_window()
        frame = tk.Frame(self, bg=BG_COLOR)
        frame.place(relx=0.5, rely=0.1, anchor="n", relwidth=0.95, relheight=0.85)

        btn_frame = tk.Frame(frame, bg=BG_COLOR)
        btn_frame.pack(pady=10)
        for label, m in [("Semaine", "semaine"), ("Jour", "jour"), ("Mois", "mois")]:
            self.styled_button(
                btn_frame, label,
                lambda m=m: self.show_statistics(m),
                width=12, pady=2
            ).pack(side=tk.LEFT, padx=5)

        stat_frame = tk.Frame(frame, bg=BG_COLOR)
        stat_frame.pack(fill="both", expand=True)

        if mode == "semaine":
            self.display_week_stats(stat_frame)
        elif mode == "jour":
            self.display_day_stats(stat_frame)
        elif mode == "mois":
            self.styled_label(stat_frame, "Statistiques mensuelles (en développement)", FONT).pack()

        self.styled_button(frame, "Retour", self.show_menu).pack(pady=10)

    def display_week_stats(self, parent):
        total = stats_semaine()
        avg_per_hour = average_per_hour_week()
        peak = peak_hours()
        repartition = repartition_par_classe()

        fig1, ax1 = plt.subplots(figsize=(5, 3))
        ax1.bar(avg_per_hour.keys(), avg_per_hour.values(), color=BTN_COLOR)
        ax1.set_title("Moyenne d'élèves par heure")
        canvas1 = FigureCanvasTkAgg(fig1, parent)
        canvas1.draw()
        canvas1.get_tk_widget().pack(side=tk.LEFT, padx=10)

        fig2, ax2 = plt.subplots(figsize=(5, 3))
        classes = ["6ème", "5ème", "4ème", "3ème"]
        ax2.pie(repartition, labels=classes, autopct='%1.1f%%')
        ax2.set_title("Répartition par classe")
        canvas2 = FigureCanvasTkAgg(fig2, parent)
        canvas2.draw()
        canvas2.get_tk_widget().pack(side=tk.LEFT, padx=10)

        tk.Label(
            parent,
            text=f"Total cette semaine : {total}\n - Heure de pic : {peak}",
            bg=BG_COLOR,
            fg=FG_COLOR,
            font=FONT
        ).pack(pady=10)

    def display_day_stats(self, parent):
        total = stats_today()
        avg_per_hour = average_per_hour()
        peak = peak_hours()
        repartition = repartition_par_classe()

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(avg_per_hour.keys(), avg_per_hour.values(), marker='o', color=BTN_COLOR)
        ax.set_title("Évolution des élèves par heure")
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)

        tk.Label(
            parent,
            text=f"Total aujourd'hui : {total}\nHeure de pic : {peak}",
            bg=BG_COLOR,
            fg=FG_COLOR,
            font=FONT
        ).pack(pady=10)

    def show_settings(self):
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Paramètres", TITLE_FONT, pady=20).pack()

        theme_frame = tk.Frame(frame, bg=BG_COLOR)
        theme_frame.pack(pady=10)
        self.styled_label(theme_frame, "Thème :", pady=0).pack(side=tk.LEFT)
        theme_menu = tk.OptionMenu(
            theme_frame,
            self.theme_var,
            "light", "dark",
            command=lambda _: self.update_theme()
        )
        theme_menu.config(
            bg=BTN_COLOR,
            fg=BTN_FG,
            font=FONT,
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        theme_menu.pack(side=tk.LEFT, padx=5)

        self.styled_button(frame, "Retour", self.show_menu).pack(pady=14)

    def logout(self):
        self.show_login()

if __name__ == "__main__":
    app = App()
    app.mainloop()
