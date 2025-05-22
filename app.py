from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, make_response
import sqlite3
import json
from datetime import datetime
from weasyprint import HTML
from export_excel import export_to_excel

app = Flask(__name__)
DB_FILE = 'tbm.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tbm_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, time TEXT, location TEXT, department TEXT, leader TEXT,
                work_location TEXT, work_content TEXT, preparation TEXT, precautions TEXT,
                ppe TEXT, risk_items TEXT, attendees TEXT, leader_signature TEXT, created_at TEXT
            )
        ''')
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save', methods=['POST'])
def save_tbm():
    data = request.json
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tbm_records (
                date, time, location, department, leader,
                work_location, work_content, preparation, precautions,
                ppe, risk_items, attendees, leader_signature, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('date'), data.get('time'), data.get('location'), data.get('department'), data.get('leader'),
            data.get('workLocation'), data.get('workContent'), data.get('preparation'), data.get('precautions'),
            json.dumps(data.get('ppe')), json.dumps(data.get('riskItems')), json.dumps(data.get('attendees')),
            data.get('leaderSignature'), datetime.now().isoformat()
        ))
        conn.commit()
    return jsonify({'message': '저장 완료'})

@app.route('/list')
def tbm_list():
    location_filter = request.args.get('location')
    department_filter = request.args.get('department')
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        query = "SELECT id, date, location, department, leader FROM tbm_records WHERE 1=1"
        params = []
        if location_filter:
            query += " AND location = ?"
            params.append(location_filter)
        if department_filter:
            query += " AND department = ?"
            params.append(department_filter)
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
    return render_template('list.html', records=rows)

@app.route('/detail/<int:record_id>')
def tbm_detail(record_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tbm_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Record not found'}), 404
        keys = [d[0] for d in cursor.description]
        data = dict(zip(keys, row))
        data['ppe'] = json.loads(data['ppe']) if data['ppe'] else []
        data['risk_items'] = json.loads(data['risk_items']) if data['risk_items'] else []
        data['attendees'] = json.loads(data['attendees']) if data['attendees'] else []
    return jsonify(data)

@app.route('/pdf/<int:record_id>')
def generate_pdf(record_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tbm_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if not row:
            return 'TBM 데이터 없음', 404
        keys = [d[0] for d in cursor.description]
        data = dict(zip(keys, row))
        data['ppe'] = json.loads(data['ppe']) if data['ppe'] else []
        data['risk_items'] = json.loads(data['risk_items']) if data['risk_items'] else []
        data['attendees'] = json.loads(data['attendees']) if data['attendees'] else []
        for p in data['attendees']:
            if isinstance(p, dict) and 'signature' in p and 'data-signature' in p:
                p['signature_data'] = p['data-signature']
            else:
                p['signature_data'] = None
    html = render_template('pdf_template.html', tbm=data)
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=tbm_{record_id}.pdf'
    return response

@app.route('/export_excel')
def export_excel():
    location_filter = request.args.get('location')
    department_filter = request.args.get('department')
    file_path = export_to_excel(location_filter, department_filter)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
