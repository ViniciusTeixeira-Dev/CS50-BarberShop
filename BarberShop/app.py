import os
from flask import Flask, flash, redirect, render_template, request, session,url_for
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
    if request.method == "POST":

        #Envia formulario para a rota da reserva
        data_hora = request.form["data_hora"]
        
        #Confirma se possui o horario
        db = get_db()
        confirm = db.execute("SELECT data_hora FROM agendamentos WHERE data_hora = ?", (data_hora,)).fetchone()
        if not confirm:
            flash("Horario Incorreto")
            return redirect("/agendamentos.html")

        if data_hora:
            return redirect(url_for('reservar', data_hora=data_hora))
        return redirect(url_for('agendamentos'))
    
    else:
    
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



@app.route("/reservar", methods=["GET","POST"])
@login_required
def reservar():
    #Confira se tem o "data_hora"
    data_hora = request.form.get("data_hora") or request.args.get("data_hora")
    if not data_hora:
        flash("Agende um horario para acessar", "danger")
        return redirect("/agendamento")
    
    if "confirmado" in request.form:
        db = get_db()
        #Verifica se está disponivel
        horario_disponivel = db.execute(
                "SELECT id FROM agendamentos WHERE data_hora = ? AND disponivel = 1",(data_hora,)).fetchone()
            
        if not horario_disponivel:
                flash("Horário já reservado", "danger")
                return redirect("/agendamento")
        
        #Faz a reserva com os dados do usuario
        db.execute("UPDATE agendamentos SET user_id = ?, disponivel = 0 WHERE data_hora = ? AND disponivel = 1", (session["user_id"], data_hora))
        db.commit()
        flash("Horario reservado com sucesso !", "success")
        return redirect("/minhasReservas")
    

    #Puxa no banco de dados o username para exibir no FrontEnd
    db = get_db()
    username = (db.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],)).fetchone())["username"]

    #Divide a "data_hora" em dois para exibir no FrontEnd separado
    data = data_hora.split()[0]
    hora = data_hora.split()[1][:5]
    return render_template("reservar.html", username = username, data = data, hora = hora)



@app.route("/minhasReservas")
@login_required
def minhasReservas():
    db = get_db()
    reservas = db.execute("SELECT id, data_hora  FROM agendamentos WHERE user_id = ? AND disponivel = 0", [session["user_id"]]).fetchall()
    return render_template("horariosAgendados.html", reservas=reservas)



@app.route("/cancelar-reserva", methods=["POST"])
@login_required
def cancelar_reserva():
    reserva_id = request.form.get("reserva_id")
    
    # Lógica para cancelamento
    db = get_db()
    db.execute("UPDATE agendamentos SET disponivel = 1 WHERE id = ?", (reserva_id,))
    db.commit()
    
    return redirect("/minhasReservas")
        


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

