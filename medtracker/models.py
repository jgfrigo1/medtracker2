from . import db

class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    hours = db.Column(db.String(100), nullable=False)
    meds = db.Column(db.Text)
