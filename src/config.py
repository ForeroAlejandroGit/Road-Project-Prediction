import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    DATABASE = os.path.join(BASE_DIR, 'database.db')
    SECRET_KEY = 'dev-secret-key-change-in-production'
    GOOGLE_MAPS_API_KEY = 'AIzaSyBqgkrD0et7fQFZp84RvCHoYUWzfgBjvZE'


