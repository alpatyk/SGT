import os

class Config:
    SECRET_KEY = 'abc123'  
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tarefas.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False