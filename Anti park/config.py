import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-evnpark-xyz')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE = os.environ.get('DATABASE', os.path.join(BASE_DIR, 'evnpark.db'))
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDbsWpN4T_GHe0RuEGTBt0GORoT2LltWp0')
