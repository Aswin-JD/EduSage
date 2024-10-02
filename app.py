from flask import Flask, render_template, Response, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, login_required, current_user, logout_user, UserMixin
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector
import google.generativeai as genai
from PIL import Image
from werkzeug.security import check_password_hash, generate_password_hash
import subprocess
import os

db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = "edusage"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///edusage.db"
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Register.query.get(int(user_id))

class Register(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def is_active(self):
        return True

    def get_id(self):
        return str(self.id)

    def is_authenticated(self):
        return True

with app.app_context():
    db.create_all()

class RegistrationForm(FlaskForm):
    email = EmailField(label='Email', validators=[DataRequired()])
    first_name = StringField(label="First Name", validators=[DataRequired()])
    last_name = StringField(label="Last Name", validators=[DataRequired()])
    username = StringField(label="Username", validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8, max=20)])


class LoginForm(FlaskForm):
    email = EmailField(label='Email', validators=[DataRequired()])
    password = PasswordField(label="Password", validators=[DataRequired()])

@app.route('/')
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = Register.query.filter_by(email=email, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for("home"))

    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully!", "info")
    return redirect(url_for("login"))


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegistrationForm()
    if request.method == "POST" and form.validate_on_submit():
        new_user = Register(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            username=form.username.data,
            password=form.password.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created Successfully! <br>You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)

@app.route("/home", methods=["POST", "GET"])
def home():
    return render_template("index.html")

@app.route("/customer_support", methods=["POST", "GET"])
def customer_support():
    return "<h1>Customer Support Page</h1>"

# @app.route("/logout", methods=["POST", "GET"])
# def logout():
#     return "<h1>Logout Page</h1>"

@app.route("/sign_language", methods=["POST", "GET"])
def sign_language():
    return "<h1>Sign Language Page</h1>"

@app.route("/tutor_interaction", methods=["POST", "GET"])
def tutor_interaction():
    return "<h1>Tutor Interaction Page</h1>"

@app.route("/virtual_board", methods=["POST", "GET"])
def virtual_board():
    return "<h1>Virtul Board Page</h1>"

@app.route("/video_call", methods=["POST", "GET"])
def video_call():
    return "<h1>Vidoe Call Page</h1>"
    
if __name__ == '__main__':
    app.run(debug=True)
