from flask import current_app as app
from flask import render_template_string, request, jsonify
from . import db
from .models import Mark
import datetime
import json
import os
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

# Diccionario de usuarios (puedes hacer esto más seguro con hash si lo necesitas)
users = {
    "josep": "josep"
}

@auth.verify_password
def verify_password(username, password):
    return users.get(username) == password


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MEDICATIONS = {
    "Sinemet": 1.0,
    "Mirapexin": 1.25,
    "Acfol": 1.5,
    "Azilect": 1.75,
    "Gabapentina": 2.0,
    "Mucuna": 2.25
}

with app.app_context():
    db.create_all()

@app.route('/')
@auth.login_required
def index():
    # Carga el HTML directamente desde archivo si existe (mejor para desarrollo)
    if os.path.exists('index.html'):
        with open('index.html', encoding='utf-8') as f:
            return render_template_string(f.read(), medications=list(MEDICATIONS.keys()))
    return "Archivo index.html no encontrado"

@app.route('/submit', methods=['POST'])
@auth.login_required
def submit():
    try:
        date_str = request.form.get('date')
        if not date_str:
            return jsonify({"message": "Fecha no proporcionada"}), 400

        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        hours = []
        for i in range(8, 24):
            val = request.form.get(f'hour_{i}')
            hours.append(val if val else '')

        meds_data = {}
        for hour in range(8, 24):
            meds_this_hour = []
            for med in MEDICATIONS.keys():
                if request.form.get(f"med_{hour}_{med}") == 'on':
                    meds_this_hour.append(med)
            if meds_this_hour:
                meds_data[str(hour)] = meds_this_hour

        existing = Mark.query.filter_by(date=date).first()
        if existing:
            existing.hours = ",".join(hours)
            existing.meds = json.dumps(meds_data)
        else:
            new_mark = Mark(date=date, hours=",".join(hours), meds=json.dumps(meds_data))
            db.session.add(new_mark)

        db.session.commit()
        return jsonify({"message": "Datos guardados correctamente."})
    except Exception as e:
        return jsonify({"message": f"Error al guardar: {str(e)}"}), 500

@app.route('/get_data', methods=['GET'])
@auth.login_required
def get_data():
    try:
        start_date = datetime.datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()

        marks = Mark.query.filter(Mark.date >= start_date, Mark.date <= end_date).order_by(Mark.date).all()
        data_points = []
        previous_date = None

        for mark in marks:
            if previous_date and mark.date != previous_date:
                # Añadir punto nulo para romper la línea entre días
                null_point = {
                    "timestamp": f"{previous_date} 23:59",
                    "value": None,
                    "type": "mark"
                }
                data_points.append(null_point)
    
            hourly_values = mark.hours.split(',')
            for i, val in enumerate(hourly_values):
                if val.strip():
                    hour = 8 + i
                    timestamp = f"{mark.date} {hour:02d}:00"
                    data_points.append({"timestamp": timestamp, "value": int(val), "type": "mark"})
    
            if mark.meds:
                meds_data = json.loads(mark.meds)
                for hour_str, meds in meds_data.items():
                    for med in meds:
                        timestamp = f"{mark.date} {int(hour_str):02d}:00"
                        data_points.append({
                            "timestamp": timestamp,
                            "value": MEDICATIONS.get(med, 0),
                            "type": "med",
                            "label": med
                        })
    
            previous_date = mark.date
    
        return jsonify(data_points)
    except Exception as e:
        return jsonify({"message": f"Error al recuperar datos: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
