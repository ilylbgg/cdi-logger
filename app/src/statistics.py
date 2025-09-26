from .database import get_all_attendance
from collections import defaultdict
from datetime import datetime

def stats_today():
    data = get_all_attendance()
    today = datetime.now().strftime('%Y-%m-%d')
    today_data = [row for row in data if row[7] == today]
    total = sum(row[6] for row in today_data)
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
    rep = {'6ème': 0, '5ème': 0, '4ème': 0, '3ème': 0}
    for row in data:
        rep['6ème'] += row[2]
        rep['5ème'] += row[3]
        rep['4ème'] += row[4]
        rep['3ème'] += row[5]
    return rep

# ...other statistics functions...
