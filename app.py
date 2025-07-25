from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
from datetime import datetime

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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

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
    # Video recommendations based on BMI and preferences
    video_recommendations = []


    # Example video recommendations for different BMI categories and preferences
    if bmi < 18.5:  # Underweight
        video_recommendations = [
           {"title": "Do This Exercise EVERY DAY for Gains!", "url": "https://www.youtube.com/watch?v=u6PNjgn1ocM"},
            {"title": "Workout Program For Skinny Guys Trying To Get Bigger", "url": "https://www.youtube.com/watch?v=Qi0p-6XcTX0"},
            {"title": "5 MUST DO Exercises For Skinny Guys (NO EQUIPMENT)", "url": "https://www.youtube.com/watch?v=Y9hiyIo963A"},
            {"title": "5-minute Workout For SKINNY GUYS GAIN MUSCLE At Home", "url": "https://www.youtube.com/watch?v=IysRUAjVCpg"},
            {"title": "INTENSE Weight Gain Workout - OMG!", "url": "https://www.youtube.com/watch?v=W7mN-i0J7M0"}
        ]
    elif 18.5 <= bmi < 25:  # Normal BMI
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
        {
            "title": "17 Min Strength Training Workout for Beginners",
            "url": "https://www.youtube.com/watch?v=WIHy-ZnSndA"
        },
        {
            "title": "30-minute NO REPEAT Strength Training for Beginners",
            "url": "https://www.youtube.com/watch?v=IMXX7A8vQGg"
        },
        {
            "title": "Weight Training for Beginners & Seniors // 20 Minute Workout",
            "url": "https://www.youtube.com/watch?v=Qbv2edgrgvI"
        },
        {
            "title": "20 Minute Full Body Strength Workout (No Equipment/No Repeat)",
            "url": "https://www.youtube.com/watch?v=Q2cMMnUuKYQ"
        },
        {
            "title": "Strength Training for Beginners | Joe Wicks Workouts",
            "url": "https://www.youtube.com/watch?v=xO3NJ7A7w5o"
        }
            ]
        elif preference == "yoga":
            video_recommendations = [
                {"title": "10-Minute Yoga For Beginners | Start Yoga Here...", "url": "https://www.youtube.com/watch?v=j7rKKpwdXNE"},
                {"title": "20 Min Full Body Daily Yoga Practice", "url": "https://www.youtube.com/watch?v=Cj_ZmFzxm1k"},
                {"title": "Yoga With Adriene - YouTube Channel", "url": "https://www.youtube.com/c/yogawithadriene"}
            ]
        else:  # mixed
            video_recommendations = [
    {"title": "45-Min Mixed Cardio Workout (No Equipment Sweat Sesh!)", "url": "https://www.youtube.com/watch?v=Yf7dqygDtZE"},
    {"title": "30 Minute Mixed Format Workout | 1.17.25", "url": "https://www.youtube.com/watch?v=k-S3s_U0dDw"},
    {"title": "30 MIN CARDIO AEROBICS WORKOUT - Move To The Beat", "url": "https://www.youtube.com/watch?v=vI5MzT-wIjs"}
]

    else:  # BMI ≥ 25 (Obese)
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

    bmi = user.bmi
    raw_pref = user.diet_preference.lower().strip()

    if "protein" in raw_pref:
        preference = "high protein"
    elif "carb" in raw_pref:
        preference = "low carbs"
    elif "vegetarian" in raw_pref:
        preference = "vegetarian"
    else:
        preference = "mixed"

    category = "underweight" if bmi < 18.5 else "normal" if bmi < 25 else "overweight"

    diet_plans = {
        "high protein": {
            "underweight": {
                "Breakfast": ["Anda Tarkari with Roti", "Chana Chaat"],
                "Lunch": ["Masoor Dal", "Paneer Bhujuri", "Rice"],
                "Dinner": ["Grilled Chicken", "Spinach Tarkari"],
                "Snack": ["Boiled Eggs", "Greek Yogurt"]
            },
            "normal": {
                "Breakfast": ["Boiled Eggs", "Dudh Chiura"],
                "Lunch": ["Soybean Curry", "Brown Rice"],
                "Dinner": ["Chicken Soup", "Salad"],
                "Snack": ["Peanut Chikki", "Protein Bar"]
            },
            "overweight": {
                "Breakfast": ["Tofu Bhujuri", "Green Smoothie"],
                "Lunch": ["Boiled Eggs", "Saag Tarkari"],
                "Dinner": ["Grilled Fish", "Boiled Cauliflower"],
                "Snack": ["Roasted Chana", "Cucumber Sticks"]
            }
        },
        "low carbs": {
            "underweight": {
                "Breakfast": ["Egg Curry", "Chia Pudding"],
                "Lunch": ["Chicken Stew", "Stir-fried Beans"],
                "Dinner": ["Paneer Salad"],
                "Snack": ["Nuts Mix", "Egg Whites"]
            },
            "normal": {
                "Breakfast": ["Keto Roti", "Avocado Smoothie"],
                "Lunch": ["Fish Tarkari", "Vegetable Mix"],
                "Dinner": ["Mushroom Soup"],
                "Snack": ["Cheese Cubes", "Peanuts"]
            },
            "overweight": {
                "Breakfast": ["Omelet", "Cucumber Salad"],
                "Lunch": ["Keto Chicken Curry", "Lettuce Wraps"],
                "Dinner": ["Pumpkin Soup"],
                "Snack": ["Carrot Sticks", "Almonds"]
            }
        },
        "vegetarian": {
            "underweight": {
                "Breakfast": ["Sukha Aloo with Roti", "Milk Tea"],
                "Lunch": ["Rajma Tarkari", "Jeera Rice"],
                "Dinner": ["Paneer Butter Masala", "Chapati"],
                "Snack": ["Banana", "Chikki"]
            },
            "normal": {
                "Breakfast": ["Chiura with Dahi", "Banana Smoothie"],
                "Lunch": ["Aloo Gobi", "Dal Tadka"],
                "Dinner": ["Veg Soup", "Mixed Salad"],
                "Snack": ["Fruit Salad", "Cornflakes"]
            },
            "overweight": {
                "Breakfast": ["Oats with Fruit", "Green Tea"],
                "Lunch": ["Taro Root", "Spinach Curry"],
                "Dinner": ["Vegetable Stew"],
                "Snack": ["Roasted Makhana", "Cucumber Slices"]
            }
        },
        "mixed": {
            "underweight": {
                "Breakfast": ["Chana Chaat", "Oats with Milk"],
                "Lunch": ["Dal Bhat", "Vegetable Curry"],
                "Dinner": ["Grilled Chicken", "Saag Tarkari"],
                "Snack": ["Boiled Egg", "Banana"]
            },
            "normal": {
                "Breakfast": ["Milk and Chia Pudding", "Sandwich"],
                "Lunch": ["Grilled Fish", "Vegetable Curry"],
                "Dinner": ["Dal Bhat", "Green Salad"],
                "Snack": ["Fruit Mix", "Egg Toast"]
            },
            "overweight": {
                "Breakfast": ["Smoothie", "Boiled Eggs"],
                "Lunch": ["Paneer Tikka", "Veg Soup"],
                "Dinner": ["Salad", "Boiled Eggs"],
                "Snack": ["Green Tea", "Roasted Chana"]
            }
        }
    }

    meals = diet_plans.get(preference, {}).get(category, {})
    return render_template("diet.html", bmi=bmi, preference=preference, meals=meals)

