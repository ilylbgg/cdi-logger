import csv
from .database import get_all_attendance

def export_csv(filepath):
    data = get_all_attendance()
    headers = ['id', 'heure', 'sixieme', 'cinquieme', 'quatrieme', 'troisieme', 'total', 'date']
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)

# PDF export can be implemented with reportlab or similar library
def export_pdf(filepath):
    # ...PDF export logic...
    pass
