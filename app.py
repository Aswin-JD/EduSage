<<<<<<< HEAD
from flask import Flask, render_template, Response
import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import google.generativeai as genai
from PIL import Image
import os
# from dotenv import load_dotenv
from flask_socketio import SocketIO, emit

# load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app)

# Initialize the webcam to capture video
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Initialize the HandDetector class with the given parameters
detector = HandDetector(staticMode=False, maxHands=1, modelComplexity=1, detectionCon=0.7, minTrackCon=0.5)

genai.configure(api_key= 'AIzaSyBQk7Saxz2x4zyEhLTUforesq1oc6igQnY')
model = genai.GenerativeModel('gemini-1.5-flash')

prev_pos = None
canvas = None

def getHandInfo(img):
    hands, img = detector.findHands(img, draw=False, flipType=True)
    if hands:
        hand = hands[0]
        lmList = hand["lmList"]
        fingers = detector.fingersUp(hand)
        return fingers, lmList
    else:
        return None

def draw(info, prev_pos, canvas, img):
    fingers, lmList = info
    current_pos = None
    if fingers == [0, 1, 0, 0, 0]:
        current_pos = lmList[8][0:2]
        if prev_pos is None: prev_pos = current_pos
        cv2.line(canvas, tuple(current_pos), tuple(prev_pos), (255, 0, 255), 10)
    elif fingers == [1, 0, 0, 0, 0]:
        canvas = np.zeros_like(img)
    return current_pos, canvas

def sendToAI(model, canvas, fingers):
    if fingers == [1, 1, 1, 1, 0]:
        pil_image = Image.fromarray(canvas)
        response = model.generate_content(["Solve this math problem", pil_image])
        return response.text
    return ""

@app.route('/')
def index():
    return render_template('index.html')

def gen_frames():
    global prev_pos, canvas
    while True:
        success, img = cap.read()
        img = cv2.flip(img, 1)

        if canvas is None:
            canvas = np.zeros_like(img)

        info = getHandInfo(img)
        if info:
            prev_pos, canvas = draw(info, prev_pos, canvas, img)
            output_text = sendToAI(model, canvas, info[0])
            if output_text:
                print("AI Output:", output_text)
                socketio.emit('ai_output', {'text': output_text})
                return ""

        image_combined = cv2.addWeighted(img, 0.7, canvas, 0.3, 0)
        ret, buffer = cv2.imencode('.jpg', image_combined)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    socketio.run(app, debug=True)
=======
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
>>>>>>> 5c6e4dae2a9a22339991268a2cdc448a39d56e1c
