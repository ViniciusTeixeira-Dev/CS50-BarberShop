import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

# Configurar o Flask
app = Flask(__name__)

# Banco de Dados
#connect = sqlite3.connect("MUDAR AINDA")
#db = connect.cursor()


@app.route("/")
def index():
    return render_template("layout.html")


