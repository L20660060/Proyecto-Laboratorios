import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-super-secreta-cambia-esto'
    BASE_DIR = Path(__file__).resolve().parent
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR / "app.sqlite"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False