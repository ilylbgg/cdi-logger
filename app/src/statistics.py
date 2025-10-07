from .database import get_all_attendance
from collections import defaultdict
from datetime import datetime, timedelta
debug = False

def stats_today(target_date=None):
    data = get_all_attendance()
    if target_date is None:
        target_date = datetime.now()
    date_str = target_date.strftime('%Y-%m-%d')
    day_data = [row for row in data if row[7] == date_str]
    total = sum(row[6] for row in day_data)
    return total

def average_per_hour():
    data = get_all_attendance()
    hours = defaultdict(list)
    for row in data:
        hours[row[1]].append(row[6])
    return {h: sum(vals)/len(vals) for h, vals in hours.items()}

def peak_hours():
    data = get_all_attendance()
    hours = defaultdict(int)
    for row in data:
        hours[row[1]] += row[6]
    if not hours:
        return []
    max_val = max(hours.values())
    return [h for h, v in hours.items() if v == max_val]

def repartition_par_classe():
    data = get_all_attendance()
    rep = {'6': 0, '5': 0, '4': 0, '3': 0}
    for row in data:
        rep['6'] += row[2]  # sixième
        rep['5'] += row[3]  # cinquième
        rep['4'] += row[4]  # quatrième
        rep['3'] += row[5]  # troisième
    return rep

def stats_semaine(target_date=None):
    data = get_all_attendance()
    if target_date is None:
        target_date = datetime.now()
    # Début de la semaine = lundi
    start_week = target_date - timedelta(days=target_date.weekday())
    start_week_str = start_week.strftime('%Y-%m-%d')
    # Fin de la semaine = dimanche
    end_week = start_week + timedelta(days=6)
    end_week_str = end_week.strftime('%Y-%m-%d')
    
    if debug : 
        print(f"Calcul stats semaine du {start_week_str} au {end_week_str}")
    week_data = [row for row in data if start_week_str <= row[7] <= end_week_str]
    total = sum(row[6] for row in week_data)
    if debug :
        print(f"Données de la semaine trouvées: {len(week_data)}")
    return total

def average_per_hour_week(target_date=None):
    data = get_all_attendance()
    if target_date is None:
        target_date = datetime.now()
    # Début de la semaine = lundi
    start_week = target_date - timedelta(days=target_date.weekday())
    start_week_str = start_week.strftime('%Y-%m-%d')
    # Fin de la semaine = dimanche
    end_week = start_week + timedelta(days=6)
    end_week_str = end_week.strftime('%Y-%m-%d')

    if debug :
        print(f"Période: du {start_week_str} au {end_week_str}")
        print(f"Nombre total d'entrées: {len(data)}")
    
    # Créer un dictionnaire avec toutes les heures possibles initialisées à 0
    all_hours = [f"{h:02d}:00" for h in range(8, 18) if h not in (12, 17)]
    hours_data = {h: [] for h in all_hours}
    
    # Filtrer les données de la semaine
    week_data = [row for row in data if start_week_str <= row[7] <= end_week_str]
    if debug then
        print(f"Nombre d'entrées pour la semaine: {len(week_data)}")
        print("Premières entrées de la semaine:", week_data[:3] if week_data else "Aucune donnée")
    
    # Créer un dictionnaire avec toutes les heures possibles
    all_hours = [f"{h:02d}:00" for h in range(8, 18) if h not in (12, 17)]
    hours_data = {h: [] for h in all_hours}
    
    # Collecter les données par heure
    for row in week_data:  # Utiliser week_data au lieu de data
        if row[1] in hours_data:
            hours_data[row[1]].append(row[6])
    
    # Calculer les moyennes
    result = {}
    for hour in all_hours:
        values = hours_data[hour]
        if values:  # S'il y a des données pour cette heure
            result[hour] = sum(values) / len(values)
        else:
            result[hour] = 0
    
    if debug :
        print("Moyennes calculées:", result)
    return result

# ...other statistics functions...
