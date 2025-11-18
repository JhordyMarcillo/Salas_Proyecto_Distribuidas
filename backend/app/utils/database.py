from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt

mongo = PyMongo()
bcrypt = Bcrypt()

def init_database(app):
    """Inicializa la base de datos y el bcrypt"""
    mongo.init_app(app)
    bcrypt.init_app(app)
    return mongo, bcrypt