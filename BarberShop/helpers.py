from flask import session,redirect,url_for
from functools import wraps
from flask import g
from datetime import datetime,timedelta
import pytz
import sqlite3


#Configuraçao de banco de dados
DATABASE = "BarberShop.db"

#Retorna uma conexão com o banco de dados (por requisição)
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Retorna dicionários em vez de tuplas
    return g.db

#Fecha a conexão com banco de dados
def close_db(e=None):
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


#Faz a inserçao dos dias disponiveis a partir do dia atual
def horariosDisponiveis(user_id):
    #Pega o horario de Brasilia e define os horarios de trabalho
    fuso = pytz.timezone('America/Sao_Paulo')  
    hoje = datetime.now(fuso)
    horarios = ['08:00','08:30','09:00','09:30','10:00']
    disponiveis = []
    
    db = get_db()
    
    #Verifica se o dia não é domingo e adiciona no banco de dados os horarios a partir do dia atual
    for dias in range(8):  
        data = hoje + timedelta(days=dias)
        if data.weekday() != 6 :  # Domingo = 6 
            for horario in horarios:
                # Combina data + horário e insere no banco de dados
                sql_format = f"{data.strftime('%Y-%m-%d')} {horario}:00"
                
                #Verifica se ja tem o dia no banco de dados
                existe = db.execute(
                        "SELECT * FROM agendamentos WHERE data_hora = ? ",
                        (sql_format,)
                    ).fetchall()
                
                if not existe:
                
                    db.execute("INSERT INTO agendamentos (data_hora,user_id) VALUES (?, ?)", (sql_format,user_id))
           
    db.commit()
                
    #Faz a seleção dos horarios disponiveis a partir do dia atual
    disponiveis = db.execute("SELECT * FROM agendamentos WHERE data_hora >= ? AND disponivel = TRUE ORDER BY data_hora", (hoje.strftime('%Y-%m-%d 00:00:00'),)).fetchall()
    return [row['data_hora'] for row in disponiveis]
            
