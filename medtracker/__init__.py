from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import event
from sqlalchemy.engine import Engine
import psycopg2

db = SQLAlchemy()

@event.listens_for(Engine, "engine_connect")
def ping_connection(connection, branch):
    if branch:
        return
    try:
        connection.scalar("SELECT 1")
    except psycopg2.Error:
        connection.invalidate()
        connection.scalar("SELECT 1")
        
def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///marks.db").replace("postgres://", "postgresql://")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from . import routes
        from .models import Mark
        db.create_all()

    return app
