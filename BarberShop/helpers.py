from flask import session,redirect,url_for
from functools import wraps
from flask import g
import sqlite3


#Configuraçao de banco de dados
DATABASE = "BarberShop.db"

def get_db():
    """Retorna uma conexão com o banco de dados (por requisição)."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Retorna dicionários em vez de tuplas
    return g.db

def close_db(e=None):
    """Fecha a conexão com o banco de dados."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Função que obriga o login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function