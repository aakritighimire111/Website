from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
from datetime import datetime

# For password reset token and email sending
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import smtplib
from email.mime.text import MIMEText

# Initialize Flask and SQLAlchemy
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Ensure database directory exists
db_dir = os.path.join(os.path.dirname(__file__), 'instance')
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'users.db')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Email configuration ---
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
  # get from environment variable named MAIL_PASSWORD
MAIL_USE_TLS = True
MAIL_USE_SSL = False


# Token serializer using app secret key
serializer = URLSafeTimedSerializer(app.secret_key)

def send_email(to_email, subject, body):
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = MAIL_USERNAME
    msg["To"] = to_email

    try:
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        if MAIL_USE_TLS:
            server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_USERNAME, [to_email], msg.as_string())
        server.quit()
        print(f"Password reset email sent to {to_email}")
    except Exception as e:
        print("Failed to send email:", e)

# --------------------------- MODELS ---------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    bmi = db.Column(db.Float)
    preferred_exercise_type = db.Column(db.String(100))
    diet_preference = db.Column(db.String(100))

    workouts = db.relationship('Workout', back_populates='user')
    diet_logs = db.relationship('DietLog', back_populates='user')

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    workout_type = db.Column(db.String(100))
    duration = db.Column(db.Integer)  # in minutes

    user = db.relationship('User', back_populates='workouts')

class DietLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    meal = db.Column(db.String(100))
    calories = db.Column(db.Integer)

    user = db.relationship('User', back_populates='diet_logs')

# Initialize the database
with app.app_context():
    db.create_all()

# --------------------------- ROUTES ---------------------------

@app.route('/')
def home():
    return render_template("index.html")
