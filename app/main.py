
import configparser
from datetime import datetime, timedelta
import calendar
import os
import tkinter as tk
from tkinter import messagebox
import logging

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

debug = False

# --- Logging setup ---
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.info('Application démarrée')

# Lecture du thème depuis settings.cfg
config = configparser.ConfigParser()
script_dir = os.path.dirname(os.path.abspath(__file__))
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
matplotlib.style.use('default')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        Base = config.get('Database', 'Base', fallback='ERREUR')
        CDI_Name = config.get("General","CDI_Name",fallback='AUCUN NOM')
        self.title(f"[CDIStats] | Base : {Base} | {CDI_Name}")
        self.geometry("800x600")
        self.configure(bg=BG_COLOR)
        self.theme_var = tk.StringVar(value=theme)
        init_db()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        logging.info("Lancement de l'application principale.")
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
        with open('./config.cfg', 'w', encoding='utf-8') as f:
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
        logging.info(f"Tentative de connexion pour l'utilisateur: {username}")
        if authenticate(username, password):
            logging.info(f"Connexion réussie pour l'utilisateur: {username}")
            self.username_var.set("")
            self.password_var.set("")
            self.show_menu()
        else:
            logging.warning(f"Échec de connexion pour l'utilisateur: {username}")
            messagebox.showerror("Erreur", "Nom d'utilisateur ou mot de passe incorrect.")

    def show_menu(self):
        logging.info("Affichage du menu principal.")
        self.clear_window()
        frame = self.center_frame()
        self.styled_label(frame, "Menu principal", TITLE_FONT, pady=18).pack()
        self.styled_button(frame, "Nouvelle Heure", self.show_new_entry).pack(pady=10)
        self.styled_button(frame, "Statistiques", self.show_statistics).pack(pady=10)
        self.styled_button(frame, "Paramètres", self.show_settings).pack(pady=10)
        self.styled_button(frame, "Déconnexion", self.logout).pack(pady=10)

    def show_new_entry(self):
        logging.info("Nouvelle entrée : sélection du jour et de l'heure.")
        self.clear_window()
        self.entry_data = {}
        self.show_entry_jour_heure()

    def update_date_display(self):
        self.date_label.config(text=self.selected_date.strftime('%d/%m/%Y'))

    def previous_day(self):
        self.selected_date -= timedelta(days=1)
        self.update_date_display()

    def next_day(self):
        self.selected_date += timedelta(days=1)
        self.update_date_display()

    def show_calendar(self):
        cal_window = tk.Toplevel(self)
        cal_window.title('Sélectionner une date')
        cal_window.configure(bg=BG_COLOR)

        year = self.selected_date.year
        month = self.selected_date.month

        def update_month(delta):
            nonlocal month, year
            month += delta
            if month > 12:
                month = 1
                year += 1
            elif month < 1:
                month = 12
                year -= 1
            update_calendar()

        def update_calendar():
            month_label.config(text=f"{calendar.month_name[month]} {year}")
            for widget in days_frame.winfo_children():
                widget.destroy()

            # Jours de la semaine
            days = ['Lun', 'Mar', 'Jeu', 'Ven']
            for i, day in enumerate(days):
                tk.Label(days_frame, text=day, bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=i)

            # Calendrier
            cal = calendar.monthcalendar(year, month)
            for i, week in enumerate(cal):
                for j, day in enumerate(week):
                    if day != 0:
                        btn = tk.Button(days_frame, text=str(day), bg=BTN_COLOR, fg=BTN_FG,
                                      command=lambda d=day: select_date(d))
                        btn.grid(row=i+1, column=j)

        def select_date(day):
            self.selected_date = datetime(year, month, day)
            self.update_date_display()
            cal_window.destroy()

        nav_frame = tk.Frame(cal_window, bg=BG_COLOR)
        nav_frame.pack(pady=5)
        tk.Button(nav_frame, text="<", command=lambda: update_month(-1), bg=BTN_COLOR, fg=BTN_FG).pack(side=tk.LEFT, padx=5)
        month_label = tk.Label(nav_frame, text="", bg=BG_COLOR, fg=FG_COLOR)
        month_label.pack(side=tk.LEFT, padx=20)
        tk.Button(nav_frame, text=">", command=lambda: update_month(1), bg=BTN_COLOR, fg=BTN_FG).pack(side=tk.LEFT, padx=5)

        days_frame = tk.Frame(cal_window, bg=BG_COLOR)
        days_frame.pack(padx=10, pady=5)

        update_calendar()

    def show_entry_jour_heure(self):
        frame = self.center_frame()
        self.styled_label(frame, "Nouvelle Entrée - Jour & Heure", TITLE_FONT, pady=10).pack()
        
        # Frame pour la date
        date_frame = tk.Frame(frame, bg=BG_COLOR)
        date_frame.pack(pady=10)
        
        # Initialisation de la date sélectionnée
        self.selected_date = datetime.now()
        
        # Boutons et affichage de la date
        tk.Button(date_frame, text="<", command=self.previous_day, bg=BTN_COLOR, fg=BTN_FG).pack(side=tk.LEFT, padx=5)
        self.date_label = tk.Label(date_frame, text="", bg=BG_COLOR, fg=FG_COLOR, font=FONT)
        self.date_label.pack(side=tk.LEFT, padx=20)
        tk.Button(date_frame, text=">", command=self.next_day, bg=BTN_COLOR, fg=BTN_FG).pack(side=tk.LEFT, padx=5)
        tk.Button(date_frame, text="Calendrier", command=self.show_calendar, bg=BTN_COLOR, fg=BTN_FG).pack(side=tk.LEFT, padx=20)
        
        self.update_date_display()
        
        # Sélection de l'heure
        hours = [f"{h:02d}:00" for h in range(8, 18) if h not in (12, 17)]
        self.heure_var = tk.StringVar(value=hours[0])
        hour_frame = tk.Frame(frame, bg=BG_COLOR)
        hour_frame.pack(pady=10)
        self.styled_label(hour_frame, "Heure :", pady=0).pack(side=tk.LEFT)
        tk.OptionMenu(hour_frame, self.heure_var, *hours).pack(side=tk.LEFT, padx=5)
        
        # Boutons de navigation
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
            date = self.selected_date.strftime('%Y-%m-%d')
            add_attendance(heure, sixieme, cinquieme, quatrieme, troisieme, total, date)
            logging.info(f"Entrée enregistrée : {date} {heure} | 6e:{sixieme} 5e:{cinquieme} 4e:{quatrieme} 3e:{troisieme} (total={total})")
            messagebox.showinfo("Succès", "Entrée enregistrée.")
            self.show_menu()
        except Exception as e:
            logging.error(f"Erreur lors de l'enregistrement de l'entrée : {e}")
            messagebox.showerror("Erreur", f"Entrée invalide: {e}")

    def show_statistics(self, mode="semaine", selected_date=None):
        logging.info(f"Affichage des statistiques : mode={mode}")
        self.clear_window()
        frame = tk.Frame(self, bg=BG_COLOR)
        frame.place(relx=0.5, rely=0.1, anchor="n", relwidth=0.95, relheight=0.85)
        
        # Initialisation de la date sélectionnée
        if not hasattr(self, 'stats_date') or selected_date is not None:
            self.stats_date = selected_date if selected_date else datetime.now()

        # Frame pour les boutons de mode
        btn_frame = tk.Frame(frame, bg=BG_COLOR)
        btn_frame.pack(pady=5)
        for label, m in [("Semaine", "semaine"), ("Jour", "jour"), ("Mois", "mois")]:
            self.styled_button(
                btn_frame, label,
                lambda m=m: self.show_statistics(m, self.stats_date),
                width=12, pady=2
            ).pack(side=tk.LEFT, padx=5)

        # Frame pour la navigation dans les dates
        date_frame = tk.Frame(frame, bg=BG_COLOR)
        date_frame.pack(pady=5)

        def update_date(delta):
            if mode == "jour":
                self.stats_date += timedelta(days=delta)
            elif mode == "semaine":
                self.stats_date += timedelta(weeks=delta)
            elif mode == "mois":
                year = self.stats_date.year + ((self.stats_date.month + delta - 1) // 12)
                month = (self.stats_date.month + delta - 1) % 12 + 1
                self.stats_date = self.stats_date.replace(year=year, month=month)
            self.show_statistics(mode, self.stats_date)

        # Boutons de navigation
        nav_frame = tk.Frame(date_frame, bg=BG_COLOR)
        nav_frame.pack()

        # Bouton précédent
        self.styled_button(nav_frame, "<", lambda: update_date(-1), width=3, pady=2).pack(side=tk.LEFT, padx=5)

        # Label de la date
        if mode == "jour":
            date_text = self.stats_date.strftime("%d/%m/%Y")
        elif mode == "semaine":
            start = self.stats_date - timedelta(days=self.stats_date.weekday())
            end = start + timedelta(days=6)
            date_text = f"Semaine du {start.strftime('%d/%m/%Y')} au {end.strftime('%d/%m/%Y')}"
        else:  # mode == "mois"
            date_text = self.stats_date.strftime("%B %Y")
        
        tk.Label(nav_frame, text=date_text, bg=BG_COLOR, fg=FG_COLOR, font=FONT).pack(side=tk.LEFT, padx=20)

        # Bouton suivant
        self.styled_button(nav_frame, ">", lambda: update_date(1), width=3, pady=2).pack(side=tk.LEFT, padx=5)

        # Bouton Aujourd'hui
        self.styled_button(date_frame, "Aujourd'hui", 
                         lambda: self.show_statistics(mode, datetime.now()),
                         width=15, pady=2).pack(pady=5)

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
        logging.info(f"Total de la semaine: {total}")
        avg_per_hour = average_per_hour_week()
        logging.info(f"Moyennes par heure: {avg_per_hour}")
        peak = peak_hours()
        logging.info(f"Heures de pic: {peak}")
        repartition = repartition_par_classe()
        logging.info(f"Répartition par classe: {repartition}")

        # Graphique des moyennes par heure
        fig1, ax1 = plt.subplots(figsize=(5, 3))
        # Conversion en listes pour le graphique
        hours = list(avg_per_hour.keys())
        values = list(avg_per_hour.values())
        if debug :
            print(f"Heures disponibles: {hours}")
            print(f"Valeurs: {values}")
        
        if hours:  # S'il y a des heures disponibles
            ax1.bar(hours, values, color=BTN_COLOR)
            ax1.set_xlabel('Heures')
            ax1.set_ylabel('Nombre moyen d\'élèves')
            # Rotation des labels pour une meilleure lisibilité
            plt.xticks(rotation=45)
            # Ajuster les marges pour éviter que les labels soient coupés
            plt.tight_layout()
        else:
            ax1.text(0.5, 0.5, 'Aucune donnée', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax1.transAxes)
            ax1.axis('off')
        ax1.set_title("Moyenne d'élèves par heure")
        canvas1 = FigureCanvasTkAgg(fig1, parent)
        canvas1.draw()
        canvas1.get_tk_widget().pack(side=tk.LEFT, padx=10)

        # Graphique de répartition par classe
        fig2, ax2 = plt.subplots(figsize=(5, 3))
        classes = ["6ème", "5ème", "4ème", "3ème"]
        values = [repartition.get('6', 0), repartition.get('5', 0), 
                 repartition.get('4', 0), repartition.get('3', 0)]
        
        # Vérifier si on a des données non nulles
        if sum(values) > 0:
            ax2.pie(values, labels=classes, autopct='%1.1f%%')
        else:
            ax2.text(0.5, 0.5, 'Aucune donnée', 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax2.transAxes)
            ax2.axis('off')  # Cacher les axes si pas de données
        
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
        logging.info("Déconnexion de l'utilisateur.")
        self.show_login()

if __name__ == "__main__":
    app = App()
    app.mainloop()
