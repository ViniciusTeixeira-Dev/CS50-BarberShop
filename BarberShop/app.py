import os
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from helpers import login_required,get_db,close_db

# Configurar o Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "devkey123") # chave temporaria se não tiver a SECRET_KEY

# Fechar o banco automaticamente ao final da requisição
app.teardown_appcontext(close_db)


@app.route("/")
@login_required
def index():
    return render_template("layout.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect("/")
        else:
            flash("Usuário ou senha incorretos", "danger")
            return redirect("login")
    
    else:
        return render_template("login.html")




if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)