@app.route('/progress')
def progress():
    # Assuming the user is logged in and you have their user_id
    user_id = 1  # Replace with actual user ID (for logged-in users, get this from session or a user object)
    
    # Get user data (BMI)
    user = User.query.get(user_id)
    bmi = user.bmi  # Assuming BMI is stored in the User model
    
    # Get workout progress (e.g., total workouts completed)
    workout_count = Workout.query.filter_by(user_id=user_id).count()
    
    # Get diet progress (e.g., how many meals were logged/adhered to)
    diet_adherence = DietLog.query.filter_by(user_id=user_id).count()  # For simplicity, we're just counting meals logged
    
    # Get recent updates (optional)
    recent_updates = []  # You can fetch recent updates from a log table or track progress entries here.
    
    # Example of recent updates
    recent_updates = [
        "Completed a 30-minute workout.",
        "Followed the high-protein diet for 3 days in a row.",
        "Lost 1 kg since last week."
    ]

    # Render the progress page with the data
    return render_template('progress.html', 
                           bmi=bmi, 
                           workout_count=workout_count, 
                           diet_adherence=diet_adherence,
                           recent_updates=recent_updates)

@app.route('/update_progress', methods=['POST'])
def update_progress():
    sets = request.form.get('sets')
    reps = request.form.get('reps')
    intensity = request.form.get('intensity')
    duration = request.form.get('duration')
    calories = request.form.get('calories')
    
    # Code to handle saving the progress to the database or processing it
    # Redirect or render a success page afterward
    return redirect(url_for('progress'))  # Or render a template


# --------------------------- MAIN ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
