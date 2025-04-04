import os
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from helpers import login_required,get_db,close_db,horariosDisponiveis
from datetime import datetime,timedelta
import pytz


# Configurar o Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey123") # chave temporaria se não tiver a SECRET_KEY

# Fechar o banco automaticamente ao final da requisição
app.teardown_appcontext(close_db)

@app.route("/")
def index():
    return render_template("layout.html")


@app.route("/agendamento", methods=["GET", "POST"])
@login_required
def agendamentos():
    user_id = session["user_id"]
    disponiveis = horariosDisponiveis(user_id)
    
    # Obtém a data atual com fuso horário correto
    fuso = pytz.timezone('America/Sao_Paulo')
    hoje = datetime.now(fuso).strftime('%Y-%m-%d')
    
    # Organiza os horários por dia
    dias = {}
    for data_hora in disponiveis:
        data = data_hora.split()[0]
        hora = data_hora.split()[1][:5]
        
        if data not in dias:
            dias[data] = []
        dias[data].append(hora)
    
    # Garante os próximos 7 dias, mesmo sem horários
    dias_completos = {}
    for i in range(7):
        data = (datetime.now(fuso) + timedelta(days=i)).strftime('%Y-%m-%d')
        dias_completos[data] = dias.get(data, [])
    
    return render_template("agendamentos.html", 
                        dias_agendamento=dias_completos,
                        hoje=hoje)
    

@app.route("/reservar", method=["GET", "POST"])
def reservar():
    if request.method == "POST":
        data_hora = request.form["data_hora"]
        
        if not data_hora:
            return render_template("agendamentos.html")

        
    
    
    
    
    else:
        return render_template("reserva.html")
    



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        #Verifica se o usuario fornecido e senhas são iguais aos do banco de dados
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/")
        else:
            flash("Usuário ou senha incorretos", "danger")
            return redirect("login")
    
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        passwordConfirm = request.form["passwordConfirm"]
        
        #Verifica se ja tem um usuario com o mesmo nome
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user is not None:
            flash("Este nome ja está em uso", "warning")
            return redirect("/register")

        #Verifica se as senhas são diferentes
        if password != passwordConfirm:
            flash("Senhas não coincidem", "warning")
            return redirect("/register")
        
        #Insere no banco de dados o novo usuario com a senha hasheada(para maior segurança)
        password = generate_password_hash(password)
        
        db.execute("INSERT INTO users (username, password) VALUES (?,?)", (username,password))
        db.commit()
        
        #Loga o usuario no site
        user_id = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        session["user_id"] = user_id["id"]
    
        
        return redirect("/")
    
    else:
        return render_template("register.html")
    
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")

@app.template_filter('format_data_curto')
def format_data_curto(data_str):
    dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    try:
        # Converte a string para datetime (sem fuso horário)
        data_naive = datetime.strptime(data_str, '%Y-%m-%d')

        # Retorna o nome correto do dia da semana
        return dias[data_naive.weekday()]
    except Exception as e:
        return f"Erro: {e}"
    


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)