@app.route('/check_mail')
def check_mail():
    return f"MAIL_USERNAME={MAIL_USERNAME}<br>MAIL_PASSWORD={'set' if MAIL_PASSWORD else 'not set'}"


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in or use another email.", "warning")
            return redirect(url_for('signup'))

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        return redirect(url_for('bmicalculation'))

    return render_template('signup.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Or whatever logic you're using to log out
    return redirect(url_for('home'))  # Redirect to 'home' instead of 'index'

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Sign in successful!", "success")
            return redirect(url_for('next_page'))
        else:
            flash("Invalid credentials, please try again.", "danger")
            return redirect(url_for('signin'))

    return render_template('signin.html')

@app.route('/bmicalculation')
def bmicalculation():
    return render_template('bmicalculation.html')
@app.route('/update_progress', methods=['POST'])
def update_progress():
    # Example logic for updating progress
    # You can fetch form data like this:
    workout_done = request.form.get('workout_done')
    duration = request.form.get('duration')
    notes = request.form.get('notes')

    # Save to DB or session (you decide)
    flash('Progress updated successfully!')
    return redirect(url_for('progress'))


@app.route('/save_bmi', methods=['POST'])
def save_bmi():
    bmi = request.form.get('bmi')
    exercise = request.form.get('preferred_exercise_type')
    diet = request.form.get('diet_preference')

    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            try:
                user.bmi = float(bmi)
                user.preferred_exercise_type = exercise
                user.diet_preference = diet
                db.session.commit()
            except Exception as e:
                print("Error saving to DB:", e)

    return redirect(url_for('next_page'))

@app.route('/next')
def next_page():
    return render_template('next.html')

@app.route('/users')
def user_table():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/offer')
def offer():
    return render_template('offer.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/tracker')
def tracker():
    return render_template('tracker.html')

@app.route("/get_nutrition", methods=["POST"])
def get_nutrition():
    data = request.get_json()
    food = data.get("query", "")
    headers = {
        "x-app-id": os.getenv("NUTRITIONIX_APP_ID"),
        "x-app-key": os.getenv("NUTRITIONIX_API_KEY"),
        "Content-Type": "application/json"
    }
    response = requests.post("https://trackapi.nutritionix.com/v2/natural/nutrients", headers=headers, json={"query": food})
    return response.json()

@app.route('/workouts')
def workout():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))

    user = User.query.get(user_id)
    if not user or not user.bmi or not user.preferred_exercise_type:
        return redirect(url_for('bmicalculation'))

    bmi = user.bmi
    preference = user.preferred_exercise_type.lower()
    video_recommendations = []

    if bmi < 18.5:
        video_recommendations = [
           {"title": "Do This Exercise EVERY DAY for Gains!", "url": "https://www.youtube.com/watch?v=u6PNjgn1ocM"},
           {"title": "Workout Program For Skinny Guys Trying To Get Bigger", "url": "https://www.youtube.com/watch?v=Qi0p-6XcTX0"},
           {"title": "5 MUST DO Exercises For Skinny Guys (NO EQUIPMENT)", "url": "https://www.youtube.com/watch?v=Y9hiyIo963A"},
           {"title": "5-minute Workout For SKINNY GUYS GAIN MUSCLE At Home", "url": "https://www.youtube.com/watch?v=IysRUAjVCpg"},
           {"title": "INTENSE Weight Gain Workout - OMG!", "url": "https://www.youtube.com/watch?v=W7mN-i0J7M0"}
        ]
    elif 18.5 <= bmi < 25:
        if preference == "cardio":
            video_recommendations = [
                {"title": "15 MIN BEGINNER CARDIO Workout (At Home No Equipment)", "url": "https://www.youtube.com/watch?v=VWj8ZxCxrYk"},
                {"title": "Fat Burning, High Intensity, Low Impact Home Cardio Workout", "url": "https://www.youtube.com/watch?v=8oQ-WNJoYtM"},
                {"title": "30 Minute Fat Burning Home Workout for Beginners", "url": "https://www.youtube.com/watch?v=gC_L9qAHVJ8"},
                {"title": "15 MIN BEGINNER CARDIO WORKOUT (No Jumping)", "url": "https://www.youtube.com/watch?v=3oitzTfujXs"},
                {"title": "30 MIN PUMPING CARDIO WORKOUT | Full Body", "url": "https://www.youtube.com/watch?v=kZDvg92tTMc"},
                {"title": "30 MIN CARDIO AEROBICS WORKOUT - Move To The Beat", "url": "https://www.youtube.com/watch?v=vI5MzT-wIjs"},
                {"title": "20 MIN CARDIO AEROBICS WORKOUT - Move To The Beat", "url": "https://www.youtube.com/watch?v=DMAxIrCAAZ0"},
                {"title": "30 MIN CARDIO HIIT WORKOUT - ALL STANDING", "url": "https://www.youtube.com/watch?v=nbP7m0S0Ato"},
                {"title": "Low Impact, All Standing CARDIO Workout. Beginner Friendly.", "url": "https://www.youtube.com/watch?v=ft9lgLOVhr4"},
                {"title": "15 Minutes BEGINNER CARDIO Workout | Joe Wicks", "url": "https://www.youtube.com/watch?v=mnEQ3ezU3Sw"}
            ]
        elif preference == "strength":
            video_recommendations = [
                {"title": "17 Min Strength Training Workout for Beginners", "url": "https://www.youtube.com/watch?v=WIHy-ZnSndA"},
                {"title": "30-minute NO REPEAT Strength Training for Beginners", "url": "https://www.youtube.com/watch?v=IMXX7A8vQGg"},
                {"title": "Weight Training for Beginners & Seniors // 20 Minute Workout", "url": "https://www.youtube.com/watch?v=Qbv2edgrgvI"},
                {"title": "20 Minute Full Body Strength Workout (No Equipment/No Repeat)", "url": "https://www.youtube.com/watch?v=Q2cMMnUuKYQ"},
                {"title": "Strength Training for Beginners | Joe Wicks Workouts", "url": "https://www.youtube.com/watch?v=xO3NJ7A7w5o"}
            ]
        elif preference == "yoga":
            video_recommendations = [
                {"title": "10-Minute Yoga For Beginners | Start Yoga Here...", "url": "https://www.youtube.com/watch?v=j7rKKpwdXNE"},
                {"title": "20 Min Full Body Daily Yoga Practice", "url": "https://www.youtube.com/watch?v=Cj_ZmFzxm1k"},
                {"title": "Yoga With Adriene - YouTube Channel", "url": "https://www.youtube.com/c/yogawithadriene"}
            ]
        else:
            video_recommendations = [
                {"title": "45-Min Mixed Cardio Workout (No Equipment Sweat Sesh!)", "url": "https://www.youtube.com/watch?v=Yf7dqygDtZE"},
                {"title": "30 Minute Mixed Format Workout | 1.17.25", "url": "https://www.youtube.com/watch?v=k-S3s_U0dDw"},
                {"title": "30 MIN CARDIO AEROBICS WORKOUT - Move To The Beat", "url": "https://www.youtube.com/watch?v=vI5MzT-wIjs"}
            ]
    else:
        video_recommendations = [
           {"title": "PLUS SIZE Full Body Workout / Obese Beginner Workout", "url": "https://www.youtube.com/watch?v=8IwNI8r-jo0"},
           {"title": "Plus Size Beginner Workout / Low Impact / All Standing / 15 Mins", "url": "https://www.youtube.com/watch?v=Urv5kB3oYms"},
           {"title": "BEGINNER WORKOUT (WHAT I DID WHILE OBESE)", "url": "https://m.youtube.com/watch?v=gNoSo4SQN2o"},
           {"title": "PLUS SIZE/BEGINNER AT HOME WALKING WORKOUT (Low Impact)", "url": "https://www.youtube.com/watch?v=xxLLOW7-57w"},
           {"title": "Morbidly Obese CHAIR/STANDING Workout / Mobility Issues", "url": "https://www.youtube.com/watch?v=JSKTtnVcDdU"}
        ]

    return render_template("workouts.html", bmi=bmi, preference=preference, videos=video_recommendations)

