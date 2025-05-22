import sqlite3
import openpyxl
from datetime import datetime

DB_FILE = 'tbm.db'

def export_to_excel(location_filter=None, department_filter=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    query = "SELECT * FROM tbm_records WHERE 1=1"
    params = []

    if location_filter:
        query += " AND location = ?"
        params.append(location_filter)
    if department_filter:
        query += " AND department = ?"
        params.append(department_filter)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'TBM Records'

    ws.append(columns)
    for row in rows:
        ws.append(row)

    filename = f"tbm_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)
    return filename
