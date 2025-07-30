from app import app, User

with app.app_context():
    users = User.query.all()
    for user in users:
        print(user.email, user.admin)