@app.route('/diet')
def diet():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))

    user = User.query.get(user_id)
    if not user or not user.bmi or not user.diet_preference:
        return redirect(url_for('bmicalculation'))

    # Simple example logic for meal generation
    if user.diet_preference == "high protein":
        meals = {
            'Breakfast': ['Scrambled eggs', 'Greek yogurt'],
            'Lunch': ['Grilled chicken breast', 'Quinoa salad'],
            'Dinner': ['Steak with broccoli', 'Cottage cheese'],
            'Snack': ['Protein bar', 'Boiled eggs']
        }
    elif user.diet_preference == "low carbs":
        meals = {
            'Breakfast': ['Avocado with eggs', 'Herbal tea'],
            'Lunch': ['Zucchini noodles with pesto', 'Tofu stir-fry'],
            'Dinner': ['Grilled fish', 'Spinach salad'],
            'Snack': ['Nuts', 'Cucumber slices']
        }
    elif user.diet_preference == "vegetarian":
        meals = {
            'Breakfast': ['Oatmeal with fruits', 'Smoothie'],
            'Lunch': ['Chickpea curry', 'Brown rice'],
            'Dinner': ['Paneer tikka', 'Vegetable soup'],
            'Snack': ['Fruit salad', 'Roasted peanuts']
        }
    else:  # mixed
        meals = {
            'Breakfast': ['Boiled eggs', 'Toast with peanut butter'],
            'Lunch': ['Chicken wrap', 'Fruit'],
            'Dinner': ['Rice and lentils', 'Grilled veggies'],
            'Snack': ['Yogurt', 'Banana']
        }

    return render_template('diet.html', meals=meals)

@app.route('/progress')
def progress():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('signin'))

    user = User.query.get(user_id)
    if not user or not user.bmi:
        return redirect(url_for('bmicalculation'))

    return render_template('progress.html', bmi=user.bmi)



# ------------ Password Reset Routes ------------

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.email, salt='password-reset-salt')
            reset_url = f"http://192.168.0.106:5000/reset_password/{token}"
            html = f"""
            <p>Hello {user.name},</p>
            <p>To reset your password, click the link below:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>If you did not request this, ignore this email.</p>
            """
            send_email(user.email, "Password Reset Request", html)
            flash("A password reset link has been sent to your email.", "info")
            return redirect(url_for('signin'))
        else:
            flash("Email address not found.", "danger")
    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash("The password reset link has expired.", "danger")
        return redirect(url_for('forgot_password'))
    except BadSignature:
        flash("Invalid password reset token.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not password or not confirm_password:
            flash("Please fill out both password fields.", "warning")
        elif password != confirm_password:
            flash("Passwords do not match.", "warning")
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                user.password = generate_password_hash(password)
                db.session.commit()
                flash("Your password has been updated! You can now log in.", "success")
                return redirect(url_for('signin'))
            else:
                flash("User not found.", "danger")
                return redirect(url_for('forgot_password'))

    return render_template('reset_password.html')

# --------------------------- MAIN ---------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

